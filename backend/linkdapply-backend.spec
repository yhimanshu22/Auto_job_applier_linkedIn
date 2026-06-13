# -*- mode: python ; coding: utf-8 -*-
"""Build: uv run pyinstaller linkdapply-backend.spec (from backend/)"""

import sys
from pathlib import Path

backend = Path(SPECPATH)

a = Analysis(
    [str(backend / "linkdapply_backend_entry.py")],
    pathex=[str(backend)],
    binaries=[],
    datas=[
        (str(backend / "config"), "config"),
        (str(backend / "linkedin_automation" / "topics.txt"), "linkedin_automation"),
        (str(backend / "linkedin_automation" / "content_calendar.txt"), "linkedin_automation"),
    ],
    hiddenimports=[
        "uvicorn.logging",
        "uvicorn.loops",
        "uvicorn.loops.auto",
        "uvicorn.protocols",
        "uvicorn.protocols.http",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespan",
        "uvicorn.lifespan.on",
        "engineio.async_drivers",
        "sqlalchemy.dialects.sqlite",
        "sqlalchemy.dialects.postgresql",
        "psycopg2",
        "selenium",
        "undetected_chromedriver",
        "cryptography",
        "stripe",
        "multipart",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest", "pytest_asyncio"],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="linkdapply-backend",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
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
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="linkdapply-backend",
)
