import os
import sys
import tempfile
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
distpath = project_root / 'output'
tmpdir = Path(tempfile.gettempdir()) / 'mayan_build'
workpath = tmpdir / 'work'
specpath = tmpdir / 'spec'
entry = project_root / 'main.py'

distpath.mkdir(parents=True, exist_ok=True)
workpath.mkdir(parents=True, exist_ok=True)
specpath.mkdir(parents=True, exist_ok=True)

assets_dir = project_root / 'assets'
icon_path = assets_dir / 'logo.ico'
logo_data_arg = f"{assets_dir / 'logo.png'}{os.pathsep}assets"

args = [
    '--clean',
    '--log-level=DEBUG',
    '--noconfirm',
    '--onefile',
    '--windowed',
    '--name', 'MayanMiner',
    '--icon', str(icon_path),
    '--add-data', logo_data_arg,
    '--hidden-import', 'pystray._win32',
    '--distpath', str(distpath),
    '--workpath', str(workpath),
    '--specpath', str(specpath),
    str(entry),
]

print('Running PyInstaller with args:')
print(' '.join(args))

import PyInstaller.__main__

PyInstaller.__main__.run(args)
