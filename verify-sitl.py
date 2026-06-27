#!/usr/bin/env python3
import json
import subprocess
import sys
sys.path.insert(0, "/home/uasop/hivecard-web")
import sitl_manager as s

bin_dir = s.BUILD_BIN_DIR
print("=== SITL binaries ===")
for p in sorted(bin_dir.iterdir()):
    if p.is_file():
        print(p.name, p.stat().st_size)

print("\n=== Simulatable vehicles ===")
vehicles = [v["vehicle"] for v in s.list_simulatable_vehicles()]
print(json.dumps(vehicles, indent=2))

print("\n=== Buildable (should be empty) ===")
print(json.dumps(s.list_buildable_vehicles(), indent=2))

print("\n=== Binary smoke test (--help) ===")
for name in sorted(p.name for p in bin_dir.iterdir() if p.is_file()):
    r = subprocess.run([str(bin_dir / name), "--help"], capture_output=True, text=True, timeout=5)
    ok = r.returncode in (0, 1) or "Usage" in (r.stdout + r.stderr)
    print(f"{name}: {'OK' if ok else 'FAIL'} (rc={r.returncode})")

print("\n=== SITL status ===")
print(json.dumps({k: s.get_status()[k] for k in ("running", "vehicle", "connection_status")}, indent=2))
