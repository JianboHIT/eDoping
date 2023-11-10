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

if [ -z "$(command -v pyinstaller)" ]; then
  echo "Error: pyinstaller not found. Aborting."
  exit 1
fi

if [ "$1" == "onedir" ]; then
  pyinstaller -n edp $(cat pkg_files) \
    && echo "Built standalone EDOPONG [edp] program dir successfully!"
else
  pyinstaller -Fn edp $(cat pkg_files) \
    && echo "Built standalone EDOPONG [edp] program successfully!"
fi
