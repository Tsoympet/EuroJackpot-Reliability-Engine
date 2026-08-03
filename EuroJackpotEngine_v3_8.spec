# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = collect_submodules("sklearn") + collect_submodules("scipy")

a = Analysis(
    ["eurojackpot_desktop_app_v3_8.py"],
    pathex=[],
    binaries=[],
    datas=[
        ('EuroJackpot_Canonical_History_v3.csv', '.'),
        ('EuroJackpot_Model_Results_v3_1_Audited.json', '.'),
        ('EuroJackpot_Ticket_Template_v3_6.png', '.'),
        ('EuroJackpot_Operational_v3_7.sqlite', '.'),
        ('EuroJackpot_Wheel_54_Pair_Compact.csv', '.'),
        ('EuroJackpot_Wheel_135_Pair_Extended.csv', '.'),
        ('EuroJackpot_Wheel_198_Triple_Compact.csv', '.'),
        ('EuroJackpot_Wheel_495_Triple_Extended.csv', '.'),
        ('EuroJackpot_ENGINE_STATE_TEMPLATE_v3_5.json', '.'),
        ('eurojackpot_reliability_engine_v3.py', '.')
    ],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="EuroJackpotEngine",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon="EuroJackpot_Desktop_Icon.ico",
)
