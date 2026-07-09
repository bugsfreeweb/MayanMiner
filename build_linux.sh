#!/bin/bash
set -e
pip3 install -r requirements.txt
pyinstaller --clean --noconfirm --onefile --windowed --name MayanMiner \
    --add-data "assets/logo.png:assets" \
    --hidden-import pystray._win32 \
    main.py
