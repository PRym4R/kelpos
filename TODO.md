# TODO — kelpOS (v2: обстриженный Linux)

Брать по приоритету. PE/нативный Windows-загрузчик — в самом конце.
Ядро больше НЕ пишем сами — стрижём конфигом (см. `linux/configs/enable.list`).

Легенда: [ ] не начато · [x] готово · [~] в работе

---

## Фаза 0 — окружение и обстриженное ядро (P0)

- [x] пивот на обстриженный Linux (v2)
- [x] локальные билд-инструменты: m4 1.4.19, bison 3.8.2, flex 2.6.4
  (без root; libelf + openssl-хэдеры подтянуты из .deb через dpkg -x)
- [x] исходники ядра 6.18.56 в `linux/src`
- [x] мини-конфиг `linux/configs/enable.list` + `scripts/mkconfig.sh`
- [x] первая сборка: `bzImage` 6.0 МБ, 1032 опции =y / 1563 выключено,
      без MODULES (всё builtin), DRM·ext4·binfmt_misc·cfg80211 на месте
- [x] QEMU в префикс без root: `scripts/setup-qemu.py` (dpkg -x + деревья
      зависимостей), `scripts/qemu-run.sh`
- [x] **живой boot-тест**: ядро грузится в QEMU, serial-консоль, bochs-drm,
      bluetooth-core, cfg80211, ext4 — паника «VFS: Unable to mount root» (это
      норма: rootfs ещё нет)
- [x] **rootfs + initramfs + живой CLI**: busybox 1.38.0 статик, при boot:
      hostname kelp, /proc /sys /dev (devtmpfs) /dev/pts /run смонтированы,
      poweroff отрабатывает. (Поймали отсутствие BINFMT_SCRIPT → ENOEXEC)
- [x] **runit как init (PID 1)**: стадии /etc/runit/{1,2,3}, runsvdir,
      сервисы console/syslogd up, обе должности живы, чистый poweroff
- [x] **пивот: musl → glibc** (дефолтный хост-GCC). Сборка статик на glibc:
      busybox 2.3M, runit 680–900K/бинарь, утоптано chpst/utmpset-патчами
      (grp.h для setgroups, ut_tv вместо 32-bит ut_time); initramfs 4.1M
- [ ] Limine + загрузка «как настоящая ОС» (UEFI), CLI рабочий
- [ ] отладка сериалом из коробки (уже на месте)

## Фаза 1 — пользовательское окружение (P1)

- [ ] базовый набор своих утилит на glibc (suckless-coutil-набор; musl отменён)
- [x] runit как init (PID 1, никаких systemd) — см. P0
- [ ] ash-style shell
- [ ] doas (вместо sudo), права, пользователи
- [ ] ext4 на виртуальном диске в QEMU; fstab по минимуму
- [ ] devtmpfs /dev (без udev) — проверка
- [ ] FIFO/socket работают, tmux поднимет devpts

## Фаза 2 — графика (P2)

- [ ] DRM/KMS отдаёт framebuffer (bochs/simpledrm/virtio-gpu)
- [ ] **X11 как display server** (Xorg, без Wayland) — кастомный DS отменён
- [ ] fontconfig + Xft для рендера шрифтов
- [ ] dmenu
- [ ] st (нативный X11)
- [ ] dwm (нативный X11)

## Фаза 3 — сеть и твой путь (P3)

- [ ] iwd как сетевой демон (nl80211 есть в keep-list)
- [ ] wifi-чипы: Intel/Realtek/Broadcom/ATH — проверить на QEMU не выйдет,
      тест на железе позже
- [ ] bluetooth (btusb/btuart в keep-list) — нужен firmware-пакет
- [ ] ethernet в QEMU (virtio-net / e1000e) — dhcp

## Фаза 4 — звук без мусора (P4)

- [ ] голый pipewire core (без pulse/jack)
- [ ] wireplumber как микшер
- [ ] ALSA-драйверы из keep-list (AC97 в QEMU, HDA на железе)

## Фаза 5 — приложения по списку (P5)

- [ ] tmux (терминальный мультиплексор)
- [ ] nsxiv — просмотрщик
- [ ] PCManFM (GTK-зависимый — обсудим suckless-цену)

## Фаза 6 — Windows: .exe через binfmt_misc (P6)

- [ ] binfmt_misc зарегистрирован для PE
- [ ] Wine как хэндлер → запуск .exe
- [ ] правила: только наши форматы, никакой винды-свалки

## Фаза 7 — нативный PE-загрузчик (P7, мечта/самый конец)

- [ ] исследование нативного PE-loader (становится реально только после всего)
- [ ] изолированная NT-подсистема (минимум)
- [ ] Win32 целиком НЕ тащим

---

## Сквозное

- [ ] песочница в духе pledge/unveil там, где реально нужно
- [ ] замеры лёгкости: размер bzImage, RAM, время до рабочего стола
- [ ] ревизия «выкинь лишнее» после каждой фазы (и из конфига тоже)
- [ ] финальный чек: что из дерева ядра реально не собирается (95%)
- [ ] вернуть spectre-митигаторы (RETPOLINE/IBT/RETHUNK) — сейчас выключены,
      т.к. objtool тянет libelf, которого нет при корне без root; на реальном
      железе включить, libelf у нас в префиксе уже есть