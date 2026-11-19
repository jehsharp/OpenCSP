# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for SOFAST GUI application
"""

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect all opencsp modules
opencsp_modules = collect_submodules('opencsp')

# Collect data files from matplotlib, imageio, and other packages
datas = []
datas += collect_data_files('matplotlib', include_py_files=True)
datas += collect_data_files('imageio')
datas += collect_data_files('PIL')
datas += collect_data_files('cv2')

# Add opencsp package as data
datas += [('opencsp', 'opencsp')]

# Hidden imports needed by the application
hiddenimports = [
    'tkinter',
    'tkinter.filedialog',
    'tkinter.messagebox',
    'tkinter.simpledialog',
    'numpy',
    'numpy.core',
    'numpy.core._multiarray_umath',
    'scipy',
    'scipy.spatial',
    'scipy.spatial.transform',
    'scipy.interpolate',
    'scipy.optimize',
    'scipy.ndimage',
    'scipy.special',
    'scipy.sparse',
    'matplotlib',
    'matplotlib.pyplot',
    'matplotlib.backends',
    'matplotlib.backends.backend_tkagg',
    'matplotlib.figure',
    'PIL',
    'PIL.Image',
    'PIL._imaging',
    'imageio',
    'imageio.core',
    'imageio.plugins',
    'h5py',
    'h5py._hl',
    'pandas',
    'cv2',
    'pyproj',
    'sympy',
    'pkg_resources',
    'pkg_resources.py2_warn',
] + opencsp_modules

# Binaries (leave empty for now)
binaries = []

a = Analysis(
    ['opencsp/app/sofast/SofastGUI.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
        'jupyter',
        'notebook',
        'IPython',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='sofast',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Set to False if you want no console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='sofast',
)
