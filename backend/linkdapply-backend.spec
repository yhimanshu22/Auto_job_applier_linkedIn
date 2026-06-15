# -*- mode: python ; coding: utf-8 -*-
"""Build: uv run pyinstaller linkdapply-backend.spec (from backend/)"""

from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

backend = Path(SPECPATH)

hiddenimports = [
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
    "sqlalchemy.dialects.sqlite",
    "sqlalchemy.dialects.postgresql",
    "psycopg2",
    "selenium",
    "undetected_chromedriver",
    "stripe",
    "multipart",
    "services.bot_config_cache",
    "services.smart_rate_limit",
    "services.chrome_ports",
] + collect_submodules("cryptography")

a = Analysis(
    [str(backend / "linkdapply_backend_entry.py")],
    pathex=[str(backend)],
    binaries=[],
    datas=[
        (str(backend / "config"), "config"),
        (str(backend / "linkedin_automation" / "topics.txt"), "linkedin_automation"),
        (str(backend / "linkedin_automation" / "content_calendar.txt"), "linkedin_automation"),
    ],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest", "pytest_asyncio"],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

# Onefile bundle: MSI/Tauri only ship a single sidecar exe (no _internal folder).
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="linkdapply-backend",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
