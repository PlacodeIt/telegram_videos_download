from telethon import TelegramClient, errors
from telethon.tl.types import InputMessagesFilterVideo
import os
import configparser
import re
import asyncio
import telethon.errors.rpcerrorlist  # Ensure this is imported to handle specific errors
from collections import defaultdict
import signal

# Define the path to the config file in the current working directory
current_dir = os.getcwd()
config_path = os.path.join(current_dir, 'theconfig.ini')

# Read the configuration file
config = configparser.ConfigParser()

# Debugging: Print raw content of config file
with open(config_path, 'r') as file:
    config_content = file.read()
    print(f"Raw content of config.ini:\n{config_content}")

config.read(config_path)
print("Configuration file read successfully.")
print(f"Sections found in config file: {config.sections()}")

# Check if the 'telegram' section exists
if 'telegram' not in config:
    raise KeyError("Missing 'telegram' section in config.ini")

# Extract the API ID and hash
try:
    api_id = config['telegram']['api_id']
    api_hash = config['telegram']['api_hash']
    print(f"API ID: {api_id}, API Hash: {api_hash}")  # Debugging output
except KeyError as e:
    raise KeyError(f"Missing key in config.ini: {e}")

# Define the download folder and target channel
download_folder = os.path.join(current_dir, 'teledown_folder')

if not os.path.exists(download_folder):
    os.makedirs(download_folder)

target_channel = config['telegram'].get('target_channel', 'YOUR_CHANNEL_NAME')

# Initialize the Telegram client with the new session name 'telegram_video_downloader'
client = TelegramClient('telegram_video_downloader', api_id, api_hash)

def sanitize_filename(text):
    # Remove invalid characters from filenames
    sanitized = re.sub(r'[\\/*?:"<>|]', "", text)
    # Remove newlines
    sanitized = sanitized.replace('\n', ' ').replace('\r', '')
    # Limit length to 20 characters
    return sanitized[:20]

def get_existing_files():
    # Get a dictionary of existing files with their sizes and names
    existing_files = defaultdict(list)
    for filename in os.listdir(download_folder):
        if filename.endswith('.mp4'):
            filepath = os.path.join(download_folder, filename)
            size = os.path.getsize(filepath)
            existing_files[size].append(filename)
    return dict(existing_files)

def existing_file_matches_text(existing_files, video_size, sanitized_text):
    if video_size in existing_files:
        similar_files = existing_files[video_size]
        for existing_file in similar_files:
            if sanitized_text in existing_file:
                return True
    return False

async def print_smiley():
    counter = 10
    while True:
        await asyncio.sleep(10)
        print(f":){counter // 60}:{counter % 60:02d}")
        counter += 10

async def main():
    # Start the background task to print ":)" every 10 seconds
    smiley_task = asyncio.create_task(print_smiley())

    downloaded_videos = 0
    skipped_videos = 0
    existing_files = get_existing_files()
    processed_messages = set()

    try:
        # Fetch messages from the target channel, starting with the most recent
        print(f'Fetching messages from channel: {target_channel}')
        total_messages = 0

        async for message in client.iter_messages(
                target_channel,
                filter=InputMessagesFilterVideo,
                reverse=True):  # Start with the most recent messages
            
            total_messages += 1
            print(f'Fetched {total_messages} messages so far')

            # Print message details for debugging
            print(f'Message ID: {message.id}, Date: {message.date}, Video: {message.video is not None}, Message: {message.message}')

            if message.id in processed_messages:
                print(f'Message ID {message.id} already processed, skipping.')
                continue

            if message.video:
                # Get the text message and sanitize it for use as a filename
                text = message.message or 'video'
                sanitized_text = sanitize_filename(text)
                
                # Define file paths
                video_file_path = os.path.join(download_folder, f'{sanitized_text}.mp4')
                
                # Check if a file with the same size and text already exists
                video_size = message.video.size
                if existing_file_matches_text(existing_files, video_size, sanitized_text):
                    print(f'Skipping download: File with the same size and text found.\nDetails: Message ID: {message.id}, Date: {message.date}, Text: {text}')
                    skipped_videos += 1
                    processed_messages.add(message.id)
                    continue

                # Log before downloading
                print(f'Starting download for: {sanitized_text}')
                
                try:
                    # Download the video
                    await client.download_media(message, video_file_path)
                    
                    # Log after successfully downloading
                    print(f'Downloaded video: {video_file_path}')
                    downloaded_videos += 1
                    processed_messages.add(message.id)
                    
                    # Add the new file to existing_files
                    existing_files[video_size].append(os.path.basename(video_file_path))
                except telethon.errors.rpcerrorlist.FileReferenceExpiredError:
                    print(f'File reference expired for message ID: {message.id}, attempting to refresh...')
                    # Try to refresh the message to get a new file reference
                    fresh_message = await client.get_messages(target_channel, ids=message.id)
                    try:
                        await client.download_media(fresh_message, video_file_path)
                        print(f'Downloaded video after refresh: {video_file_path}')
                        downloaded_videos += 1
                        processed_messages.add(fresh_message.id)
                        existing_files[video_size].append(os.path.basename(video_file_path))
                    except Exception as e:
                        print(f'Error downloading refreshed video: {e}')
                except Exception as e:
                    print(f'Error downloading video: {e}')

    except asyncio.CancelledError:
        print("Download interrupted by user.")
    finally:
        # Cancel the smiley task when downloads are complete or if an error occurs
        smiley_task.cancel()
        try:
            await smiley_task
        except asyncio.CancelledError:
            pass
        print(f'Operation end: Total videos downloaded: {downloaded_videos}. Total videos skipped: {skipped_videos}.\nThe script has finished running. Stay sharp :)')
        await client.disconnect()

def shutdown(signal, frame):
    response = input("Are you sure you want to exit? (y/n): ")
    if response.lower() == 'y':
        print("Exiting...")
        for task in asyncio.all_tasks():
            task.cancel()
        asyncio.get_event_loop().stop()
    else:
        print("Continuing...")

async def run_with_retries(client, max_retries=3):
    for attempt in range(max_retries):
        try:
            async with client:
                await main()
            break
        except errors.FloodWaitError as e:
            print(f"Flood wait error: Waiting for {e.seconds} seconds before retrying...")
            await asyncio.sleep(e.seconds)
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt + 1 == max_retries:
                print("Max retries reached. Exiting.")
                break
            print("Retrying...")

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Register the signal handler for graceful shutdown
    signal.signal(signal.SIGINT, shutdown)

    try:
        loop.run_until_complete(run_with_retries(client))
    except (KeyboardInterrupt, SystemExit):
        shutdown(signal.SIGINT, None)
        loop.run_until_complete(asyncio.sleep(0.1))  # Allow all tasks to cancel
    finally:
        loop.close()
