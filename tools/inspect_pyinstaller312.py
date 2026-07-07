import sys
import importlib.util

print('sys.executable:', sys.executable)
spec = importlib.util.find_spec('PyInstaller')
print('find_spec:', spec)
try:
    import PyInstaller
    print('PyInstaller.__file__:', getattr(PyInstaller, '__file__', None))
except Exception as e:
    print('PyInstaller import error:', repr(e))
