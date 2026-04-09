# Clippa

Clippa is a lightweight media downloader for YouTube, TikTok, Instagram, X, Reddit, Vimeo, SoundCloud, and many other sources supported by `yt-dlp`.

It runs in the browser or as a native macOS app.

![Python](https://img.shields.io/badge/python-3.8+-blue)
![License](https://img.shields.io/badge/license-MIT-green)

![Clippa MP3 Mode](assets/preview-mp3.png)

## Download

If you just want the macOS app:

1. Open the latest release page:
   `https://github.com/marcoraza/clippa/releases/latest`
2. Download `Clippa-mac-unsigned.zip`
3. Follow the install guide in [INSTALL-macOS.md](INSTALL-macOS.md)

Important:

- the current public build is unsigned
- macOS may block the first launch
- the workaround is simple and documented below

## macOS Install, Step by Step

### Option 1, Download a prebuilt app

1. Download `Clippa-mac-unsigned.zip` from the latest release
2. Extract the zip
3. Drag `Clippa.app` into `Applications`
4. Right-click `Clippa.app`
5. Click `Open`
6. Confirm the macOS warning

After the first manual open, macOS usually stops asking again for that app.

### If macOS still blocks it

1. Try opening the app once
2. Open `System Settings`
3. Go to `Privacy & Security`
4. Scroll to the security section
5. Click `Open Anyway`
6. Open `Clippa.app` again

More detail is in [INSTALL-macOS.md](INSTALL-macOS.md).

## Run From Source

### Requirements

- Python 3.8+
- `ffmpeg`
- `yt-dlp`

macOS with Homebrew:

```bash
brew install ffmpeg yt-dlp
```

Linux:

```bash
sudo apt install ffmpeg
pip install yt-dlp
```

### Start the web app

```bash
git clone https://github.com/marcoraza/clippa.git
cd clippa
./reclip.sh
```

Open:

- `http://localhost:8899`

To expose it on your local network:

```bash
HOST=0.0.0.0 PORT=8899 ./reclip.sh
```

## Build the macOS App

This project can package itself as a `.app`.

```bash
git clone https://github.com/marcoraza/clippa.git
cd clippa
./reclip.sh
venv/bin/python -m pip install -r requirements-desktop.txt
./scripts/build-macos-app.sh
open dist/Clippa.app
```

What the build does:

- packages the Flask backend inside the app
- bundles `ffmpeg` and `ffprobe`
- creates `dist/Clippa.app`

## Create a Shareable macOS Zip

If you want a ready-to-send build without Apple Developer signing:

```bash
./scripts/release-macos-unsigned.sh
```

This produces:

- `dist/Clippa.app`
- `dist/Clippa-mac-unsigned.zip`

Note:

- this build is usable
- it is not notarized by Apple
- first launch will require manual confirmation on another Mac

## Persistent Background Mode on macOS

If you want Clippa available after closing Terminal:

```bash
./reclip.sh
./scripts/install-macos-service.sh
```

Useful commands:

```bash
launchctl print gui/$(id -u)/com.marko.clippa
tail -f logs/clippa.out.log
tail -f logs/clippa.err.log
./scripts/uninstall-macos-service.sh
```

## Supported Sources

Clippa works with anything supported by `yt-dlp`, including:

- YouTube
- TikTok
- Instagram
- X / Twitter
- Reddit
- Vimeo
- Twitch
- SoundCloud
- Dailymotion
- LinkedIn
- many more

## Usage

1. Paste one or more links
2. Choose `MP4` or `MP3`
3. Click `Fetch`
4. Pick quality if available
5. Download the result

## Signed Releases

If you have an Apple Developer account, this repo also includes signing and notarization scripts:

- `scripts/store-notary-credentials.sh`
- `scripts/release-macos-app.sh`

These are optional. The public release currently targets the unsigned flow for simple installation.

## License

MIT. See [LICENSE](LICENSE).

## Disclaimer

Use responsibly. Respect platform terms and content copyright.
