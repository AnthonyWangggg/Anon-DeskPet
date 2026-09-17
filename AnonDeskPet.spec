from PyInstaller.utils.hooks import collect_all
from pathlib import Path
import os
import sys

# The desktop tool environment also exposes Poppler/libheif DLL directories.
# Those unrelated ICU/API-set DLLs must not shadow Windows' system libraries.
if sys.platform == 'win32':
    windows = Path(os.environ.get('SystemRoot', 'C:/Windows'))
    os.environ['PATH'] = os.pathsep.join((str(Path(sys.executable).parent),
                                        str(Path(sys.base_prefix)),
                                        str(windows / 'System32'), str(windows)))

live_data, live_binaries, live_hidden = collect_all('live2d')
a = Analysis(
    ['main.py'], pathex=[],
    binaries=live_binaries,
    datas=[('assets/character', 'assets/character'), ('assets/live2d/Anon', 'assets/live2d/Anon'), *live_data],
    hiddenimports=['live2d.v3', 'OpenGL.GL', 'pynvml', *live_hidden],
    hookspath=[], hooksconfig={}, runtime_hooks=[],
    excludes=['tkinter', 'PySide6.QtWebEngineCore', 'PySide6.QtWebEngineWidgets',
              'PySide6.QtQml', 'PySide6.QtQuick', 'PySide6.QtPdf', 'PySide6.QtMultimedia'],
    noarchive=False,
)
# Windows 10/11 supplies ICU and the UCRT/API sets required by current Qt.
# Do not redistribute similarly named binaries discovered in unrelated tools.
if sys.platform == 'win32':
    a.binaries = [entry for entry in a.binaries
                  if not (Path(entry[0]).name.lower().startswith('api-ms-')
                          or Path(entry[0]).name.lower() in ('icuuc.dll', 'ucrtbase.dll')
                          or Path(entry[0]).name.lower().startswith('icudt'))]
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='AnonDeskPet',
          debug=False, bootloader_ignore_signals=False, strip=False, upx=False,
          console=False, disable_windowed_traceback=False, icon='assets/character/icon.png')
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='AnonDeskPet')
