# Mayan Miner v1.1.0

Open-source Windows-first CPU/GPU mining launcher with a polished desktop dashboard, live monitoring, automation features, and built-in XMRig installer.

## Features
- **Dashboard**: 10 real-time stat cards (status, hashrate, shares, uptime, last share + earnings, latency, GPU/CPU temp, restarts), live hashrate chart, miner output console
- **Stats**: Performance tab (hashrate chart with 1h/4h/6h/12h/24h/All time-range buttons, ShareFeed event column) and System tab (connection status, drops, uptime, worker, threads, peak hashrate)
- **Settings** organized across 6 tabs: Pool (multi-pool failover), GPU (NVIDIA CUDA), Miner (algorithm, threads, TLS, proxy, custom template), General (splash, tray, login, theme), Automation (auto-restart, scheduled mining, persistent log), Profiles
- **Live earnings estimate** via CoinGecko XMR/USD price feed
- **Pool latency** measurement (ping)
- **GPU/CPU temperature** monitoring
- **Configuration Profiles** — save/load/delete named profiles for one-click setup switching
- **Config export/import** to/from JSON for backup
- **Dark/Light theme** toggle — applies immediately, no restart
- **Auto-restart** on miner crash with configurable retries and delay
- **Scheduled mining** — set start/end HH:MM window
- **Persistent mining log** (auto-rotated, saved to data folder)
- **Auto-start countdown** on splash screen
- **Desktop shortcut** created on first launch
- Parses miner output live — works with **XMRig**, **SRBMiner**, or any custom miner
- Built-in XMRig installation with automatic architecture detection and post-download verification
- TLS and proxy support for pool connections
- Fully custom algorithm names (type any algorithm your miner supports)
- "Custom" miner kind with command template (`{executable} {pool} {wallet} {worker} {password} {algorithm} {threads} {extra_args}` placeholders)
- Toggle to tray on minimize/close (optional)
- "Start with Windows and begin mining automatically" (optional)
- Encrypted local configuration storage in `%APPDATA%\MayanMiner`
- Transparent 0.2% developer fee

## Default developer wallet
- XMR: `DEV_WALLET`
- Fee: 0.2%

## Quick start
```powershell
python -m pip install -r requirements.txt
python main.py
```

Preview the generated launch command without opening the GUI:
```powershell
python main.py --headless
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
1. Run `output\MayanMinerSetup.exe`.
2. Follow the standard Windows installation wizard.
3. The installer installs into `Program Files\Mayan Miner` by default and creates a Start menu shortcut (and optionally a desktop shortcut).
4. All app data (encrypted settings, encryption key, downloaded XMRig binary) lives in `%APPDATA%\MayanMiner` — separate from program files.
5. Uninstall using Windows Settings > Apps > Mayan Miner, or the uninstall shortcut in the Start menu. You will be asked whether to also delete the `%APPDATA%\MayanMiner` folder.

## Repository layout
- `main.py` — app launcher entry point
- `mayan_miner/` — application package
  - `app.py` — Tk UI (dashboard + stats + settings tabs)
  - `widgets.py` — live chart, stat-card, and ShareFeed widgets
  - `stats.py` — parses live miner stdout into hashrate/shares history
  - `splash.py` — optional startup splash screen
  - `tray.py` — system tray integration
  - `autostart.py` — Windows "start on login" registry helper
  - `config.py`, `miner.py`, `updater.py` — settings, launch-command building, XMRig updater
- `installer/` — installer script and build workflow
- `output/` — packaged build artifacts (ignored by git)
- `tests/` — unit tests
- `assets/` — icons and images

## Repository
https://github.com/bugsfreeweb/MayanMiner

## License
MIT
