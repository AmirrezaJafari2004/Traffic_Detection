# -*- mode: python ; coding: utf-8 -*-

import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

project_dir = os.path.abspath(SPECPATH)

datas = [
    (os.path.join(project_dir, "assets"), "assets"),
    (os.path.join(project_dir, "data"), "data"),
    (os.path.join(project_dir, "models"), "models"),
    (os.path.join(project_dir, "lanes"), "lanes"),
    (os.path.join(project_dir, "videos"), "videos"),
    (os.path.join(project_dir, "outputs"), "outputs"),
    (os.path.join(project_dir, "Doc_output"), "Doc_output"),
]

datas += collect_data_files("ultralytics")
datas += collect_data_files("customtkinter")

hiddenimports = []
hiddenimports += collect_submodules("ultralytics")
hiddenimports += collect_submodules("torch")
hiddenimports += collect_submodules("torchvision")

a = Analysis(
    [os.path.join(project_dir, "main.py")],
    pathex=[project_dir],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name="SystemTrafficDetection",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(project_dir, "assets", "app_icon.ico"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="SystemTrafficDetection",
)
