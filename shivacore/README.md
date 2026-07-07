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


## Status: K-Sprint 1 abgeschlossen (07.07.2026)

GDT + TSS (dedizierter Double-Fault-Stack via IST), IDT mit Breakpoint-/
Double-Fault-/Page-Fault-Handlern, PIC-Remapping (8259 von 0x08-0x0F auf
0x20-0x2F), Timer- + Keyboard-Interrupts aktiv. QEMU-verifiziert: Breakpoint
(`int3`) kehrt sauber zurueck, kein Crash, Idle-Loop laeuft weiter.

**Gefixter Bug:** Erster Testlauf loeste einen Double Fault direkt nach dem
Breakpoint-Handler aus. Ursache: nach dem Laden des eigenen (minimalen) GDT
zeigte der alte Stack-Segment-Selektor (SS, vom Bootloader-GDT) ins Leere.
Bei der IRETQ-Rueckkehr aus dem Interrupt wird SS zwingend neu geladen und
validiert -> #GP waehrend IRETQ -> vom Prozessor als Double Fault eskaliert.
Fix: SS nach dem GDT-Laden explizit auf den Null-Selektor setzen (in
Long-Mode bei CPL0 fuer das Stack-Segment zulaessig, da Flat-Memory-Modell).

## Nächster Schritt: K-Sprint 2

Speicherverwaltung — Paging (aktuelle Page-Tables auslesen/verstehen), Heap-
Allokator (`#[global_allocator]`), damit `alloc`/`Box`/`Vec` nutzbar werden.


## Status: K-Sprint 2 abgeschlossen (07.07.2026)

Paging-Mapper (`OffsetPageTable` über das vom Bootloader linear gemappte
physische RAM), einfacher `BootInfoFrameAllocator` (iteriert die vom
Bootloader gemeldete `MemoryRegions`-Karte nach freien 4-KiB-Frames), Heap
(100 KiB, `linked_list_allocator`). `alloc` (Box/Vec/String) ist jetzt im
Kernel nutzbar. QEMU-verifiziert: `Box::new(41)` und `Vec` mit Summe 0..10=45
funktionieren fehlerfrei, kein Crash.

Voraussetzung war eine `BootloaderConfig` mit `mappings.physical_memory =
Some(Mapping::Dynamic)`, eingebettet via `entry_point!(kernel_main, config =
&BOOTLOADER_CONFIG)` in `main.rs`.

## Nächster Schritt: K-Sprint 3

Multitasking — Prozess-/Task-Struktur, einfacher Scheduler, Context-Switch.
