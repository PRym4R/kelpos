#!/usr/bin/env python3
"""Вытаскивает qemu-system-x86 + все зависимости в префикс без root.

Читает индексы Debian (main/binary-amd64 + binary-all), скачивает .deb
и распаковывает `dpkg -x` в общий корень. Уже установленные в системе
пакеты пропускает. Рут не нужен (никакой установки в систему).
"""
import gzip
import os
import re
import subprocess
import urllib.request

DIST = "http://deb.debian.org/debian"
SUITE = "trixie"
KB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_DIR = os.path.join(KB, "cache", "debs")
ROOT = os.path.join(KB, "cache", "pqemu")
CACHE = os.path.join(KB, "cache")

# локальные индексы: cache/debs/P (amd64) и cache/debs/Pall (all)
SPECS = [
    (os.path.join(INDEX_DIR, "P"), "amd64"),
    (os.path.join(INDEX_DIR, "Pall"), "all"),
]

if not os.path.exists(SPECS[0][0]) or not os.path.exists(SPECS[1][0]):
    os.makedirs(INDEX_DIR, exist_ok=True)
    print("индексов нет — качаю Packages.gz из Debian", SUITE)
    for idx_path, arch in SPECS:
        url = f"{DIST}/dists/{SUITE}/main/binary-{arch}/Packages.gz"
        with urllib.request.urlopen(url) as r:
            data = gzip.decompress(r.read())
        with open(idx_path, "wb") as f:
            f.write(data)

queue = ["qemu-system-x86"]
seen = set()


def parse_index(path):
    """Package-name -> {Version, Depends, Filename}"""
    pkgs = {}
    cur = None
    with open(path) as f:
        for line in f:
            line = line.rstrip("\n")
            if line == "":
                cur = None
                continue
            if line[0] != " " and ":" in line:
                key, _, val = line.partition(":")
                val = val.strip()
                if key == "Package":
                    cur = val
                    pkgs.setdefault(cur, {})
                elif cur is not None:
                    pkgs[cur][key] = val
    return pkgs


IDX = {}
for path, _arch in SPECS:
    for name, info in parse_index(path).items():
        IDX.setdefault(name, {}).update(info)


def dpkg_installed(name):
    r = subprocess.run(["dpkg", "-s", name], capture_output=True, text=True)
    return r.returncode == 0


def fetch(url, dest):
    if os.path.exists(dest):
        return
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    print("  dl", url.split("/")[-1])
    urllib.request.urlretrieve(url, dest)


def main():
    os.makedirs(ROOT, exist_ok=True)
    n = 0
    while queue:
        name = queue.pop(0)
        if name in seen:
            continue
        seen.add(name)
        info = IDX.get(name)
        if not info:
            print(f"!! {name}: нет в индексе (виртуальный/необязательный) — пропуск")
            continue
        if dpkg_installed(name):
            print(f"== {name}: уже в системе")
            continue
        fn = info.get("Filename")
        if not fn:
            print(f"!! {name}: нет Filename")
            continue
        deb = os.path.join(ROOT, name + ".deb")
        fetch(DIST + "/" + fn, deb)
        subprocess.run(["dpkg", "-x", deb, ROOT], check=True)
        n += 1
        print(f"== {name} {info.get('Version','')} — распакован")
        deps = (info.get("Depends") or "").split(",")
        for d in deps:
            if not d.strip():
                continue
            alt = d.split("|")[0].strip()
            alt = re.sub(r"\s*\[[^\]]*\]", "", alt)
            alt = re.sub(r"\s*\([^)]*\)", "", alt).strip()
            if alt and alt not in seen:
                queue.append(alt)
    link_firmware()
    print(f"готово: {n} пакетов распаковано в {ROOT}")


def link_firmware():
    """QEMU ищет BIOS (seabios/ipxe) в своём datadir (share/qemu) — соберём симлинки.
    Ссылки относительные, чтобы жить при переносе/переименовании проекта."""
    dd = os.path.join(ROOT, "usr", "share", "qemu")
    os.makedirs(dd, exist_ok=True)
    for d in ("seabios", "ipxe"):
        src_dir = os.path.join(ROOT, "usr", "share", d)
        if not os.path.isdir(src_dir):
            continue
        for f in os.listdir(src_dir):
            dst = os.path.join(dd, f)
            if os.path.islink(dst) or os.path.exists(dst):
                os.remove(dst)
            os.symlink(os.path.relpath(os.path.join(src_dir, f), dd), dst)


if __name__ == "__main__":
    main()