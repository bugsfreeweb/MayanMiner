# Mayan Miner Launcher v2.0.7

Open-source Windows-first CPU/GPU mining launcher with a polished desktop dashboard, multi-coin mining, multi-miner support, live monitoring, automation features, and built-in miner installers.

![Mayan ! Miner App launcher](output/dashboard.png)


## What's New in v2.0.7

### New Features
- **Stats System Redesign** — 4 beautiful circular ring cards showing Miner Status, Internet Status, CPU Status (real-time), and GPU Status (real-time via nvidia-smi)
- **Performance Status Display** — accept/reject status with emoji indicators, acceptance rate, recent events (block found, share accepted/rejected), and last share time
- **Help / About Tab** — new sidebar tab with About (publisher info), Privacy Policy, Terms & Conditions, and FAQ sections
- **Real-time System Monitoring** — CPU usage, temperature, cores/threads, frequency; GPU usage, temp, fan, VRAM via nvidia-smi
- **Recent Events Log** — scrollable event feed below system cards showing shares, blocks, and connection events
- **Editable dev fee** — General settings now allows adjusting the dev fee percentage (min 0.2%, max 5.0%, default 0.2%)
- **Start with Windows** — auto-start on Windows login with Start menu integration

### Improvements
- **System tab visual overhaul** — circular ring gauges with color-coded health indicators (green/yellow/red)
- **GPU detection** — automatic brand, model, and VRAM detection for NVIDIA/AMD/Intel GPUs
- **CPU health monitoring** — real-time CPU load with health rating (Good/Fair/Hot)
- **CPU affinity pinning** — affinity is now always set explicitly (all cores OR pinned cores) matching app settings exactly; XMRigCC daemon child processes also get pinned
- **Process name cleanup** — single Task Manager entry; console window hidden properly
- **AppData folder** — renamed to MayanMinerLauncher (auto-migrates from old MayanMiner folder)

### Bug Fixes
- **CPU affinity mismatch** — Task Manager now shows the exact cores configured in Hardware settings
- **XMRigCC daemon child affinity** — miner processes spawned by daemon also get correct affinity pinning
- **Import settings sync** — imported settings now correctly update all active coin configs

---

## What's New in v2.0.6

### New Features
- **Start with Windows** — new option in General Settings to auto-start Mayan Miner when Windows boots
- **Selected coin highlighting** — selected coin in Pools tab highlighted with accent color
- **Modern search bar** — Pools tab search redesigned with placeholder text and focus highlight

### Bug Fixes
- **Import settings now includes user data** — imported settings correctly restore coins, pools, wallets, and algorithms
- **Dashboard respects max coins limit** — dashboard only displays configured number of coins; Add button disables when limit is reached

---

## What's New in v2.0.5

### New Features
- **CPU affinity pinning** — miner processes are now pinned to specific CPU cores based on thread count, reducing CPU usage in Task Manager
- **Sidebar redesign** — larger icons, accent bar on active tab, improved spacing, better Rigs icon
- **Pool coin reorder** — reorder your active coin list with Up/Down buttons
- **Refresh button** — Pools tab now has a Refresh button to resync the coin list
- **Unsaved changes warning** — warns before closing if you have unsaved settings
- **Button disable during activity** — Save/Export/Import buttons are disabled and show status text while operations are in progress

### Improvements
- **Dropdown restyling** — all OptionMenu dropdowns now match the dark theme
- **Custom miner radio styling** — selected miner type is highlighted with accent color, others dimmed
- **Dashboard scroll behavior** — scrollbar only appears when content actually overflows; cards stay at top when few

### Bug Fixes
- **Process cleanup on stop** — miner and daemon processes are properly tree-killed on stop
- **Settings import fix** — config is copied before modification; rebuild_ui() moved to prevent widget destruction errors
- **Pools coin list fix** — coin list no longer disappears when searching; coins added from dashboard now appear instantly in Pools tab
- **Pools scrollbar auto-hide** — pools tab scrollbar now only appears when coin list overflows, matching dashboard behavior
- **Singleton instance** — prevents duplicate MayanMiner.exe processes in Task Manager (ghost process fix)
- **Save button visual feedback** — Save/Export/Import buttons now show text change ("Saving..." etc.) and properly re-enable after operations

---

## What's New in v2.0.4

### New Features
- **Qubic (QUBIC) coin support** — mine Qubic via QubicMiner with a simplified pool dialog (Pool URL, Alias, Access Token) and automatic `appsettings.json` import from the QubicMiner folder
- **Portable EXE build** — run Mayan Miner from any folder without installation; download the `MayanMiner-Portable` zip, extract, and run `MayanMiner.exe`
- **EXE uninstall cleanup** — uninstalling the app now removes the desktop shortcut and Start menu entry automatically

### Bug Fixes
- **Qubic Add Pool button** — fixed PoolDialog not saving pool data for QUBIC coin
- **Scrollbar auto-hide** — dashboard and custom miners scrollbars now only appear when content overflows the visible area
- **Mouse wheel scroll** — improved scroll behavior on Dashboard and Custom Miners tab with proper containment check (only scrolls when cursor is over the scrollable area)
- **EXE uninstall removes desktop shortcut** — uninstalling via Windows Settings or `--uninstall` flag now properly removes the desktop shortcut icon

