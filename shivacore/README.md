# ShivaCore — Bare-Metal Kernel (K-Sprint 0 ✅)

Eigener Kernel von Grund auf in Rust (`no_std`, `x86_64-unknown-none`) — kein
Linux-Unterbau, kein Fremdcode ausser dem minimalen Boot-Protokoll
(`bootloader` 0.11 Crate). Teil des GlobusOS-Betriebssystems
(GlobusOS = OS gesamt, ShivaCore = nur der Kernel darin).

## Status: K-Sprint 0 abgeschlossen (07.07.2026)

Verifiziert per QEMU-Boot-Test (BIOS-Image):
- ✅ Kernel-ELF wird vom Bootloader korrekt geladen und Entry-Point erreicht
- ✅ Serielle Debug-Konsole funktioniert (`serial_println!` via UART 16550)
- ✅ Framebuffer-Textausgabe funktioniert (Pixel-Modus, nicht klassisches VGA-Text)
- ✅ Kein Hang, sauberer Übergang in Idle-Loop (`hlt`)

**Vorheriges Problem (05.-06.07.) war ein Diagnose-Irrtum, kein echter Bug:**
Frühere Sessions vermuteten einen Hang zwischen Bootloader und Kernel wegen
leerem Serial-Log. Root-Cause-Analyse (07.07.) mit einem minimalen
Raw-Serial-Diagnose-Kernel (direkter Port-Write vor jeglicher Initialisierung)
zeigte: der Kernel wurde immer schon erreicht und konnte schreiben. Der
vollständige Kernel (inkl. `lazy_static`-Serial-Init und Framebuffer-Init)
bootet bei erneutem Test einwandfrei durch — vermutlich war das leere Log in
früheren Sessions ein Artefakt eines fehlgeschlagenen/falsch konfigurierten
Testlaufs, kein Kernel-Bug.

## Bauen

```bash
cd kernel && cargo build --release
cd ../boot && cargo run --release -- \
  ../kernel/target/x86_64-unknown-none/release/shivacore \
  ../images
```

Erzeugt `images/shivacore-bios.img` und `images/shivacore-uefi.img`.

## Testen (QEMU)

```bash
qemu-system-x86_64 -drive format=raw,file=images/shivacore-bios.img \
  -serial stdio -display none -no-reboot
```

Erwartete Ausgabe:
```
ShivaCore: Kernel-Einstiegspunkt erreicht.
ShivaCore: Framebuffer-Ausgabe erfolgreich.
ShivaCore: Boot vollstaendig. Uebergabe an Idle-Loop.
```

## Nächster Schritt: K-Sprint 1

CPU-Grundlagen — GDT, IDT, Interrupt-Handler (Breakpoint, Double-Fault, Page-Fault),
PIC-Remapping. Baut direkt auf diesem Kernel auf (`kernel/src/main.rs`).

## Struktur

- `kernel/` — der eigentliche bare-metal Kernel-Crate (kompiliert zu ELF, läuft ring 0)
- `boot/` — Host-Tool, das aus dem Kernel-ELF bootfähige BIOS/UEFI-Images baut
  (nutzt `bootloader::BiosBoot`/`UefiBoot`, läuft NICHT im Kernel-Kontext)
