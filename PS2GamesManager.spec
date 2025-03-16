# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['gui.py'],
    pathex=[],
    binaries=[],
    datas=[('db_playstation2_official_as.json', '.'), ('db_playstation2_official_au.json', '.'), ('db_playstation2_official_eu.json', '.'), ('db_playstation2_official_jp.json', '.'), ('db_playstation2_official_ko.json', '.'), ('db_playstation2_official_us.json', '.'), ('assets', 'assets'), ('assets/linux', 'linux'), ('assets/ps2gamesmanager.desktop', '.'), ('assets/ps2gamesmanager.png', '.')],
    hiddenimports=['PIL._tkinter_finder', 'customtkinter', 'PIL._tkinter_finder', 'PIL._imaging', 'PIL._imagingft', 'PIL._imagingmath'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='PS2GamesManager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets/icon.ico'],
)
