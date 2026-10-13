#!/bin/sh
# Лепка initramfs kelpOS одной командой:
#   busybox (glibc, статик) + runit (статик) + /init + /etc/runit/{1,2,3} + /service/*
# Итог: userland/initramfs.gz  →  подаётся в QEMU опцией -initrd.
set -e

KB="$(cd "$(dirname "$0")/.." && pwd)"
BUSYBOX_SRC="$KB/cache/busybox-1.38.0"
RUNIT_CMD="$KB/cache/runit/command"
R="$KB/userland/rootfs"
ETC="$KB/userland/rootfs-tpl/etc"
SVC="$KB/userland/rootfs-tpl/service"
OUT="$KB/userland/initramfs.gz"

# 1) свежий rootfs
rm -rf "$R"; mkdir -p "$R"

# 2) busybox со ссылками на все апплеты.
#    Берём готовый бинарь напрямую (make install в дереве ненадёжен: однажды
#    подсунул в rootfs пустой busybox без апплетов) и проверяем его.
BB="$BUSYBOX_SRC/busybox"
[ "$(stat -c %s "$BB")" -gt 700000 ] || { echo "FATAL: busybox мал (>700K ждём) — пересобери"; exit 1; }
mkdir -p "$R/bin"; cp "$BB" "$R/bin/busybox"; chmod +x "$R/bin/busybox"
"$R/bin/busybox" --list-full | while read -r p; do
  mkdir -p "$R/${p%/*}"
  ln -sf /bin/busybox "$R/$p"
done

# 3) runit (статик): init-инфраструктура — PID1
#    rm -f: одноимённые симлинки апплетов (абсолютные -> /bin/busybox) сначала
#    удаляем, иначе cp уходит сквозь них в системный /bin/busybox
mkdir -p "$R/sbin" "$R/usr/bin" "$R/usr/sbin"
for b in runit runit-init runsv runsvdir; do rm -f "$R/sbin/$b"; cp "$RUNIT_CMD/$b" "$R/sbin/"; done
for b in sv svlogd chpst utmpset runsvchdir; do rm -f "$R/usr/bin/$b"; cp "$RUNIT_CMD/$b" "$R/usr/bin/"; done

# 4) /init + runit-дерево (1/2/3) + сервисы
cp "$KB/userland/init" "$R/init"
chmod +x "$R/init"
cp -r "$ETC" "$R/etc"
cp -r "$SVC" "$R/service"
chmod +x "$R"/etc/runit/1 "$R"/etc/runit/2 "$R"/etc/runit/3 "$R"/service/*/run

# 5) initramfs: cpio newc -> gzip
rm -f "$OUT"
( cd "$R" && find . -print0 | cpio --null -o -H newc 2>/dev/null | gzip -9 > "$OUT" )

echo "rootfs : $R ($(du -sh "$R" | cut -f1))"
echo "ramdisk: $OUT ($(du -h "$OUT" | cut -f1))"
ls -l "$R/sbin/runit-init" "$R/sbin/runsvdir"
file "$R/sbin/runit-init" | grep -o 'statically linked'