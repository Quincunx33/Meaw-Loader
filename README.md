# 🐱 Meaw Loader

> A blazing-fast, open-source media downloader with an adorable cat-themed aesthetic. Paste links from YouTube, TikTok, Instagram, Twitter/X, Reddit, and 1000+ sites to download high-quality **MP4** video or **MP3** audio.

[![GitHub Repository](https://img.shields.io/badge/GitHub-Repository-181717?logo=github)](https://github.com/Quincunx33/Meaw-Loader.git)
![License](https://img.shields.io/badge/license-MIT-orange)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![yt--dlp](https://img.shields.io/badge/engine-yt--dlp-red)

**Linked**: [https://grabar.pages.dev](https://grabar.pages.dev)

---

## ✨ Features

- **🐾 1000+ Supported Sites**: Powered by `yt-dlp` — download from YouTube, TikTok, Instagram, Twitter/X, Reddit, Facebook, Vimeo, Twitch, SoundCloud, Loom, Pinterest, and more.
- **📥 Batch URL Text File Import**: Import any `.txt` file containing lists of URLs with one click via the **Import TXT** button, drag-and-drop directly onto the URL box, or press `Alt + I`. Links are parsed, deduplicated, and queued automatically.
- **🎬 Quality & Resolution Picker**: Automatically lists all available resolutions (`1080p`, `720p`, `480p`, `360p`) with real-time **estimated file sizes** so you know exactly what you're downloading.
- **📊 Live Progress Bar & Queue Manager**: Real-time progress bar beneath active downloads displaying percentage completion, speed, and status, plus live queue status badge and one-click "Download All".
- **🎵 MP4 & MP3 Support**: Switch between full HD video or extracted high-bitrate MP3 audio with one click.
- **⌨️ Global Keyboard Shortcuts**:
  - `Ctrl + Enter` (or `⌘ + Enter` on macOS): Trigger the "Grab" button instantly from anywhere.
  - `Alt + I`: Open text file import dialog to load URL lists into queue.
  - `Esc`: Clear the current URL input field with instant visual feedback.
  - `/`: Quick focus on the URL input.
  - `Alt + 1` / `Alt + 2`: Quickly switch format between MP4 (Video) and MP3 (Audio).
  - `?`: Open the interactive keyboard shortcuts guide.
- **📜 Smart Download History**:
  - Automatically saves your last 10 completed downloads to `localStorage`.
  - **Instant Re-download**: Re-download any item directly without needing to fetch info again.
  - **Custom Sorting**: Sort your history by **Date (Newest/Oldest)**, **Title (A–Z / Z–A)**, or **File Size (Largest/Smallest)**.
- **🖼️ Universal Thumbnail Loader**: Zero referrer leakage (`no-referrer`) ensures thumbnails from YouTube, TikTok, and Instagram load smoothly with automatic fallbacks.
- **🌙 Light & Dark Mode**: Persistent theme switcher with custom CSS variables.
- **📦 Zero Heavy Frameworks**: Lightweight single-file Python server (`server.py`) and pure responsive frontend.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- `ffmpeg` (for media merging and audio extraction)

### Installation & Run

1. Clone the repository:
   ```bash
   git clone https://github.com/Quincunx33/Meaw-Loader.git
   cd Meaw-Loader
   ```

2. Start the server:
   ```bash
   python3 server.py
   ```
   *(Or with npm: `npm run dev`)*

3. Open **http://localhost:8080** in your browser.

---

## 📖 How to Use

1. **Paste URL(s)**: Paste one or multiple video links separated by spaces, commas, or new lines.
2. **Choose Format**: Toggle between **MP4** (video) and **MP3** (audio).
3. **Click "Grab"**: Loads metadata, thumbnails, and available quality options.
4. **Select Quality**: Pick your preferred resolution (`1080p`, `720p`, etc.) or keep the default best quality.
5. **Download**: Hit **Download** to start downloading with the live progress bar.
6. **History & Re-download**: Access previous downloads at the bottom of the page anytime.

---

## 🛠️ Tech Stack

- **Backend**: Python 3 (`Flask`)
- **Engine**: [yt-dlp](https://github.com/yt-dlp/yt-dlp) + [ffmpeg](https://ffmpeg.org/)
- **Frontend**: Vanilla HTML5, CSS3, ES6 JavaScript
- **Typography**: Instrument Serif & DM Mono

---

## ⚖️ License

Distributed under the [MIT License](LICENSE). Copyright (c) 2026 Meaw Loader.

---

## ⚠️ Disclaimer

This tool is created for educational and personal archival purposes. Please respect the copyright and Terms of Service of content providers.
