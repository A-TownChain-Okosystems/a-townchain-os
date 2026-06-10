"""
Build System — Issue #7 (EXE / AppImage Installer)
Baut A-TownChain OS als ausführbare Binärdatei.
Unterstützt: Linux AppImage, Windows EXE, macOS .app, Docker Image.
"""
import subprocess, sys, os, shutil, platform, json, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BUILD_CONFIG = {
    "name":        "A-TownChain OS",
    "version":     "2.0.0",
    "entry_point": "start.py",
    "icon":        "frontend/assets/icon.png",
    "description": "A-TownChain Blockchain OS",
    "author":      "A-TownChain-Okosystems",
}

def run(cmd, cwd=None):
    print(f"  $ {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd or ROOT,
                             capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ⚠️ {result.stderr[:200]}")
    return result.returncode == 0

def build_docker():
    """Docker Image bauen."""
    print("\n🐳 Docker Image bauen...")
    tag = f"atcchain/a-townchain-os:{BUILD_CONFIG['version']}"
    ok = run(f"docker build -t {tag} -f docker/Dockerfile.node .")
    if ok:
        print(f"  ✅ Image: {tag}")
        run(f"docker tag {tag} atcchain/a-townchain-os:latest")
    return ok

def build_linux_appimage():
    """Linux AppImage mit PyInstaller."""
    print("\n🐧 Linux AppImage bauen...")
    if not shutil.which("pyinstaller"):
        run("pip install pyinstaller --quiet")
    spec = f"""
# -*- mode: python -*-
a = Analysis(['{ROOT}/start.py'],
             pathex=['{ROOT}'],
             binaries=[],
             datas=[
               ('{ROOT}/frontend', 'frontend'),
               ('{ROOT}/config', 'config'),
             ],
             hiddenimports=['flask','cryptography','web3'],
             hookspath=[],)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas,
          name='{BUILD_CONFIG["name"].replace(" ","-")}',
          debug=False, bootloader_ignore_signals=False,
          strip=False, upx=True, console=True,
          icon=None)
"""
    spec_path = os.path.join(ROOT, "build", "atc.spec")
    os.makedirs(os.path.join(ROOT, "build"), exist_ok=True)
    with open(spec_path, "w") as f: f.write(spec)
    ok = run(f"pyinstaller --distpath build/dist --workpath build/work {spec_path}")
    if ok: print(f"  ✅ Build: build/dist/A-TownChain-OS")
    return ok

def build_windows_exe():
    """Windows EXE (nur auf Windows oder mit Wine)."""
    print("\n🪟 Windows EXE bauen...")
    if platform.system() != "Windows" and not shutil.which("wine"):
        print("  ⚠️ Nur auf Windows oder mit Wine möglich")
        return False
    return build_linux_appimage()  # PyInstaller auf Windows

def build_deb():
    """Debian/Ubuntu .deb Paket."""
    print("\n📦 .deb Paket bauen...")
    deb_dir = os.path.join(ROOT, "build", "deb")
    os.makedirs(f"{deb_dir}/DEBIAN", exist_ok=True)
    os.makedirs(f"{deb_dir}/usr/bin", exist_ok=True)
    os.makedirs(f"{deb_dir}/usr/share/atcchain", exist_ok=True)
    control = f"""Package: a-townchain-os
Version: {BUILD_CONFIG['version']}
Section: net
Priority: optional
Architecture: amd64
Depends: python3 (>= 3.10), python3-pip, docker.io
Maintainer: A-TownChain-Okosystems <dev@atownchain.io>
Description: {BUILD_CONFIG['description']}
"""
    with open(f"{deb_dir}/DEBIAN/control", "w") as f: f.write(control)
    launcher = f"""#!/bin/bash
cd /usr/share/atcchain && python3 start.py "$@"
"""
    with open(f"{deb_dir}/usr/bin/atcchain", "w") as f: f.write(launcher)
    run(f"chmod +x {deb_dir}/usr/bin/atcchain")
    ok = run(f"dpkg-deb --build {deb_dir} build/a-townchain-os_{BUILD_CONFIG['version']}_amd64.deb")
    if ok: print(f"  ✅ .deb: build/a-townchain-os_{BUILD_CONFIG['version']}_amd64.deb")
    return ok

def main():
    import argparse
    parser = argparse.ArgumentParser(description="A-TownChain OS Build System")
    parser.add_argument("target", choices=["docker","linux","windows","deb","all"],
                         help="Build-Ziel")
    args = parser.parse_args()

    print(f"🔨 A-TownChain OS Build System v{BUILD_CONFIG['version']}")
    print(f"   Ziel: {args.target}\n")
    t0 = time.time()

    results = {}
    if args.target in ("docker","all"):  results["docker"]   = build_docker()
    if args.target in ("linux","all"):   results["linux"]    = build_linux_appimage()
    if args.target in ("windows","all"): results["windows"]  = build_windows_exe()
    if args.target in ("deb","all"):     results["deb"]      = build_deb()

    print(f"\n{'='*50}")
    print(f"Build-Summary ({round(time.time()-t0,1)}s):")
    for t, ok in results.items():
        print(f"  {'✅' if ok else '❌'} {t}")
    sys.exit(0 if all(results.values()) else 1)

if __name__ == "__main__": main()
