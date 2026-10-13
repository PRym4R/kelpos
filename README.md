# kelpOS

Легковесная ОС «под себя»: **обстриженный Linux + свой минимальный userland**.
Без systemd, без udev, без мусора. Принцип suckless: можно выкинуть — выкидываем.

> v2. Раньше был план писать своё ядро — оказалось, что весь нужный софт
> (pipewire, dwm, iwd, PCManFM…) живёт на Linux API, и «клетка» только
> отодвигала бы результат на годы. Теперь мы стрижём ядро конфигом, а всю
> «чистоту» несёт тонкий слой userland'а поверх.

## Что внутри

- **Ядро** — Linux 6.18, обстриженный через Kconfig (`linux/configs/enable.list`):
  вырезаны старые ЦПУ, серверное, лишние ФС, виртуальные гости.
  Осталось: x86_64, ext4, DRM/KMS, сеть (+wifi/bt чипы), ALSA, binfmt_misc,
  devtmpfs, serial, virtio (для QEMU). Без модулей — всё builtin, `bzImage` ~6 МБ.
- **PID 1** — [runit](http://smarden.org/runit/) (никакого systemd). Стадии
  `/etc/runit/{1,2,3}`, сервисы в `/service`, супервизор `runsvdir`.
- **Shell/утилиты** — [busybox](https://busybox.net/) (статика на glibc).
- **Свобода** — doas вместо sudo; минимум привилегий в духе OpenBSD.
- **GUI (план)** — X11 (Xorg) + dwm + dmenu + st. Никакого Wayland и
  кастомных композиторов.

Всё собирается **без root**: QEMU, хост-инструменты и тулчейн раскладываются
`dpkg -x` в проектный `cache/`.

## Статус

- [x] обстриженное ядро 6.18.56 (`bzImage` 6 МБ, 1032 опции `=y`)
- [x] userland: busybox (glibc, статика) + initramfs + живой CLI в QEMU
- [x] runit как PID 1: стадии 1/2/3, сервисы `console`/`syslogd`
- [ ] загрузка «как настоящая ОС»: UEFI + [Limine](https://limine-bootloader.org/)
- [ ] X11, сеть (iwd), звук (pipewire) — см. `TODO.md`

Схема — `docs/architecture.md`. Ближайшие задачи — `NEXT.md`.

## Сборка и запуск

```sh
# 1) ядро (одной командой; хост-инструменты подтянутся сами в cache/)
scripts/build.sh

# 2) userland → userland/initramfs.gz
scripts/mkrootfs.sh

# 3) запуск в QEMU
scripts/qemu-run.sh
```

Требования: Linux x86_64, `gcc`, `make`, `python3`, `cpio`, `gzip`, `curl`.
Пакеты Debian тянутся без root через `dpkg -x` в `cache/`.

## Структура

```
linux/            исходники ядра + мини-конфиг (enable.list)
userland/         /init, шаблоны rootfs, сервисы runit, initramfs
scripts/          сборка ядра, rootfs, QEMU, хост-инструменты
docs/             архитектура
cache/            тулчейн и зависимости (не коммитится)
```

## Железные правила

1. Брать по приоритету, не всё сразу.
2. Suckless: можно выкинуть без потери смысла — выкидываем. Статика, текстовые
   конфиги, никаких монстров.
3. Всё проверяем в QEMU; железо не жжём.
4. Новая фича = пара строк в `enable.list`, а не 200 файлов.

## Лицензия

ISC — см. `LICENSE`. Ядро Linux (GPL-2.0), busybox, runit — под своими лицензиями.