### Improvements
- **Dev fee Xelis routing** — 0.2% dev fee for Xelis now routes to Suprnova.cc pool instead of moneroocean
- **Dev fee no-stop mining** — dev fee cycle (every 499s for ~1s) no longer triggers a full miner restart; user miner resumes immediately after dev fee completes
- **Process tree killing** — `taskkill /T /F /PID` ensures all child processes (daemon + miner) are killed together

## What's New in v2.0.3

### Bug Fixes
- **Light theme visibility fix** — improved contrast and readability across the entire light theme: buttons, dropdowns, input fields, tabs, disabled states, and scrollbars now all display correctly
- **Light palette color corrections** — fixed typo in chart fill color, darkened primary/danger/accent colors for proper contrast on light backgrounds
- **TTK widget styling** — dropdown menus, comboboxes, spinboxes, checkbuttons, and radio buttons now properly adapt colors when switching between dark and light themes
- **Button disabled states** — no longer invisible in light theme (uses proper gray tones)

### Improvements
- **Window height reduced** — main window reduced by 20px for a cleaner fit (1280x860, min 1024x760)
- **Daemon executable support** — custom miners now support an optional daemon executable (some coins require both a miner and a daemon/node to run); daemon starts automatically with the miner and stops when mining stops
- **Custom miners Save button** — custom miner changes require clicking Save to persist; button is disabled until a change is made (dirty-state tracking)
- **Subprocess working directory fix** — miner processes now run from the executable's own directory, so companion files (e.g. XMRigCC's xmrigMiner.exe) are found correctly
- **Executable validation** — clear error message if a miner executable path is invalid or missing
- **XMRigCC support** — use `xmrigDaemon.exe` as the Miner Executable (the daemon manages the miner internally); config.json is auto-patched with your pool/wallet/threads before starting; add `--cc-disabled` to Extra args to suppress CC Server dashboard errors if the CC Server is not running

## Features

### Multi-Coin Dashboard
- **Configurable grid** — mine up to 20 coins simultaneously (default 4), each with its own miner process
- **Start/Stop Mining All** — single button to start all enabled coins or stop all running coins (with confirmation)
- **Per-coin CPU core allocation** — Spinbox on each card (0 = auto, max = total cores minus 10% reserve)
- **Miner kind badge** on each card — XMRig (cyan), SRBMiner (purple), Custom (orange)
- **Live hashrate chart** and earnings estimate per coin
- **Pool health latency** displayed on each coin card
- **GPU temperature and fan speed** monitoring per coin
- **Stats display adapts per coin** — shares/rejected for CPU coins, blocks found for GPU coins
- **Mouse wheel scrollable** coin cards when content overflows

### Multi-Miner Support
- **XMRig** — primary CPU miner for RandomX and CryptoNight algorithms
- **SRBMiner-Multi** — GPU + CPU miner supporting kawpow, etchash, autolykos2, and 50+ algorithms
- **Custom miners** — add up to 8 custom miner executables with command templates, optional daemon executable support
- **XMRigCC support** — daemon-based miner that manages the miner process internally; use `xmrigDaemon.exe` as the executable; the app auto-patches the daemon's `config.json` with your pool, wallet, algorithm, and thread settings before starting
- **Coin search with custom coin creation** — add any coin not in the database

### Settings & Configuration
- **6 tabs**: Pools, Hardware, Miner Tools, General, Automation, Profiles
- **Pools tab** — multi-coin pool management with per-coin pool lists, TLS and proxy support, **move up/down for priority ordering**
- **Miner Tools tab** — 2-column layout (XMRig left, SRBMiner right), separate Install/Update buttons, custom miner grid with daemon support, Save button with dirty-state tracking
- **General tab** — splash, tray, theme settings, configurable max coins, graph history points, editable dev fee percentage
- **Automation** — auto-restart on crash, scheduled mining, persistent log
- **Profiles** — save/load/delete named profiles, config export/import

### Monitoring & Notifications
- **CoinGecko price tracking** for all coins with live USD price and 24h change
- **Earnings estimates** — daily/weekly/monthly projections based on hashrate and price
- **Fixed notification area** in sidebar — last 5-8 notifications with animations
- **Stats page** — per-coin checkboxes to filter charts, share difficulty graph, per-coin stats display
- **Miner output console** — filter by coin or show all
- **Detail window** — per-coin hashrate, shares/blocks, difficulty, block height, uptime, earnings, hashrate chart, miner log

### Rig Management
- **Multi-rig support** — add, edit, remove remote mining rigs
- **Rig status monitoring** — online/offline, hashrate, coins mining, GPU temp, uptime, shares
- **Edit rig dialog** — modify name, host, port for each rig

