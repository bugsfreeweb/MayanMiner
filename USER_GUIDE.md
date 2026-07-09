# Mayan Miner v1.2.0 User Guide

## Table of Contents
1. [Quick Start](#quick-start)
2. [Dashboard](#dashboard)
3. [Animated Banner](#animated-banner)
4. [Miner Output Log & Collapse](#miner-output-log--collapse)
5. [Multi-Pool Management](#multi-pool-management)
6. [Stats Tab](#stats-tab)
7. [Settings Tab](#settings-tab)
8. [Configuration Profiles](#configuration-profiles)
9. [Automation](#automation)
10. [Theme](#theme)
11. [Tray & Startup](#tray--startup)
12. [Frequently Asked Questions](#frequently-asked-questions)

---

## Quick Start

1. Launch Mayan Miner (a splash screen appears briefly).
2. Go to **Settings > Pool** — click **Add pool**, enter your pool URL and wallet address.
3. Click **Save settings** at the bottom.
4. Go to **Dashboard** and click **Start mining**.
5. Watch live hashrate, shares, blocks found, and monitoring cards update in real time.

If you do not have XMRig installed, click **Install / update XMRig** on the Settings page — Mayan Miner will download the correct build for your system automatically.

---

## Dashboard

The main view shows 12 stat cards in two rows:

**Row 1** — Mining status
| Card | Description |
|------|-------------|
| STATUS | Current miner status (Ready / Mining / Stopped / Failed) |
| HASHRATE | Current hashrate (updates every second) |
| ACCEPTED / REJECTED | Share counts |
| UPTIME | Mining session duration |
| LAST SHARE | Time since last share accepted |

**Row 2** — Live monitoring
| Card | Description |
|------|-------------|
| EST. EARNINGS | Estimated daily earnings in USD or XMR. Hidden for non-XMR coins (RVN, ETH, ETC, etc.) and shows the coin name instead. |
| POOL LATENCY | Ping to the pool server (measured every 30s) |
| GPU TEMP | GPU temperature and fan speed (NVIDIA only) |
| CPU TEMP | CPU temperature |
| RESTARTS | Auto-restart attempt counter |
| BLOCKS FOUND | Number of blocks mined (detected from miner output; flashes cyan on new block) |

Cards are compact-sized to leave more room for the chart and console.

Below the cards:
- **Animated banner** (see below)
- **Live hashrate chart** — plots your hashrate over time with a share flash effect
- **Miner output console** — full miner stdout/stderr with **Clear** and **Collapse/Expand** buttons
- **Start mining / Stop** buttons

---

## Animated Banner

Positioned at the top of the dashboard (row 0), the canvas-based animated banner shows:

- **Coin name** (e.g. Monero (XMR), Ravencoin (RVN), Ethereum (ETH))
- **Algorithm** (e.g. rx/0, kawpow, ethash)
- **Pool index** — `[1/3]` when multiple enabled pools exist
- **Current hashrate** when mining is active

The text colour cycles through a pulsing hue, and a glowing progress bar animates below the text. When not mining, it displays "Ready" in muted grey.

---

## Miner Output Log & Collapse

The console at the bottom of the dashboard can be collapsed to give the hashrate chart more vertical space:

- Click **▲ Collapse** — the log text area hides and the chart expands to fill the gap
- Click **▼ Expand** — the log reappears and the chart returns to its normal size

Use **Clear** to empty the log at any time.

---

## Multi-Pool Management

Mayan Miner v1.3.0 supports independent pools, each with its own:

- URL, wallet, worker, password
- Algorithm + coin (auto-detected coin name from algorithm)
- Enabled/disabled toggle

**How it works:**
1. Go to **Settings > Pool**.
2. Click **Add pool** to add a new pool entry.
3. Each pool stores its own algorithm and coin selection.
4. The first **enabled** pool in the list is used for mining.
5. Use the **Toggle enabled** button to enable/disable a pool (the button text updates to "Enable pool" or "Disable pool" based on the selected pool's state).
6. Use **Set as default** in the Miner tab to reorder the pool list — the matching pool moves to the top.

**Pool failover:**
- If the miner crashes or the connection drops twice, the app automatically switches to the next enabled pool and restarts mining.
- A `[failover]` message appears in the log indicating the switch.
- If no more pools are available, standard auto-restart logic takes over.

**Pool selection in the dashboard list:**
- ✓ = enabled, ✗ = disabled
- ▶ = currently active pool (shown during mining)
- Coin name in `[brackets]` helps identify each pool

---

## Stats Tab

Two sub-tabs:

### Performance
- **Hashrate chart** with time-range buttons: 1h, 4h, 6h, 12h, 24h, All (click any to filter)
- **ShareFeed** — live feed of accepted/rejected shares with emoji indicators
- Info: active coin, algorithm, accepted/rejected counts, acceptance rate, pool explorer link

### System
- Connection status, connection drops, miner uptime, worker name, CPU/GPU thread counts, peak hashrate, active pool URL and wallet

---

## Settings Tab

Organised into 6 tabs:

### Pool
- Add / Edit / Remove / Toggle enabled pools. Each pool has its own URL, wallet, worker, password, algorithm, and enabled flag. The list shows coin names and active status.

### GPU
- Enable GPU mining, select GPU devices, set GPU threads per device.

### Miner
- Miner kind (XMRig / SRBMiner / custom)
- Algorithm, CPU threads, use-all-cores toggle
- **Set as default** — reorders the pool list so the pool with this algorithm becomes first
- Miner executable path (Browse or use Install/Update button)
- Extra args, TLS, proxy, custom command template
- Live command preview

### General
- Show splash screen on startup
- Keep running in system tray when minimized
- Show tray icon
- Start mining automatically at Windows login
- **Theme** — Dark / Light (Apply changes immediately, no restart needed)
- Version info and **Open data folder** shortcut

### Automation
- **Auto-restart on crash** — enable, set max retries and delay (seconds)
- **Scheduled mining** — enable, set start and end time (HH:MM 24-hour)
- **Persistent mining log** — saves miner output to `%APPDATA%\MayanMiner\logs\` (auto-rotated at 5MB)

### Profiles
- **Configuration Profiles** — save your current settings as a named profile, load any saved profile to restore all settings instantly, delete unwanted profiles
- **Config Backup** — export settings to a JSON file, import from a previous backup

---

## Configuration Profiles

Profiles store all pool, miner, GPU, and connection settings for quick switching.

### Save a profile
1. Go to **Settings > Profiles**.
2. Type a name in the **Name** field.
3. Click **Save** — the profile appears in the list.

### Load a profile
1. Click on a saved profile in the list.
2. Click **Load** — all settings (pool, threads, GPU, algo, proxy, TLS) are restored instantly.

### Delete a profile
1. Select the profile in the list.
2. Click **Delete** and confirm.

> Profiles persist across app restarts and are not lost when saving general settings.

---

## Automation

### Auto-restart
If the miner crashes, Mayan Miner can restart it automatically. Configure the maximum number of retry attempts and the delay between restarts.

### Pool failover
When enabled with multiple pools, sustained connection drops (2+) or a miner crash triggers failover to the next enabled pool in the list — no manual intervention needed.

### Scheduled mining
Set a daily time window (e.g., 22:00 to 08:00) for automatic mining. The app starts/stops the miner when the window opens/closes.

### Persistent mining log
When enabled, all miner output is written to a daily log file in the data folder. Logs older than 5MB are rotated automatically.

---

## Theme

Choose between **Dark** and **Light** themes in **Settings > General**. Click **Apply** — the entire UI switches immediately without restarting the app.

---

## Tray & Startup

- **Minimize to tray** — when enabled, closing or minimising the window hides Mayan Miner to the system tray. Right-click the tray icon to show the window, start/stop mining, or exit.
- **Start on login** — registers Mayan Miner to launch when you log into Windows (starts minimised to tray). If "Start mining automatically" is also enabled, mining begins immediately.

---

## Frequently Asked Questions

**Q: Where are my settings stored?**
A: `%APPDATA%\MayanMiner\config.json` (encrypted). The encryption key is stored alongside it. You can open the data folder from **Settings > General > Open data folder**.

**Q: The miner fails to start with "not compatible" error.**
A: Click **Install / update XMRig** to re-download the correct architecture build for your system.

**Q: How do I switch from dark to light theme?**
A: Go to **Settings > General**, select Light, click **Apply**. The change is immediate.

**Q: How do I back up my configuration?**
A: Go to **Settings > Profiles**, click **Export config**. Save the JSON file to a safe location. To restore, click **Import config** and select the file.

**Q: My saved profiles disappeared.**
A: This was a bug in v1.0.0. Upgrading to v1.2.0 and saving settings again preserves all profiles.

**Q: What is the 0.2% developer fee?**
A: Every 499 seconds, the launcher mines for ~1 second to the developer wallet to support continued development.

**Q: How do I add multiple pools?**
A: Go to **Settings > Pool**, click **Add pool** for each pool. Each pool can have a different algorithm and coin. The first enabled pool is used; failover switches to the next on connection loss.

**Q: Why is EST. EARNINGS showing `— (RVN)` instead of a dollar amount?**
A: Earnings estimates are only available for Monero (XMR / rx/* algorithms). For other coins like Ravencoin, Ethereum, or Ethereum Classic, the card displays the coin name instead.

**Q: How does pool failover work?**
A: If the connection drops twice or the miner crashes, the app automatically switches to the next enabled pool. A `[failover]` entry is written to the log. When all pools are exhausted, standard auto-restart applies.

**Q: Can I see blocks found?**
A: Yes — the **BLOCKS FOUND** card on the dashboard shows the count and flashes cyan when a new block is detected in the miner output.
