//! ShivaCore Kernel — Library Crate für Test-Ausführung
//!
//! Re-exportiert alle Kernel-Module für Unit- und Integrationstests.
#![cfg_attr(not(test), no_std)]
#![feature(abi_x86_interrupt)]
#![allow(dead_code)]
#![allow(unused_imports)]
#![allow(unused_variables)]
#![allow(unused_mut)]

#[cfg(test)]
extern crate std;

extern crate alloc;

pub mod allocator;
pub mod ats1000;
pub mod framebuffer;
pub mod gdt;
pub mod interrupts;
pub mod memory;
pub mod serial;
pub mod capability;
pub mod process;
pub mod scheduler;
pub mod ipc;
pub mod did;
pub mod remote_caps;
pub mod knowledge_graph;
pub mod memory_manager;
pub mod atcfs;
pub mod vfs;
pub mod syscall;
pub mod timer;
pub mod block;
pub mod net;
pub mod tcpip;
pub mod p2p;
pub mod security;
pub mod consensus;
pub mod mempool;
pub mod blockchain;
pub mod vm;
pub mod contract;
pub mod ai;
pub mod kernel_init;
pub mod cross_subsystem;
pub mod atcnet;
pub mod genesis;
pub mod genesis_bridge;
pub mod gossip_bridge;
pub mod security_audit;
pub mod userspace;
pub mod elf_loader;
pub mod page_fault;
pub mod user_sched;
pub mod user_io;
pub mod hw_drivers;
pub mod system;
pub mod sockets;
pub mod devfs;
pub mod threads;
pub mod power;
pub mod container;
pub mod signals;
pub mod smp;
pub mod vmm;
pub mod cow;
pub mod tracing;
pub mod container_net;
pub mod lkm;
pub mod module_security;
pub mod fs_journal;
