# Mayan Miner User Guide

## Quick start
1. Install Python 3.12 on Windows.
2. Open the project folder in PowerShell.
3. Run `.uild_exe.ps1` to create `output\MayanMiner.exe`.
4. Launch `output\MayanMiner.exe` and select a CPU miner executable.

## Building the app
- Run `.uild_exe.ps1` from the repository root.
- The build outputs are stored in the `output/` folder.

## Building the installer
1. Install Inno Setup 6.
2. Run `.
installer\build_installer.ps1` from PowerShell.
3. The installer will be created in `output\MayanMinerSetup.exe`.

## Installing Mayan Miner
- Run the installer `output\MayanMinerSetup.exe`.
- Choose the installation folder (default is `Program Files\Mayan Miner`).
- A Start menu shortcut will be created.

## Uninstalling Mayan Miner
- Open Windows Settings > Apps > Apps & features.
- Find `Mayan Miner` and choose Uninstall.
- Alternatively, use the uninstall shortcut created in the Start menu.

## Using Mayan Miner
1. Open the app (an optional splash screen appears briefly first — toggle this in Settings).
2. Go to the **Settings** tab: enter your pool URL, wallet address, worker name, and mining algorithm
   (type any custom algorithm name your miner supports), pick a miner kind, and point it at your CPU
   miner executable. Custom miner apps can use their own command syntax via the command template field.
3. Click "Save settings".
4. Go to the **Dashboard** tab and click "Start mining".
5. Watch the live hashrate graph and the status/hashrate/shares/uptime cards update in real time from
   the miner's own output. Click "Stop" to end the session.

## Uninstalling Mayan Miner
- Open Windows Settings > Apps > Apps & features.
- Find `Mayan Miner` and choose Uninstall.
- Alternatively, use the uninstall shortcut created in the Start menu.
- You'll be asked whether to also remove your saved settings (in `%APPDATA%\MayanMiner`), or keep them.

## Background mining, tray, and startup options
- In Settings > Appearance & behavior, "Keep running in the tray when minimized or closed" lets Mayan
  Miner keep mining in the background instead of quitting — right-click the tray icon to reopen it,
  start/stop mining, or exit for real.
- "Start Mayan Miner (and mining) when I log into Windows" registers the app to launch automatically
  at login (Windows only), starting minimized to the tray.
- All settings, the encryption key, and the downloaded miner binary live in `%APPDATA%\MayanMiner`
  (Settings tab has an "Open data folder" shortcut).

## Notes for new users
- The app is a launcher: it requires a real CPU miner executable such as XMRig.
- If you do not have a miner executable, download one from a trusted source and select it in the app.
- Settings are stored locally and encrypted in the user profile.

## Repository layout
- `main.py` — application entry point
- `mayan_miner/` — source code for the miner launcher
- `installer/` — installer scripts for Windows
- `output/` — build artifacts and generated packages
- `tests/` — unit tests
