#!/bin/sh
# Сборка минимального конфига kelpOS из enable.list.
# База: allnoconfig (всё off) → включить наш keep-list → olddefconfig (закрыть депы).
set -e
cd "$(dirname "$0")/../linux/src"

make ARCH=x86_64 allnoconfig >/dev/null

while read -r line; do
    case "$line" in
        ''|\#*) continue ;;
    esac
    sym="${line%%=*}"
    val="${line#*=}"
    case "$line" in
        *=n)
            ./scripts/config -d "$sym" ;;
        *=*)
            ./scripts/config --set-val "$sym" "$val" ;;
        *)
            ./scripts/config -e "$sym" ;;
    esac
done < ../configs/enable.list

make ARCH=x86_64 olddefconfig >/dev/null

echo "=== kelpOS.config: $(wc -l < .config) строк, enabled: $(grep -c '^CONFIG_.*=y' .config)"