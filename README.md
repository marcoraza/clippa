# Clippa

Clippa is a self-hosted video and audio downloader with a clean web UI. Paste links from YouTube, TikTok, Instagram, Twitter/X, and 1000+ other sites and save them as MP4 or MP3.

![Python](https://img.shields.io/badge/python-3.8+-blue)
![License](https://img.shields.io/badge/license-MIT-green)

https://github.com/user-attachments/assets/419d3e50-c933-444b-8cab-a9724986ba05

![Clippa MP3 Mode](assets/preview-mp3.png)

## Features

- Download videos from 1000+ supported sites (via [yt-dlp](https://github.com/yt-dlp/yt-dlp))
- MP4 video or MP3 audio extraction
- Quality/resolution picker
- Bulk downloads — paste multiple URLs at once
- Automatic URL deduplication
- Clean, responsive UI — no frameworks, no build step
- Single Python file backend (~150 lines)

## Quick Start

```bash
brew install yt-dlp ffmpeg    # or apt install ffmpeg && pip install yt-dlp
git clone https://github.com/marcoraza/clippa.git
cd clippa
./reclip.sh
```

Open **http://localhost:8899**.

To listen on your whole local network instead of only `localhost`:

```bash
HOST=0.0.0.0 PORT=8899 ./reclip.sh
```

Or with Docker:

```bash
docker build -t clippa . && docker run -p 8899:8899 clippa
```

## Desktop App For macOS

You can now run Clippa as a native Mac window without opening a browser tab:

```bash
cd clippa
venv/bin/python -m pip install -r requirements-desktop.txt
venv/bin/python desktop.py
```

To build a `.app` bundle:

```bash
chmod +x scripts/build-macos-app.sh
./scripts/build-macos-app.sh
open dist/Clippa.app
```

Notes:

- The desktop build still uses the same Flask backend internally
- Finished downloads are saved through the native macOS save dialog
- When bundled, temporary download files live in `~/Downloads/Clippa`
- `ffmpeg` and `ffprobe` are copied into the app bundle during the build

## Signed Release For Other Macs

To distribute without Gatekeeper warnings on other machines, you need:

- an Apple Developer membership
- a `Developer ID Application` certificate installed in Keychain
- a saved `notarytool` keychain profile

Save notary credentials once:

```bash
export APPLE_NOTARY_PROFILE="clippa-notary"
export APPLE_ID="your-apple-id@example.com"
export APPLE_TEAM_ID="TEAMID1234"
export APPLE_APP_PASSWORD="xxxx-xxxx-xxxx-xxxx"
chmod +x scripts/store-notary-credentials.sh
./scripts/store-notary-credentials.sh
```

Build, sign, notarize, and produce a distributable zip:

```bash
export APPLE_SIGN_IDENTITY="Developer ID Application: Your Name (TEAMID1234)"
export APPLE_NOTARY_PROFILE="clippa-notary"
chmod +x scripts/release-macos-app.sh
./scripts/release-macos-app.sh
```

Final release artifact:

- `dist/Clippa.app`
- `dist/Clippa-mac.zip`

If `security find-identity -v -p codesigning` returns `0 valid identities found`, this Mac does not yet have the signing certificate needed for a fully trusted installer.

## Unsigned Release For Immediate Use

If you just want a working build now, without Apple Developer:

```bash
chmod +x scripts/release-macos-unsigned.sh
./scripts/release-macos-unsigned.sh
```

Artifacts:

- `dist/Clippa.app`
- `dist/Clippa-mac-unsigned.zip`

Install instructions for another Mac are in `INSTALL-macOS.md`.

## Usage

1. Paste one or more video URLs into the input box
2. Choose **MP4** (video) or **MP3** (audio)
3. Click **Fetch** to load video info and thumbnails
4. Select quality/resolution if available
5. Click **Download** on individual videos, or **Download All**

## Run Persistently On macOS

If you want Clippa to stay up after closing Terminal, this repo includes a `launchd` service definition for macOS.

1. Start it once manually and confirm dependencies are installed:

```bash
cd clippa
./reclip.sh
```

2. Install the LaunchAgent:

```bash
chmod +x scripts/install-macos-service.sh scripts/uninstall-macos-service.sh
./scripts/install-macos-service.sh
```

3. Access it from:

- `http://localhost:8899` on the same Mac
- `http://YOUR-LAN-IP:8899` from another device on the same network

Useful commands:

`launchctl print gui/$(id -u)/com.marko.clippa`

`tail -f logs/clippa.out.log`

`tail -f logs/clippa.err.log`

`./scripts/uninstall-macos-service.sh`

This exposes Clippa to your local network, not the public internet. If you want internet access, put it behind a reverse proxy or tunnel and add authentication.

## Supported Sites

Anything [yt-dlp supports](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md), including:

YouTube, TikTok, Instagram, Twitter/X, Reddit, Facebook, Vimeo, Twitch, Dailymotion, SoundCloud, Loom, Streamable, Pinterest, Tumblr, Threads, LinkedIn, and many more.

## Stack

- **Backend:** Python + Flask (~150 lines)
- **Frontend:** Vanilla HTML/CSS/JS (single file, no build step)
- **Download engine:** [yt-dlp](https://github.com/yt-dlp/yt-dlp) + [ffmpeg](https://ffmpeg.org/)
- **Dependencies:** 2 (Flask, yt-dlp)

## Disclaimer

This tool is intended for personal use only. Please respect copyright laws and the terms of service of the platforms you download from. The developers are not responsible for any misuse of this tool.

## License

[MIT](LICENSE)
