# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

from PyInstaller.utils.hooks import collect_all


project_root = Path(SPECPATH).parent

datas = []
binaries = []
hiddenimports = []

for package_name in (
    "markitdown",
    "magika",
    "charset_normalizer",
    "pdfminer",
    "pdfplumber",
    "mammoth",
    "pptx",
    "pandas",
    "openpyxl",
    "xlrd",
    "bs4",
    "markdownify",
    "defusedxml",
    "olefile",
    "pydub",
    "speech_recognition",
    "youtube_transcript_api",
    "lxml",
    "PIL",
):
    collected_datas, collected_binaries, collected_hiddenimports = collect_all(package_name)
    datas += collected_datas
    binaries += collected_binaries
    hiddenimports += collected_hiddenimports


a = Analysis(
    [str(project_root / "packaging" / "launcher.py")],
    pathex=[str(project_root / "src")],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    [],
    exclude_binaries=True,
    name="MarkItDown Desktop",
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
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="MarkItDown Desktop",
)
