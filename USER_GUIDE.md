# Mayan Miner v1.1.0 User Guide

## Table of Contents
1. [Quick Start](#quick-start)
2. [Dashboard](#dashboard)
3. [Stats Tab](#stats-tab)
4. [Settings Tab](#settings-tab)
5. [Configuration Profiles](#configuration-profiles)
6. [Automation](#automation)
7. [Theme](#theme)
8. [Tray & Startup](#tray--startup)
9. [Frequently Asked Questions](#frequently-asked-questions)

---

## Quick Start

1. Launch Mayan Miner (a splash screen appears briefly).
2. Go to **Settings > Pool** — enter your pool URL and wallet address.
3. Click **Save settings** at the bottom.
4. Go to **Dashboard** and click **Start mining**.
5. Watch live hashrate, shares, and monitoring cards update in real time.

If you do not have XMRig installed, click **Install / update XMRig** on the Settings page — Mayan Miner will download the correct build for your system automatically.

---

## Dashboard

The main view shows 10 stat cards in two rows:

**Row 1** — Mining status
| Card | Description |
|------|-------------|
| STATUS | Current miner status (Ready / Mining / Stopped / Failed) |
| HASHRATE | Current hashrate |
| ACCEPTED / REJECTED | Share counts |
| UPTIME | Mining session duration |
| LAST SHARE | Time since last share accepted |

**Row 2** — Live monitoring
| Card | Description |
|------|-------------|
| EST. EARNINGS | Estimated daily earnings in USD or XMR (fetched from CoinGecko every 5 min) |
| POOL LATENCY | Ping to the pool server (measured every 30s) |
| GPU TEMP | GPU temperature and fan speed (NVIDIA only) |
| CPU TEMP | CPU temperature |
| RESTARTS | Auto-restart attempt counter |

Below the cards:
- **Live hashrate chart** — plots your hashrate over time
- **Miner output console** — full miner stdout/stderr with a **Clear** button
- **Start mining / Stop** buttons

---

## Stats Tab

Two sub-tabs:

### Performance
- **Hashrate chart** with time-range buttons: 1h, 4h, 6h, 12h, 24h, All (click any to filter)
- **ShareFeed** — live feed of accepted/rejected shares with emoji indicators
- Info: active coin, algorithm, accepted/rejected counts, acceptance rate, pool explorer link

### System
- Connection status, connection drops, miner uptime, worker name, CPU/GPU thread counts, peak hashrate

---

## Settings Tab

Organised into 6 tabs:

### Pool
- Add / Edit / Remove pools (first enabled pool is primary). Supports failover.

### GPU
- Enable GPU mining, select GPU devices, set GPU threads per device.

### Miner
- Miner kind (XMRig / SRBMiner / custom)
- Algorithm, CPU threads, use-all-cores toggle
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
A: This was a bug in v1.0.0. Upgrading to v1.1.0 and saving settings again preserves all profiles.

**Q: What is the 0.2% developer fee?**
A: Every 499 seconds, the launcher mines for ~1 second to the developer wallet to support continued development.
