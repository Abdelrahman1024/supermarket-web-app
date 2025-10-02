# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[('supermarket.db', '.'), ('path\\to\\site-packages\\plotly', 'plotly'), ('path\\to\\site-packages\\pandas', ' pandas'), ('path\\to\\site-packages\\numpy', ' numpy')],
    hiddenimports=['scipy.special._cdflib', 'pysqlite2', 'MySQLdb', 'psycopg2', 'pkg_resources.py2_warn', 'packaging'],
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
    name='app',
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
)
