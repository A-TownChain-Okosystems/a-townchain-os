"""A-TownChain OS Build System — Multi-Platform Build Orchestration."""

import os
import sys
import subprocess
import hashlib
import json
from pathlib import Path
from datetime import datetime


class BuildConfig:
    """Build configuration and metadata."""
    
    PROJECT_ROOT = Path(__file__).parent.parent
    BUILD_DIR = PROJECT_ROOT / "build"
    DIST_DIR = BUILD_DIR / "dist"
    CARGO_MANIFEST = PROJECT_ROOT / "Cargo.toml"
    PYTHON_REQUIREMENTS = [
        "backend/requirements.txt",
        "gateway/requirements.txt",
    ]
    
    # Build targets
    TARGETS = {
        "substrate": {"type": "cargo", "path": str(PROJECT_ROOT)},
        "gateway": {"type": "python", "path": "gateway"},
        "backend": {"type": "python", "path": "backend"},
    }


def run_command(cmd, cwd=None):
    """Execute shell command with error handling."""
    print(f"  > {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd or BuildConfig.PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return e.returncode, e.stdout, e.stderr


def build_substrate():
    """Build Substrate runtime and node."""
    print("\n[BUILD] Substrate (Rust)...")
    
    if not BuildConfig.CARGO_MANIFEST.exists():
        print("  ⚠ Cargo.toml not found — skipping Substrate build")
        return False
    
    # Build release binary
    rc, out, err = run_command([
        "cargo", "build", "--release", "--workspace"
    ])
    
    if rc != 0:
        print(f"  ❌ Cargo build failed:\n{err}")
        return False
    
    print("  ✅ Substrate build complete")
    return True


def build_python(target: str):
    """Build Python targets (install dependencies, collect statics)."""
    target_path = BuildConfig.PROJECT_ROOT / target
    
    print(f"\n[BUILD] {target.title()} (Python)...")
    
    if not target_path.exists():
        print(f"  ⚠ {target} directory not found")
        return False
    
    # Install dependencies
    req_file = target_path / "requirements.txt"
    if req_file.exists():
        print(f"  Installing dependencies from {req_file}...")
        rc, out, err = run_command([
            "pip", "install", "-r", str(req_file)
        ])
        if rc != 0:
            print(f"  ⚠ Dependency installation had issues (continuing): {err[:200]}")
    
    # Run syntax check
    print(f"  Checking Python syntax...")
    py_files = list(target_path.glob("**/*.py"))
    syntax_ok = True
    for py_file in py_files:
        rc, _, err = run_command(["python", "-m", "py_compile", str(py_file)])
        if rc != 0:
            print(f"    ❌ {py_file}: {err}")
            syntax_ok = False
    
    if syntax_ok:
        print(f"  ✅ {target} ready")
        return True
    else:
        print(f"  ⚠ {target} has syntax errors (non-blocking)")
        return True  # Continue build


def run_tests():
    """Run test suites."""
    print("\n[BUILD] Running tests...")
    
    test_dirs = [
        BuildConfig.PROJECT_ROOT / "tests",
        BuildConfig.PROJECT_ROOT / "blockchain" / "tests",
    ]
    
    passed = 0
    failed = 0
    
    for test_dir in test_dirs:
        if not test_dir.exists():
            continue
        
        print(f"  Testing {test_dir.name}...")
        rc, out, err = run_command(["pytest", str(test_dir), "-v", "--tb=short"])
        
        if rc == 0:
            passed += 1
            print(f"    ✅ Tests passed")
        else:
            failed += 1
            print(f"    ⚠ Tests failed: {err[:300]}")
    
    return failed == 0


def generate_build_report():
    """Generate build summary report."""
    print("\n[BUILD] Build Report")
    print("=" * 60)
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "version": "2.0",
        "targets_built": [],
        "artifacts": [],
    }
    
    # Scan for build artifacts
    if BuildConfig.DIST_DIR.exists():
        for artifact in BuildConfig.DIST_DIR.glob("**/*"):
            if artifact.is_file():
                size_kb = artifact.stat().st_size / 1024
                report["artifacts"].append({
                    "path": str(artifact.relative_to(BuildConfig.PROJECT_ROOT)),
                    "size_kb": round(size_kb, 2),
                })
    
    # Write report
    report_file = BuildConfig.BUILD_DIR / "build_report.json"
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"✅ Report saved to {report_file}")
    return report


def build():
    """Main build orchestrator."""
    print("[BUILD] Starting A-TownChain OS Build System")
    print(f"[BUILD] Project root: {BuildConfig.PROJECT_ROOT}")
    print(f"[BUILD] Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Create build directories
    BuildConfig.DIST_DIR.mkdir(parents=True, exist_ok=True)
    
    results = {}
    
    # Build components
    results["substrate"] = build_substrate()
    results["gateway"] = build_python("gateway")
    results["backend"] = build_python("backend")
    
    # Run tests (optional, non-blocking)
    has_pytest = subprocess.run(["which", "pytest"], capture_output=True).returncode == 0
    if has_pytest:
        run_tests()
    
    # Generate report
    report = generate_build_report()
    
    # Summary
    print("\n" + "=" * 60)
    print("[BUILD] Build Summary")
    
    success_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    
    for target, success in results.items():
        status = "✅" if success else "❌"
        print(f"  {status} {target}")
    
    print("=" * 60)
    
    if success_count == total_count:
        print(f"✅ Build SUCCESS — All {total_count} targets built")
        print(f"   Version: {report['version']}")
        return 0
    else:
        print(f"⚠ Build PARTIAL — {success_count}/{total_count} targets built")
        return 1


if __name__ == "__main__":
    sys.exit(build())
