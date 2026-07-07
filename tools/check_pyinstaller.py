import sys
import importlib.util
import shutil

print('sys.executable:', sys.executable)
print('python_version:', sys.version.splitlines()[0])

spec = importlib.util.find_spec('PyInstaller')
if spec:
    print('PyInstaller spec origin:', spec.origin)
else:
    print('PyInstaller spec: not found')

print('pyinstaller_exe:', shutil.which('pyinstaller'))
try:
    import PyInstaller
    print('PyInstaller.__file__:', PyInstaller.__file__)
except Exception as e:
    print('PyInstaller import error:', repr(e))
