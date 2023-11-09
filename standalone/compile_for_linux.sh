#!/usr/bin/env bash
# 
# Usage: (1) bash compile_for_linux.sh
#        (2) bash compile_for_linux.sh onedir
#        (3) bash compile_for_linux.sh clear
# 
# NOTE: For build process optimization, a fresh virtual
#   environment is essential, one that includes solely
#   PyInstaller and the dependencies it requires.
# 
# Author: Jianbo ZHU
# Date: 2023.11.08


if [ "$1" == "clear" ]; then
  rm -rf build dist src edp.spec pkg_files 2>/dev/null
  exit 0
fi

SRCDIR=../src/edoping

rm -rf src 2>/dev/null      # clear src directory
mkdir src
cp -r $SRCDIR/[^__]*.py src

ls src/* | tee pkg_files

for fn in $(cat pkg_files | awk -F '[/.]' '{print $2}'); do
  for fp in $(cat pkg_files | awk -F '[/.]' '{print $2}'); do
    sed -i "s/^from .$fp/from  $fp/g" src/$fn.py
  done
done

if [ "$1" == "onedir" ]; then
  cat > edp.spec << EOF
# -*- mode: python ; coding: utf-8 -*-

filestr='''
src/xxx.py
'''

a = Analysis(
    filestr.split(),
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
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
    [],
    exclude_binaries=True,
    name='edp',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
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
    upx=True,
    upx_exclude=[],
    name='edp',
)
EOF
else
  cat > edp.spec << EOF
# -*- mode: python ; coding: utf-8 -*-

filestr='''
src/xxx.py
'''

a = Analysis(
    filestr.split(),
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
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
    name='edp',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
EOF
fi

sed -i '/^src/d' edp.spec
sed -i '/^filestr/r pkg_files' edp.spec

command -v pyinstaller >/dev/null 2>&1 \
  && pyinstaller edp.spec \
  && echo "Built standalone EDOPONG [edp] program successfully!"
