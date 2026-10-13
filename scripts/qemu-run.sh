#!/bin/sh
# Запуск обстриженного ядра в QEMU (из локального префикса, без root).
# Usage: scripts/qemu-run.sh [доп. -append куски] [доп. -device ...]
KB="$(cd "$(dirname "$0")/.." && pwd)"
Q="$KB/cache/pqemu"
export LD_LIBRARY_PATH="$Q/usr/lib/x86_64-linux-gnu:$Q/usr/lib"
export QEMU_AUDIO_DRV=none

BZ="$KB/linux/src/arch/x86/boot/bzImage"
RAM="$KB/userland/initramfs.gz"
OWN="console=ttyS0"

[ -f "$RAM" ] && INITRD="-initrd $RAM"

exec "$Q/usr/bin/qemu-system-x86_64" \
    -L "$Q/usr/share/qemu" \
    -m 256 -nographic -no-reboot \
    -kernel "$BZ" \
    -append "$OWN" \
    $INITRD \
    "$@"
