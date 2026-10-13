#!/usr/bin/env python3
"""Вытаскивает хост-инструменты сборки ядра в префикс без root.

Нужны для `make bzImage`: m4/bison/flex (генерация Kconfig) и libelf-dev
(objtool) + libssl-dev (extract-cert). Рут не нужен — только `dpkg -x` в
проектный cache/hosttools.
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
ROOT = os.path.join(KB, "cache", "hosttools")

SPECS = [os.path.join(INDEX_DIR, "P"), os.path.join(INDEX_DIR, "Pall")]

if not all(os.path.exists(p) for p in SPECS):
    os.makedirs(INDEX_DIR, exist_ok=True)
    print("индексов нет — качаю Packages.gz из Debian", SUITE)
    for idx_path, arch in zip(SPECS, ("amd64", "all")):
        url = f"{DIST}/dists/{SUITE}/main/binary-{arch}/Packages.gz"
        with urllib.request.urlopen(url) as r:
            data = gzip.decompress(r.read())
        with open(idx_path, "wb") as f:
            f.write(data)

queue = ["bison", "flex", "m4", "libelf-dev", "libssl-dev"]
seen = set()


def parse_index(path):
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
for path in SPECS:
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
        if not info or not info.get("Filename"):
            print(f"!! {name}: нет в индексе — пропуск")
            continue
        if dpkg_installed(name):
            print(f"== {name}: уже в системе")
            continue
        deb = os.path.join(ROOT, name + ".deb")
        fetch(DIST + "/" + info["Filename"], deb)
        subprocess.run(["dpkg", "-x", deb, ROOT], check=True)
        os.remove(deb)
        n += 1
        print(f"== {name} {info.get('Version','')} — распакован")
        for d in (info.get("Depends") or "").split(","):
            alt = d.split("|")[0].strip()
            alt = re.sub(r"\s*\[[^\]]*\]", "", alt)
            alt = re.sub(r"\s*\([^)]*\)", "", alt).strip()
            if alt and alt not in seen:
                queue.append(alt)
    print(f"готово: {n} пакетов в {ROOT}")


if __name__ == "__main__":
    main()
