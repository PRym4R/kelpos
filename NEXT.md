# NEXT — рабочий todo (внутренний трекер)

Текущий фокус: P0, загрузка «как настоящая ОС» (UEFI + Limine).

- [ ] P0 · Ядро: EFI_STUB (EFI/EFI_STUB) в `linux/configs/enable.list` + пересборка
- [ ] P0 · OVMF-прошивка из Debian (`dpkg -x`)
- [ ] P0 · Limine собрать из исходников
- [ ] P0 · Диск: GPT + ESP(FAT) + root ext4 + rootfs
- [ ] P0 · `limine.cfg` + загрузка EFI в QEMU
