# Mayan Miner

Mayan Miner is an open-source, Windows-first CPU mining launcher with a polished desktop dashboard. It includes built-in XMRig installer support so users do not need to install a separate miner manually.

## Features
- Modern desktop UI for mining settings and live output
- Built-in XMRig installation and automatic miner updates
- Real miner launch support with custom pools, wallets, worker names, algorithms, and extra arguments
- Encrypted local configuration storage
- Built-in developer wallet and 0.2% fee note
- Windows executable packaging with PyInstaller

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
3. The installer installs into `Program Files\Mayan Miner` by default and creates a Start menu shortcut.
4. Uninstall using Windows Settings > Apps > Mayan Miner, or use the uninstall shortcut created in the Start menu.

## Repository layout
- `main.py` — app launcher entry point
- `mayan_miner/` — application package
- `installer/` — installer script and build workflow
- `output/` — packaged build artifacts (ignored by git)
- `tests/` — unit tests

## Repository
This project is intended for public GitHub hosting as MayanMiner.
