# Mayan Miner v2.0.1 User Guide

## Table of Contents
1. [Quick Start](#quick-start)
2. [Dashboard](#dashboard)
3. [Multi-Coin Mining](#multi-coin-mining)
4. [Stats Page](#stats-page)
5. [Settings](#settings)
6. [Miner Tools](#miner-tools)
7. [Automation](#automation)
8. [Configuration Profiles](#configuration-profiles)
9. [Theme](#theme)
10. [Tray & Startup](#tray--startup)
11. [Frequently Asked Questions](#frequently-asked-questions)

---

## Quick Start

1. Launch Mayan Miner (a splash screen appears briefly).
2. Go to **Settings > Miner Tools** — click **Install XMRig** or **Install SRBMiner** to download the miner.
3. Go to **Settings > Pools** — select a coin and configure your pool URL and wallet address.
4. Click **Save Settings** at the bottom.
5. Go to **Dashboard** — click **Add Coin** to add a coin, then click **Start** on the coin card.
6. Watch live hashrate, earnings, and charts update in real time.

---

## Dashboard

The dashboard shows up to **4 coins** in a 2×2 grid. Each coin card displays:

| Element | Description |
|---------|-------------|
| Miner Badge | XMRig (cyan), SRBMiner (purple), or Custom (orange) |
| Ticker & Name | Coin identifier and full name |
| Hashrate | Current hashrate (updates every second) |
| Mini Chart | Live hashrate history |
| Pool & Algo | Pool URL and algorithm |
| CPU Cores | Adjustable core allocation (0 = auto) |
| Est. Earnings | Estimated daily earnings in USD |
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
5. Maximum 4 coins on the dashboard — the Add Coin button is disabled when at limit.

### Detail Window
Click **Details** on any coin card to see:
- Hashrate, Shares/Blocks, Uptime, Est. Earnings
- Full hashrate history chart
- Raw miner output log

---

## Multi-Coin Mining

Mayan Miner v2.0 supports mining multiple coins simultaneously. Each coin runs its own miner subprocess independently.

### How it works
- Each coin card has its own **Start/Stop** button
- Each coin uses its own miner instance (separate XMRig or SRBMiner process)
- Per-coin CPU core allocation prevents resource conflicts
- Pool failover works per-coin — if a pool connection drops, the app switches to the next enabled pool for that specific coin

### Core Allocation
- **0** = auto (miner decides)
- **Max** = total CPU cores minus 10% reserve
- Adjust the Spinbox on each coin card to set the core count

---

## Stats Page

The stats page shows detailed performance information for mining coins.

### Performance Tab
- **Hashrate chart** with time-range buttons: 1h, 4h, 6h, 12h, 24h, All
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
- First pool = primary, rest = auto-failover
- Add custom coins directly from the Pools tab (includes Pool URL, Wallet, and Mining Tool)

### Hardware
- GPU mining configuration (NVIDIA CUDA)
- Enable GPU, select devices, set GPU threads

### Miner Tools
- **2-column layout** — XMRig card on left, SRBMiner card on right
- Separate **Install** and **Update** buttons for each miner
- Version status displayed (installed version or "not found")
- **Custom Miners** grid (2×2) — add up to 4 custom miner executables

### General
- Show splash screen on startup
- Keep running in system tray when minimized
- Show tray icon
- Start mining automatically at Windows login
- **Theme** — Dark / Light (applies immediately)
- Developer fee displayed (0.2%, not editable)
- **Check Updates** — verifies GitHub releases for newer versions

### Automation
- **Auto-restart on crash** — enable, set max retries and delay
- **Scheduled mining** — set start/end HH:MM window
- **Persistent mining log** — saves miner output to data folder

### Profiles
- **Save/Load/Delete** named profiles
- **Export/Import** config as JSON backup

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
2. Enter a name and browse for the executable path.
3. Select the miner type (XMRig, SRBMiner, or Custom).
4. Maximum 4 custom miners in a 2×2 grid.

---

## Automation

### Auto-restart
If the miner crashes, Mayan Miner can restart it automatically. Configure the maximum number of retry attempts and the delay between restarts.

### Pool failover
When enabled with multiple pools, sustained connection drops or a miner crash triggers failover to the next enabled pool — no manual intervention needed.

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

Choose between **Dark** and **Light** themes in **Settings > General**. Click **Apply** — the entire UI switches immediately without restarting the app.

---

## Tray & Startup

- **Minimize to tray** — when enabled, closing or minimizing the window hides Mayan Miner to the system tray. Right-click the tray icon to show the window, start/stop mining, or exit.
- **Start on login** — registers Mayan Miner to launch when you log into Windows (starts minimized to tray). If "Start mining automatically" is also enabled, mining begins immediately.

---

## Frequently Asked Questions

**Q: Where are my settings stored?**
A: `%APPDATA%\MayanMiner\config.json` (encrypted). You can open the data folder from **Settings > General > Open data folder**.

**Q: How do I mine a coin that's not in the database?**
A: Go to **Dashboard > Add Coin** (or **Settings > Pools > Add Coin**) and click **+ Add Custom Coin**. Enter the ticker, name, algorithm, and mine type (cpu/gpu).

**Q: Why is the hashrate showing 0 H/s?**
A: Make sure the miner is installed (**Settings > Miner Tools**) and a pool is configured with a valid wallet address (**Settings > Pools**).

**Q: Can I mine with both XMRig and SRBMiner at the same time?**
A: Yes. Each coin card lets you select the mining tool. You can have XMRig mining XMR on CPU while SRBMiner mines RVN on GPU simultaneously.

**Q: Why is EST. EARNINGS showing the coin name instead of a dollar amount?**
A: Earnings estimates are only available for coins with CoinGecko price data. For coins without price data, the coin name is displayed instead.

**Q: How does pool failover work?**
A: If the connection drops or the miner crashes, the app automatically switches to the next enabled pool. A `[failover]` entry is written to the log.

**Q: What is the 0.2% developer fee?**
A: Every 499 seconds, the launcher mines for ~1 second to the developer wallet to support continued development. This fee is not editable.

**Q: How do I check for app updates?**
A: Go to **Settings > General** and click **Check Updates**. If a newer version is available on GitHub, the button changes to **Download Update**.

**Q: Can I see blocks found for GPU coins?**
A: Yes — the detail window shows **Blocks Found** for GPU coins (RVN, ETC, KAS, etc.) and **Shares** (accepted/rejected) for CPU coins (XMR, SAL, etc.).

**Q: Why are CMD windows flashing when I start mining?**
A: This has been fixed in v2.0. All miner subprocesses run hidden — no CMD windows should appear.

**Q: How do I add TLS or proxy to my pool?**
A: Go to **Settings > Pools**, select your coin and pool, click **Edit**, then check **Use TLS** or enter a proxy address.
