#!/bin/sh
# Сборка обстриженного bzImage.
# 1) scripts/mkconfig.sh — мини-конфиг из linux/configs/enable.list
# 2) make bzImage
# Хост-инструменты (m4/bison/flex + libelf/libssl headers) лежат в
# cache/hosttools — без root, через scripts/setup-hosttools.py.
set -e

cd "$(dirname "$0")/../"
KB="$PWD"
HT="$KB/cache/hosttools"

[ -x "$HT/usr/bin/bison" ] || python3 scripts/setup-hosttools.py

export PATH="$HT/usr/bin:$PATH"        # m4 / bison / flex
INC="-I$HT/usr/include -I$HT/usr/include/x86_64-linux-gnu"
LIB="$HT/usr/lib/x86_64-linux-gnu"

./scripts/mkconfig.sh

cd linux/src
# objtool в 6.18 на x86 обязателен (HAVE_STATIC_CALL_INLINE / HAVE_UACCESS_VALIDATION)
# и требует libelf. Мы не профиль root: libelf взят из deb (dpkg -x) в $HT.
make -j"${KB_JOBS:-6}" \
    HOSTCFLAGS="$INC" \
    HOSTLDFLAGS="-L$LIB -Wl,-rpath,$LIB" \
    bzImage

echo
echo "=== готово ==="
ls -lh arch/x86/boot/bzImage
