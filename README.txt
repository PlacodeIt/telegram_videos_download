 Telegram Video Downloader

This project is a Python script for downloading videos from a specified Telegram channel using the Telethon library. The script fetches messages from the channel, checks if the video already exists locally, and downloads new videos while handling expired file references.

 Features

- Fetch messages from a specified Telegram channel.
- Download videos from the channel, avoiding duplicates.
- Handle expired file references by refreshing and retrying downloads.
- Log detailed information about downloaded and skipped videos.
- Print progress indicators to the terminal.

 Requirements

- Python 3.6+
- Telethon library

update 6/6/24
 Features

- Fetch Messages from Channel
- Download Videos
- Avoid Duplicates: Check if a video already exists locally based on file size and text.
- Handle Expired File References: Refresh and retry downloads if the file reference is expired.
- Logging and Debugging: Print detailed logs and debugging information.
- Progress Indicators: Print progress indicators to the terminal every 10 seconds.
- Graceful Shutdown: Handle shutdowns with user confirmation.
- Retry Mechanism: Retry the download process in case of temporary errors.
- Configuration File: Use a configuration file to store API credentials, download path, and target channel.

 Improvements

1. Optimized File Existence Check: 
    - Implemented using a `defaultdict` for O(1) time complexity when checking if a video with the same size already exists.

2. Retry Mechanism:
    - Added a retry mechanism to handle temporary errors, such as `FloodWaitError`, ensuring robust error handling.

3. Chill Shutdown:
    - Implemented a chill shutdown that asks the user for confirmation before exiting and cancels all ongoing tasks properly.

4. Detailed Logging:
    - Enhanced the logging to provide detailed information about each step, including fetching messages, starting downloads, and handling errors.

5. Print Statements:
    - Updated and standardized print statements, providing consistent and clear output.

 Configuration

Create a `theconfig.ini` file in the same directory as the script with the following content:

---------- To be continued ----(hopefully)------ 