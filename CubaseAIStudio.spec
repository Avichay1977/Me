# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Cubase AI Studio
Build with: pyinstaller CubaseAIStudio.spec
"""

import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect Google AI dependencies
google_hidden_imports = collect_submodules('google.generativeai')
google_hidden_imports += collect_submodules('google.ai.generativelanguage')
google_hidden_imports += collect_submodules('google.api_core')
google_hidden_imports += collect_submodules('google.auth')

a = Analysis(
    ['launcher.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('templates', 'templates'),
        ('cubase_bridge', 'cubase_bridge'),
        ('macros', 'macros'),
    ],
    hiddenimports=[
        'flask',
        'flask_cors',
        'dotenv',
        'werkzeug',
        'jinja2',
        'markupsafe',
        'itsdangerous',
        'click',
    ] + google_hidden_imports,
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
    name='CubaseAIStudio',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # No console window
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
    name='CubaseAIStudio',
)
