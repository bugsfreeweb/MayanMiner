# Mayan Miner v2.0.2

Open-source Windows-first CPU/GPU mining launcher with a polished desktop dashboard, multi-coin mining, multi-miner support, live monitoring, automation features, and built-in miner installers.

## What's New in v2.0.2

### New Features
- **Pool Priority Ordering** — Move pools up/down in the Pools tab to set primary and failover priority by sequence
- **Blockchain Stats in Detail Popup** — Block height and network difficulty now displayed alongside hashrate, shares, and earnings
- **Configurable Max Coins** — Settings > General > Display lets you set 1-20 coins on the dashboard (default 4)
- **Coin Details Popup Improvements** — Added DIFFICULTY and BLOCK HEIGHT stat cards with real-time updates

### Improvements
- **Price Display for All Coins** — All coins on dashboard now show live CoinGecko price data whether mining or not (previously only showed when actively mining)
- **Custom Coin Price Tracking** — Custom coins with CoinGecko IDs now get automatic price fetching
- **SRBMiner Share Parsing** — Expanded regex patterns to correctly parse SRBMiner's `Results: N, M` output format for shares/rejected stats
- **Block Height & Difficulty Parsing** — Expanded patterns to match `new block #N`, `at height N`, `pool diff:`, `current diff:` formats from various miners
- **Rig Management Scrollbar** — Scrollbar now hidden when content fits, mouse wheel scrolling enabled
- **Settings Display Padding** — Improved spacing between labels and input fields in General > Display

### Bug Fixes
- Fixed price display only working for XMR — now all coins show price/status
- Fixed shares/rejected not tracking for SRBMiner-mined coins
- Fixed block height and difficulty showing "--" for non-XMR coins
- Fixed dashboard tracker variable scope issue causing potential crash
- Fixed rig management page crash and scrollbar always visible
- Fixed SRBMiner CPU mining using wrong flags (`--cpu-threads`/`--disable-gpu` instead of `--threads`)
- Fixed coin mining restrictions — all coins can now use XMRig or SRBMiner for CPU or GPU

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
- **Custom miners** — add up to 4 custom miner executables with command templates
- **Coin search with custom coin creation** — add any coin not in the database

### Settings & Configuration
- **6 tabs**: Pools, Hardware, Miner Tools, General, Automation, Profiles
- **Pools tab** — multi-coin pool management with per-coin pool lists, TLS and proxy support, **move up/down for priority ordering**
- **Miner Tools tab** — 2-column layout (XMRig left, SRBMiner right), separate Install/Update buttons, custom miner grid
- **General tab** — splash, tray, theme settings, configurable max coins, graph history points (dev fee displayed but not editable)
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
- **Encrypted local configuration** storage in `%LOCALAPPDATA%\MayanMiner`
- **App update check** — checks GitHub releases, disables button if no update available
- **Transparent 0.2% developer fee** (not editable)
- **Responsive UI** — adapts to different screen sizes and DPI settings

## Default developer wallet
- XMR: `DEV_WALLET_ADDRESS`
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
```powershell
.\build_msi.ps1
```

The MSI installer will be written to the `output` folder as `MayanMiner-Setup.msi`.

## Installation and uninstall
1. Run `output\MayanMiner-Setup.msi`.
2. Follow the standard Windows installation wizard.
3. The installer installs to `%LOCALAPPDATA%\MayanMiner` (per-user) and creates a Start menu shortcut.
4. All app data (encrypted settings, encryption key, downloaded miner binaries) lives in `%LOCALAPPDATA%\MayanMiner`.
5. Uninstall using Windows Settings > Apps > Mayan Miner, or the uninstall shortcut in the Start menu.

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
- `installer/` — WiX MSI installer scripts
- `output/` — packaged build artifacts (ignored by git)
- `tests/` — unit tests
- `assets/` — icons and images
- `version_info.txt` — EXE metadata (FileVersion, ProductVersion, CompanyName, etc.)

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

## Repository
https://github.com/bugsfreeweb/MayanMiner

## License
MIT
