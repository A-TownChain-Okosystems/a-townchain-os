// ShivaCore — Kernel-Einstiegspunkt.
// K-Sprint 0: Boot (BIOS+UEFI via `bootloader` 0.11), serielle Debug-Konsole,
// Framebuffer-Textausgabe. Kein Linux-Unterbau, kein Fremdcode fuer Boot-Logik
// jenseits des minimalen Boot-Protokolls (`bootloader`-Crate).
#![no_std]
#![no_main]

mod serial;
mod framebuffer;
mod ats1000;

use bootloader_api::{entry_point, BootInfo};
use core::panic::PanicInfo;

entry_point!(kernel_main);

fn kernel_main(boot_info: &'static mut BootInfo) -> ! {
    serial_println!("ShivaCore: Kernel-Einstiegspunkt erreicht.");

    if let Some(fb) = boot_info.framebuffer.as_mut() {
        framebuffer::init(fb);
        println!("ShivaCore Kernel v0.0.1 -- K-Sprint 0");
        println!("Boot: OK | Serial: OK | Framebuffer: OK");
        serial_println!("ShivaCore: Framebuffer-Ausgabe erfolgreich.");
    } else {
        serial_println!("ShivaCore: WARNUNG -- kein Framebuffer vom Bootloader erhalten.");
    }

    serial_println!("ShivaCore: Boot vollstaendig. Uebergabe an Idle-Loop.");

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
