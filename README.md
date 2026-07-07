# Mayan Miner

Mayan Miner is an open-source, Windows-first CPU mining launcher with a polished desktop dashboard. It includes built-in XMRig installer support so users do not need to install a separate miner manually.

## Features
- Clean, tabbed desktop UI: a **Dashboard** (live status, hashrate graph, miner output) and a
  **Settings** tab (pool/wallet/miner/algorithm, appearance, and storage), instead of one crowded screen
- Real-time hashrate graph plus at-a-glance stat cards (status, hashrate, accepted/rejected shares, uptime)
  parsed live from the running miner's own output — works with xmrig, SRBMiner, or any custom miner
- Built-in XMRig installation and automatic miner updates
- Real miner launch support with custom pools, wallets, worker names, algorithms, and extra arguments
- Fully custom algorithm names (type any algorithm your miner supports, not just the presets)
- "Custom" miner kind can drive any other miner executable, including one with its own CLI syntax,
  via an optional command template (`{executable} {pool} {wallet} {worker} {password} {algorithm}
  {threads} {extra_args}` placeholders)
- Optional splash screen on startup (toggle in Settings)
- Minimize/close to the system tray and keep mining in the background; tray menu can show the window,
  start/stop mining, or fully exit (toggle in Settings — off by default)
- Optional "start with Windows and begin mining automatically" (Settings; Windows-only)
- Dark/light theme option (applies on next launch)
- Encrypted local configuration storage, all kept in its own per-user AppData folder like other
  Windows apps, with an "Open data folder" shortcut in Settings
- Installs and uninstalls like a normal Windows app (Start Menu/desktop shortcut, entry in
  Windows Settings > Apps); uninstalling asks whether to also delete your saved settings
- Built-in developer wallet and 0.2% fee note
- Windows executable packaging with PyInstaller, with the app logo bundled as both the in-app icon
  and the .exe file icon, plus a SHA256 checksum published alongside each build for integrity checks

## Default developer wallet
- XMR: 4AmMooquAZ3JUAjuJTEDNZSxw9gmR5VuaMzKrmxjfHXuh1TGYdu3QxuEXLPhhSTZFmcA5DYfyGn3Z4Nfa27ionur4wwha1o
- Developer fee: 0.2%

## Run locally
```powershell
python -m pip install -r requirements.txt
python main.py
```

## Build Windows executable
```powershell
.\build_exe.ps1
```

The executable will be written to the `output` folder as `MayanMiner.exe`.

## Build the Windows installer
After building the executable, use Inno Setup and the installer script:
```powershell
cd installer
.\build_installer.ps1
```

The installer output will also be saved in the `output` folder.

## GitHub release automation
When a GitHub release is created, the release workflow will automatically:
- build `output\MayanMiner.exe`
- build `output\MayanMinerSetup.exe`
- publish both files as release assets

## Installation and uninstall
1. Run the generated installer from `output\MayanMinerSetup.exe`.
2. Follow the standard Windows installation wizard and choose the install location.
3. The installer installs into `Program Files\Mayan Miner` by default and creates a Start menu shortcut
   (and, optionally, a desktop shortcut).
4. All app data (encrypted settings, encryption key, downloaded XMRig binary) lives in its own folder
   at `%APPDATA%\MayanMiner` — separate from the program files, like other Windows apps.
5. Uninstall using Windows Settings > Apps > Mayan Miner, or the uninstall shortcut in the Start menu.
   You'll be asked whether to also delete the `%APPDATA%\MayanMiner` folder, or keep your settings for
   next time.

## Repository layout
- `main.py` — app launcher entry point
- `mayan_miner/` — application package
  - `app.py` — the Tk UI (dashboard + settings tabs)
  - `widgets.py` — the dependency-free live chart and stat-card widgets
  - `stats.py` — parses live miner stdout into hashrate/shares history
  - `splash.py` — the optional startup splash screen
  - `tray.py` — system tray integration (optional `pystray` dependency)
  - `autostart.py` — Windows "start on login" registry helper
  - `config.py`, `miner.py`, `updater.py` — settings, launch-command building, XMRig updater
- `installer/` — installer script and build workflow
- `output/` — packaged build artifacts (ignored by git)
- `tests/` — unit tests

## Repository
This project is intended for public GitHub hosting as MayanMiner.
