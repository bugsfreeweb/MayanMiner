# Mayan Miner

Mayan Miner is an open-source, Windows-first CPU/GPU mining launcher with a polished desktop dashboard. It includes built-in XMRig installer support so users do not need to install a separate miner manually.

## Features
- **Three-tab dashboard**: **Dashboard** (live status, hashrate graph, miner output), **Stats** (performance charts with time-range controls, share/recent-event feed, system info), and **Settings** (pool/wallet/miner/algorithm, TLS, proxy, GPU, general)
- **Real-time hashrate graph** with 1h/4h/6h/12h/24h/All time-range buttons, plus at-a-glance stat cards (status, hashrate, accepted/rejected shares, uptime, last share)
- **ShareFeed**: Animated column showing recent mining events with emoji indicators (smiling for accepted, sad for rejected)
- Parses miner output live — works with **XMRig**, **SRBMiner**, or any custom miner
- **Built-in XMRig installation** and automatic miner updates with post-download verification
- **TLS** and **proxy** support for pool connections
- Fully custom algorithm names (type any algorithm your miner supports)
- "Custom" miner kind with command template (`{executable} {pool} {wallet} {worker} {password} {algorithm} {threads} {extra_args}` placeholders)
- Multi-pool failover support
- GPU mining with NVIDIA CUDA support
- **Dashboard**: real-time stat cards, live hashrate chart, miner output console with Start/Stop controls
- **Stats**: Performance tab (hashrate chart with time ranges + ShareFeed event column) and System tab (connection status, drops, uptime, worker, threads, peak hashrate)
- Toggleable dark-only palette with professional styling
- Minimize/close to system tray (optional)
- "Start with Windows and begin mining automatically" (optional)
- Encrypted local configuration storage in `%APPDATA%\MayanMiner`
- Built-in developer wallet with transparent 0.2% developer fee

## Default developer wallet
- XMR: `4AmMooquAZ3JUAjuJTEDNZSxw9gmR5VuaMzKrmxjfHXuh1TGYdu3QxuEXLPhhSTZFmcA5DYfyGn3Z4Nfa27ionur4wwha1o`
- Developer fee: 0.2%

## Run locally
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
  - `app.py` — the Tk UI (dashboard + stats + settings tabs)
  - `widgets.py` — the dependency-free live chart, stat-card, and ShareFeed widgets
  - `stats.py` — parses live miner stdout into hashrate/shares history
  - `splash.py` — the optional startup splash screen
  - `tray.py` — system tray integration (optional `pystray` dependency)
  - `autostart.py` — Windows "start on login" registry helper
  - `config.py`, `miner.py`, `updater.py` — settings, launch-command building, XMRig updater
- `installer/` — installer script and build workflow
- `output/` — packaged build artifacts (ignored by git)
- `tests/` — unit tests
- `assets/` — icons and images

## Repository
This project is intended for public GitHub hosting as [MayanMiner](https://github.com/bugsfreeweb/MayanMiner).

## License
MIT
