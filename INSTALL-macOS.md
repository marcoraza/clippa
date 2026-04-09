# Install Clippa on macOS

This guide is for the prebuilt file:

- `Clippa-mac-unsigned.zip`

## First install

1. Download `Clippa-mac-unsigned.zip`
2. Double-click the zip to extract it
3. Drag `Clippa.app` to `Applications`
4. Open `Applications`
5. Right-click `Clippa.app`
6. Click `Open`
7. Confirm the warning dialog

That first manual open is expected because the public build is not notarized by Apple.

## If macOS blocks the app

1. Try to open `Clippa.app`
2. Open `System Settings`
3. Go to `Privacy & Security`
4. Scroll down to the security section
5. Click `Open Anyway`
6. Try opening `Clippa.app` again

## What to expect

- Clippa opens as a normal macOS app
- downloaded files are saved through the native save dialog
- temporary files are stored in `~/Downloads/Clippa`

## If you want a fully trusted installer later

This repo already includes the scripts for Apple code signing and notarization, but that requires an Apple Developer account.
