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
1. Open the app.
2. Enter your pool URL, wallet address, worker name, and mining algorithm.
3. Select the CPU miner executable on your machine.
4. Click "Start mining".
5. Click "Stop" to end the session.

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
