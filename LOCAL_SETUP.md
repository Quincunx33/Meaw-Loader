# Meaw Loader: Local Python setup

This version runs the web interface and Python downloader on the same desktop computer. It does not use a hosted backend URL. The local server binds to `127.0.0.1` so it is not exposed to other devices on your network.

## Requirements

- Windows, macOS, or Linux desktop/laptop
- Python 3.10 or newer
- Internet access for the first launch so dependencies can be installed

## Windows

1. Download and extract the repository ZIP from GitHub.
2. Install Python 3.10 or newer if it is not already installed. On Windows, enable the Python launcher (`py`) during installation.
3. Double-click `start_local.bat` in the extracted project folder. The first run creates a virtual environment and installs the packages from `requirements.txt`.
4. Open `http://127.0.0.1:8080` in your browser. Keep the launcher window open while using Meaw Loader.
5. Press `Ctrl+C` in the launcher window to stop the server.

## macOS or Linux

1. Download and extract the repository ZIP from GitHub.
2. Install Python 3.10 or newer. On some Linux distributions, the `python3-venv` package is also required.
3. Open a terminal in the project folder and run:

   ```bash
   chmod +x start_local.sh
   ./start_local.sh
   ```

4. Open `http://127.0.0.1:8080` in your browser. Keep the terminal open while using Meaw Loader; press `Ctrl+C` to stop it.

The first run creates `.venv/` and installs the Python dependencies. Downloads are saved under `downloads/`.

## Optional YouTube cookies

Some YouTube requests may require the user's own fresh browser cookies. If needed, export them in Netscape cookies.txt format and save the file beside `server.py` as `secret_cookies.txt`. This file is ignored by Git and is not served by the local web server. Do not upload or share it; cookies grant account access. If a video works without cookies but fails with them, remove the local cookie file and export a fresh copy only if required.

## Important

This local Python edition is for desktop/laptop browsers. iPhone and Android browsers cannot run this Python server directly. Do not expose the server to the public internet or change its default loopback host unless you understand the security implications.
