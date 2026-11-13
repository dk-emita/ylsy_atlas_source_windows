"""Desktop package with the Windows ICU implementation used by Qt and its child process."""
from pathlib import Path
import re

from PyInstaller.utils.hooks import collect_submodules

root = Path(SPECPATH).parent
a = Analysis(
    [str(root / 'run.py')],
    pathex=[str(root)],
    binaries=[],
    datas=[(str(root / name), name) for name in ('web', 'assets', 'resources')],
    hiddenimports=collect_submodules('keyring.backends'),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[str(root / 'scripts' / 'qt_system_runtime.py')],
    excludes=[],
    noarchive=False,
    optimize=0,
)
# Qt's Windows wheel uses the OS's unversioned ICU exports. A versioned ICU
# discovered elsewhere by the dependency scanner shadows the OS shim and also
# breaks QtWebEngineProcess.exe, which cannot run a Python runtime hook.
# Chromium's resources/icudtl.dat is intentionally retained.
a.binaries = [
    item for item in a.binaries
    if not re.fullmatch(r'icu(?:uc|in|dt)\d*\.dll', Path(item[0]).name, re.I)
]
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, a.binaries, a.datas, [],
    name='ylsy-atlas',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    version=str(root / 'assets' / 'version_info.txt'),
    icon=[str(root / 'assets' / 'atlas-icon.ico')],
)