### Additional Features
- **Dark/Light theme** toggle — applies immediately, no restart
- **Desktop shortcut** created on first launch
- **Toggle to tray** on minimize/close (optional)
- **Start with Windows** and begin mining automatically (optional)
- **Encrypted local configuration** storage in `%LOCALAPPDATA%\MayanMinerLauncher`
- **App update check** — checks GitHub releases, disables button if no update available
- **Transparent developer fee** — configurable 0.2% default (min 0.2%, max 5.0%); fee runs on the same miner tool you use
- **Responsive UI** — adapts to different screen sizes and DPI settings

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

The executable will be written to the `output` folder as `Mayan Miner Launcher-v2.0.7.exe`.

## Build portable EXE (no installation required)
```powershell
.\build_portable.ps1
```

The portable distribution will be written to `output/MayanMiner-Portable/` — run `Mayan Miner Launcher.exe` directly from that folder.

## Installation and uninstall
1. Run `output\Mayan Miner Launcher-v2.0.7.exe` to install, or extract the portable zip and run `Mayan Miner Launcher.exe` directly.
2. The installer creates a desktop shortcut and Start menu entry.
3. All app data (encrypted settings, encryption key, downloaded miner binaries) lives in `%LOCALAPPDATA%\MayanMinerLauncher`.
4. Uninstall using Windows Settings > Apps > Mayan Miner — this also removes the desktop shortcut and registry entries.

## Repository layout
- `main.py` — app launcher entry point
- `mayan_miner/` — application package
  - `app.py` — Tk UI shell (sidebar navigation, page routing)
  - `dashboard.py` — multi-coin dashboard with configurable grid
  - `stats_page.py` — stats page with per-coin chart filtering and share difficulty graph
  - `widgets.py` — CoinCard, StatCard, MiniChart, RealtimeChart, AnimatedProgressBar, ShareFeed
  - `stats.py` — parses live miner stdout into hashrate/shares/blocks/difficulty/height history
  - `coins_db.py` — 26-coin database with pools, algorithms, and stats type classification
  - `coin_search.py` — search widget with custom coin creation
  - `price_tracker.py` — CoinGecko price tracking for all coins
  - `notifications.py` — notification center with animated widget
  - `splash.py` — startup splash screen
  - `tray.py` — system tray integration
  - `autostart.py` — Windows "start on login" registry helper
  - `config.py` — encrypted configuration management
  - `miner.py` — launch-command building for XMRig/SRBMiner/custom
  - `updater.py` — miner download and update management
  - `pool_health.py` — pool latency health check
  - `rigs_page.py` — multi-rig management
  - Settings tabs: `pools_tab.py`, `hardware_tab.py`, `miner_tools_tab.py`, `general_tab.py`, `automation_tab.py`, `profiles_tab.py`, `settings_page.py`
- `installer/` — WiX MSI installer scripts (legacy)
- `output/` — packaged build artifacts (ignored by git)
- `tests/` — unit tests
- `assets/` — icons and images
- `version_info.txt` — EXE metadata (FileVersion, ProductVersion, CompanyName, etc.)
- `build_portable.ps1` — build script for portable EXE distribution

## Supported Coins

### CPU Mining (Shares-based)
| Coin | Algorithm | Miner |
|------|-----------|-------|
| XMR (Monero) | RandomX | XMRig |
| SAL (Salvium) | RandomX | XMRig |
| ZEPH (Zephyr) | RandomX | XMRig |
| QRL | RandomX | XMRig |
| XTM (Tari) | RandomX | XMRig |
| SATASHI | RandomX | XMRig |
| CCX (Conceal) | CryptoNight R | XMRig |
| RTM (Raptoreum) | GhostRider | SRBMiner |
| EPIC (EPIC Cash) | RandomARQ | XMRig |
| CRB (Cereblix) | NeuroMorph | XMRig |

### GPU Mining (Blocks-based)
| Coin | Algorithm | Miner |
|------|-----------|-------|
| ZANO (Zano) | ProgPow Zano | SRBMiner |
| RVN (Ravencoin) | KawPow | SRBMiner |
| ETC (Ethereum Classic) | Etchash | SRBMiner |
| KAS (Kaspa) | KHeavyHash | SRBMiner |
| ERG (Ergo) | Autolykos2 | SRBMiner |
| ALPH (Alephium) | Blake3 Alephium | SRBMiner |
| FIRO (Firo) | FiroPow | SRBMiner |
| XNA (Neurai) | KawPow | SRBMiner |
| KLS (Karlsen) | KarlsenHash v2 | SRBMiner |
| FLUX (Flux) | ZelHash | SRBMiner |
| ETHW (EthereumPoW) | KawPow | SRBMiner |
| QUAI (Quai Network) | ProgPow Quai | SRBMiner |
| RXD (Radiant) | SHA512/256d Radiant | SRBMiner |
| PYI (Pyrin) | PyrinHash | SRBMiner |
| NEOX (Neoxa) | KawPow | SRBMiner |
| XLS (Xelis) | XelisHash | SRBMiner |

### Custom Mining
| Coin | Miner | Notes |
|------|-------|-------|
| QUBIC (Qubic) | QubicMiner | Uses Access Token instead of wallet; import from appsettings.json |

## Repository
https://github.com/bugsfreeweb/MayanMiner

## License
MIT
