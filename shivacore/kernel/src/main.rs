// ShivaCore — Kernel-Einstiegspunkt.
// K-Sprint 0: Boot (BIOS+UEFI via `bootloader` 0.11), serielle Debug-Konsole,
// Framebuffer-Textausgabe.
// K-Sprint 1: GDT + TSS (Double-Fault-Stack), IDT (Breakpoint/Double-Fault/
// Page-Fault), PIC-Remapping (0x20-0x2F), Timer+Keyboard-Interrupts aktiv.
// Kein Linux-Unterbau, kein Fremdcode jenseits des minimalen Boot-Protokolls.
#![no_std]
#![feature(abi_x86_interrupt)]
#![no_main]

mod ats1000;
mod framebuffer;
mod gdt;
mod interrupts;
mod serial;

use bootloader_api::{entry_point, BootInfo};
use core::panic::PanicInfo;

entry_point!(kernel_main);

fn kernel_main(boot_info: &'static mut BootInfo) -> ! {
    serial_println!("ShivaCore: Kernel-Einstiegspunkt erreicht.");

    if let Some(fb) = boot_info.framebuffer.as_mut() {
        framebuffer::init(fb);
        println!("ShivaCore Kernel v0.0.2 -- K-Sprint 1");
        println!("Boot: OK | Serial: OK | Framebuffer: OK");
        serial_println!("ShivaCore: Framebuffer-Ausgabe erfolgreich.");
    } else {
        serial_println!("ShivaCore: WARNUNG -- kein Framebuffer vom Bootloader erhalten.");
    }

    gdt::init();
    serial_println!("ShivaCore: GDT + TSS geladen.");

    interrupts::init_idt();
    serial_println!("ShivaCore: IDT geladen.");

    // Breakpoint-Handler live testen -- muss zurueckkehren, kein Crash.
    x86_64::instructions::interrupts::int3();
    serial_println!("ShivaCore: Breakpoint-Test bestanden (int3 zurueckgekehrt).");

    interrupts::init_pics();
    serial_println!("ShivaCore: PICs remapped (0x20-0x2F), Interrupts aktiviert.");

    println!("K-Sprint 1: GDT/IDT/PIC OK");
    serial_println!("ShivaCore: K-Sprint 1 abgeschlossen. Uebergabe an Idle-Loop.");

    loop {
        x86_64::instructions::hlt();
    }
}

#[panic_handler]
fn panic(info: &PanicInfo) -> ! {
    serial_println!("ShivaCore: KERNEL PANIC -- {}", info);
    loop {
        x86_64::instructions::hlt();
    }
}
