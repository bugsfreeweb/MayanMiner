# Mayan Miner Launcher v2.0.7 User Guide

## Table of Contents
1. [Quick Start](#quick-start)
2. [Dashboard](#dashboard)
3. [Multi-Coin Mining](#multi-coin-mining)
4. [Stats Page](#stats-page)
5. [Settings](#settings)
6. [Rig Management](#rig-management)
7. [Miner Tools](#miner-tools)
8. [Automation](#automation)
9. [Configuration Profiles](#configuration-profiles)
10. [Theme](#theme)
11. [Tray & Startup](#tray--startup)
12. [Frequently Asked Questions](#frequently-asked-questions)

---

## Quick Start

### Option 1: Installer
1. Run `MayanMiner.exe` from the installer build.
2. Launch Mayan Miner (a splash screen appears briefly).

### Option 2: Portable (no installation)
1. Extract the `MayanMiner-Portable` zip to any folder.
2. Run `MayanMiner.exe` directly — no installation required.

### Getting started
1. Go to **Settings > Miner Tools** — click **Install XMRig** or **Install SRBMiner** to download the miner.
2. Go to **Settings > Pools** — select a coin and configure your pool URL and wallet address.
3. Click **Save Settings** at the bottom.
4. Go to **Dashboard** — click **Add Coin** to add a coin, then click **Start** on the coin card.
5. Watch live hashrate, earnings, and charts update in real time.

---

## Dashboard

The dashboard shows coins in a **scrollable grid** (default 4, configurable up to 20 in Settings > General > Display). Each coin card displays:

| Element | Description |
|---------|-------------|
| Miner Badge | XMRig (cyan), SRBMiner (purple), or Custom (orange) |
| Ticker & Name | Coin identifier and full name |
| Hashrate | Current hashrate (updates every second) |
| Mini Chart | Live hashrate history (visible when mining) |
| Pool & Algo | Pool URL and algorithm |
| CPU Cores | Adjustable core allocation (0 = auto) |
| Est. Earnings | Estimated daily earnings in USD or live price |
| GPU Temp | Temperature and fan speed (when available) |
| Pool Latency | Ping response time to pool |
| Start/Stop | Mining control buttons |
| Details | Opens detailed stats window |

### Start/Stop Mining All
- **Start Mining All** button — starts all enabled coins at once (cyan accent)
- **Stop Mining All** button — stops all running coins with a confirmation dialog showing active coin count and names
- Button toggles between states based on current mining activity

### Stats Display by Coin Type
- **CPU coins** (XMR, SAL, ZEPH, etc.) — shows **Shares** (accepted/rejected)
- **GPU coins** (RVN, ETC, KAS, etc.) — shows **Blocks Found** count

### Adding Coins
1. Click **Add Coin** on the dashboard.
2. Search for a coin by name, ticker, or algorithm.
3. Select the mining tool (XMRig, SRBMiner, or Custom).
4. For coins not in the database, click **+ Add Custom Coin** and enter:
   - Coin Name, Ticker, Algorithm
   - Pool URL, Wallet Address
   - Mining Tool selection (XMRig/SRBMiner/Custom)
5. For **Qubic (QUBIC)**, the pool dialog shows Pool URL, Alias, and Access Token fields, plus an Import button to load settings from QubicMiner's `appsettings.json`.
6. Maximum coins configurable in Settings > General > Display (default 4).

### Detail Window
Click **Details** on any coin card to see:
- **Hashrate** — current mining speed
- **Shares/Blocks** — accepted/rejected shares (CPU) or blocks found (GPU)
- **Difficulty** — current network difficulty (parsed from miner output)
- **Block Height** — current blockchain height (parsed from miner output)
- **Uptime** — how long the miner has been running
- **Est. Earnings** — projected daily income in USD
- Full hashrate history chart
- Raw miner output log

### Price Display
All coins on the dashboard show live CoinGecko price data:
- Coins with price data show the current USD price with 24h change percentage
- Coins actively mining show estimated daily earnings based on hashrate
- Coins without CoinGecko listing show "Price not trackable"
- Custom coins with a CoinGecko ID also get automatic price tracking

---

## Multi-Coin Mining

Mayan Miner supports mining multiple coins simultaneously. Each coin runs its own miner subprocess independently.

### How it works
- Each coin card has its own **Start/Stop** button
- Each coin uses its own miner instance (separate XMRig or SRBMiner process)
- Per-coin CPU core allocation prevents resource conflicts
- Pool failover works per-coin — if a pool connection drops, the app switches to the next enabled pool for that specific coin

### Core Allocation
- **0** = auto (miner decides)
- **Max** = total CPU cores minus 10% reserve
- Adjust the Spinbox on each coin card to set the core count

### Any Coin, Any Miner
All coins in the database can be mined with either XMRig or SRBMiner, for both CPU and GPU mining. The mining tool selection is flexible — choose whichever works best for your hardware.

---

## Stats Page

The stats page shows detailed performance information for mining coins.

### Performance Tab
- **Hashrate chart** with time-range buttons: 1h, 4h, 6h, 12h, 24h, All
- **Share Difficulty chart** — visualizes share difficulty over time
- **Per-coin checkboxes** to show/hide individual coin data in the chart
- **Coin info** — active coin, algorithm, shares/blocks, acceptance rate
- **ShareFeed** — live feed of accepted/rejected shares with emoji indicators

### System Tab
- Connection status, miner uptime, peak hashrate
- Active pool info (URL, wallet)
- Price status from CoinGecko

---

## Settings

Organized into 6 tabs:

### Pools
- Select a coin from the left panel to view its pools
- **Add Pool** — enter pool URL, wallet, worker, password, algorithm
- **Mining Tool** — select which miner to use for this coin (XMRig/SRBMiner/Custom)
- **TLS** and **Proxy** checkboxes (default unticked)
- **Move Up/Down** — reorder pools to set primary and failover priority
  - First pool = primary (used first)
  - Remaining pools = auto-failover (used in order if primary fails)
- Add custom coins directly from the Pools tab

### Hardware
- GPU mining configuration (NVIDIA CUDA)
- Enable GPU, select devices, set GPU threads

### Miner Tools
- **2-column layout** — XMRig card on left, SRBMiner card on right
- Separate **Install** and **Update** buttons for each miner
- Version status displayed (installed version or "not found")
- **Custom Miners** grid (2x2) — add up to 4 custom miner executables

### General
- **Application**: Show splash screen on startup, keep running in system tray, show tray icon
- **Display**: Configure max coins on dashboard (1-20), graph history points (30-500)
- **Developer Fee**: Configurable (default 0.2%, min 0.2%, max 5.0%) — runs on the same miner tool you use
- **Logging**: Enable persistent mining log to file
- **Check Updates** — verifies GitHub releases for newer versions

### Automation
- **Auto-restart on crash** — enable, set max retries and delay
- **Scheduled mining** — set start/end HH:MM window
- **Persistent mining log** — saves miner output to data folder

### Profiles
- **Save/Load/Delete** named profiles
- **Export/Import** config as JSON backup

---

## Rig Management

The Rig Management page lets you monitor and manage multiple mining rigs from one interface.

### Adding a Rig
1. Go to **Rigs** in the sidebar.
2. Click **+ Add Rig**.
3. Enter the rig name, host/IP address, and port.
4. Click **Save**.

### Editing a Rig
1. Click **Edit** on any rig card.
2. Modify the name, host, or port.
3. Click **Save**.

### Rig Card Information
Each rig card shows:
- **Status** — online/offline (green/red dot)
- **Hashrate** — total hashrate across all coins
- **Coins** — number of coins being mined
- **GPU Temp** — current GPU temperature
- **Uptime** — how long the rig has been running
- **Shares** — total accepted shares

### Refresh
Click **Refresh All** to update all rig statuses. The local rig updates automatically from the current mining session.

---

## Miner Tools

### Installing Miners
1. Go to **Settings > Miner Tools**.
2. Click **Install XMRig** or **Install SRBMiner**.
3. The progress bar shows download status.
4. Once installed, the status shows the version and the Install button is disabled.
5. Use **Update** to download the latest version.

### Custom Miners
1. Click **+ Add Custom Miner** in the Custom Miners section.
2. Enter a name and browse for the miner executable path.
   - **XMRigCC users**: Set the daemon (`xmrigDaemon.exe`) as the Miner Executable — the daemon manages the miner internally. Leave Daemon Executable empty.
   - Use **full paths** (e.g. `C:\xmrigCC\miner\xmrigDaemon.exe`), not bare filenames.
   - Add `--cc-disabled` to **Extra args** to suppress CC Server dashboard errors if you don't run the CC Server.
3. Optionally set a **Daemon Executable** (some coins require both a miner and a daemon/node running simultaneously).
4. Select the miner type (XMRig, SRBMiner, or Custom).
5. Maximum 8 custom miners.
6. Changes are tracked — the **Save Custom Miners** button enables when you make changes and must be clicked to persist.

---

## Automation

### Auto-restart
If the miner crashes, Mayan Miner can restart it automatically. Configure the maximum number of retry attempts and the delay between restarts.

### Pool failover
When enabled with multiple pools, sustained connection drops or a miner crash triggers failover to the next enabled pool — no manual intervention needed. Use the Move Up/Down buttons in Settings > Pools to set failover order.

### Scheduled mining
Set a daily time window (e.g., 22:00 to 08:00) for automatic mining.

### Persistent mining log
When enabled, all miner output is saved to daily log files in the data folder.

---

## Configuration Profiles

Profiles store all settings for quick switching.

### Save a profile
1. Go to **Settings > Profiles**.
2. Type a name in the **Name** field.
3. Click **Save**.

### Load a profile
1. Click on a saved profile in the list.
2. Click **Load** — all settings are restored instantly.

### Delete a profile
1. Select the profile in the list.
2. Click **Delete** and confirm.

---

## Theme

Choose between **Dark** and **Light** themes in **Settings > General**. The theme applies immediately without restarting the app. Both themes now have full visibility for all UI elements including buttons, dropdowns, input fields, tabs, and disabled states.

---

## Tray & Startup

- **Minimize to tray** — when enabled, closing or minimizing the window hides Mayan Miner to the system tray. Right-click the tray icon to show the window, start/stop mining, or exit.
- **Start on login** — registers Mayan Miner to launch when you log into Windows (starts minimized to tray). If "Start mining automatically" is also enabled, mining begins immediately.

---

## Frequently Asked Questions

**Q: Where are my settings stored?**
A: `%LOCALAPPDATA%\MayanMinerLauncher\config.json` (encrypted). The app data folder also stores downloaded miner binaries and log files.

**Q: How do I mine a coin that's not in the database?**
A: Go to **Dashboard > Add Coin** (or **Settings > Pools > Add Coin**) and click **+ Add Custom Coin**. Enter the ticker, name, algorithm, and mine type (cpu/gpu). Custom coins with a CoinGecko ID get automatic price tracking.

**Q: Why is the hashrate showing 0 H/s?**
A: Make sure the miner is installed (**Settings > Miner Tools**) and a pool is configured with a valid wallet address (**Settings > Pools**).

**Q: Can I mine with both XMRig and SRBMiner at the same time?**
A: Yes. Each coin card lets you select the mining tool. You can have XMRig mining XMR on CPU while SRBMiner mines RVN on GPU simultaneously.

**Q: Why is EST. EARNINGS showing a price instead of a dollar amount?**
A: Earnings estimates require both CoinGecko price data AND an active mining hashrate. When not mining, the card shows the live CoinGecko price with 24h change. When mining, it shows estimated daily earnings.

**Q: How does pool failover work?**
A: If the connection drops or the miner crashes, the app automatically switches to the next enabled pool. Use the Move Up/Down buttons in Settings > Pools to set the failover order.

**Q: What is the developer fee?**
A: A configurable fee (default 0.2%) runs periodically to the developer wallet to support continued development. You can adjust it in Settings > General > Developer Fee (minimum 0.2%, maximum 5.0%). The fee always uses the same miner tool you're using (e.g., SRBMiner → XEL via Suprnova, XMRig → XMR via MoneroOcean).

**Q: How do I check for app updates?**
A: Go to **Settings > General** and click **Check Updates**. If a newer version is available on GitHub, the button changes to **Download Update**.

**Q: Can I see blocks found for GPU coins?**
A: Yes — the detail window shows **Blocks Found** for GPU coins (RVN, ETC, KAS, etc.) and **Shares** (accepted/rejected) for CPU coins (XMR, SAL, etc.). It also shows **Difficulty** and **Block Height** when available from miner output.

**Q: Why are CMD windows flashing when I start mining?**
A: This has been fixed. All miner subprocesses run hidden — no CMD windows should appear.

**Q: How do I add TLS or proxy to my pool?**
A: Go to **Settings > Pools**, select your coin and pool, click **Edit**, then check **Use TLS** or enter a proxy address.

**Q: How do I reorder pools for failover?**
A: Go to **Settings > Pools**, select your coin, then use the **Up** and **Down** buttons to reorder pools. The first pool is primary, the rest are failover in order.

**Q: Can I change how many coins appear on the dashboard?**
A: Yes. Go to **Settings > General > Display** and adjust "Max coins on dashboard" (1-20, default 4).

**Q: How do I manage multiple mining rigs?**
A: Go to **Rigs** in the sidebar. Click **+ Add Rig** to add remote rigs by host/IP and port. Each rig card shows status, hashrate, and mining info. The local rig updates automatically.

**Q: Does price tracking work for all coins?**
A: Yes. All coins with a CoinGecko ID get automatic price tracking. Custom coins can also have a CoinGecko ID for price data. Coins without a CoinGecko listing show "Price not trackable".

**Q: What does "cc error: unable to performRequest POST" mean?**
A: This is a XMRigCC-specific error. The XMRigCC daemon tries to report stats to the CC Server dashboard (localhost:3344). If the CC Server (`xmrigServer.exe`) is not running, this error appears but **mining is unaffected**. To suppress it, add `--cc-disabled` to Extra args in the pool settings.

**Q: How do I set up XMRigCC for coins like C64 CHAIN?**
A: XMRigCC has 3 components: xmrigServer (dashboard), xmrigDaemon (manager), xmrigMiner (worker). In Mayan Miner:
1. In **Custom Miners**, add a new entry with `xmrigDaemon.exe` as the Miner Executable (full path).
2. Set Miner type to **XMRig-args**.
3. Add `--cc-disabled` to Extra args if you don't need the CC dashboard.
4. Click **Save Custom Miners**.
5. In **Pools**, set Mining tool to **Custom** and select your saved custom miner.

The app automatically patches the daemon's `config.json` with your pool, wallet, algorithm, and thread settings before starting, so the daemon uses your configuration instead of its bundled defaults.

**Q: Why does mining fail with "Miner executable not found"?**
A: The executable path is invalid or uses a bare filename. Always use the full path (e.g. `C:\xmrig\xmrig.exe`), not just `xmrig.exe`. Use the **...** browse button to select the file.

**Q: How do I mine Qubic (QUBIC)?**
A: Qubic uses QubicMiner instead of XMRig/SRBMiner. Steps:
1. Install QubicMiner and set it up in **Settings > Miner Tools > Custom Miners**.
2. In **Settings > Pools**, select QUBIC from the coin list.
3. Click **Add Pool** — enter the Pool URL (wss://...), Alias, and Access Token. You can also click **Import from appsettings.json** to auto-fill from your QubicMiner config.
4. Click **Save** and start mining from the Dashboard.
Note: QUBIC uses an Access Token instead of a wallet address.

**Q: How do I run Mayan Miner without installing?**
A: Download the portable build, extract the zip, and run `MayanMiner.exe` directly. No installation needed — all data is stored in the extracted folder.

**Q: Why does the app freeze when I stop mining?**
A: This has been fixed. Stopping mining now runs in a background thread. The app should remain responsive while the miner shuts down. Process trees (daemon + miner) are killed together to ensure complete shutdown.
