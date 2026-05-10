# -*- mode: python ; coding: utf-8 -*-
#
# One-folder (COLLECT) build — starts much faster than one-file, which unpacks to
# %TEMP% on every launch (often 30–90s+ on first run + AV scanning).

block_cipher = None

a = Analysis(
    ['server.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('app_paths.py', '.'),
        ('db_manager.py', '.'),
        ('models.py', '.'),
        ('runAiBot.py', '.'),
        ('supervisor.py', '.'),
        ('migrate_encryption.py', '.'),
        ('modules', 'modules'),
        ('routes', 'routes'),
        ('run_ai_bot', 'run_ai_bot'),
        ('services', 'services'),
        ('utils', 'utils'),
        ('config', 'config'),
    ],
    hiddenimports=[
        'fastapi',
        'uvicorn',
        'pydantic',
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'uvicorn.lifespan.off',
        'multipart',
        'stripe',
        'undetected_chromedriver',
        'pyautogui',
        'google.generativeai',
        'openai',
    ],
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
    name='server',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    runtime_tmpdir=None,
    console=True,
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
    upx=False,
    upx_exclude=[],
    name='server',
)
