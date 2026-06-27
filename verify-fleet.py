#!/usr/bin/env python3
"""Verify multi-SITL fleet on hivecard."""
import json
import sys
import time

sys.path.insert(0, "/home/uasop/hivecard-web")
import location_manager
import sitl_fleet

print("=== Stop all (clean slate) ===")
sitl_fleet.stop_all()
time.sleep(2)

print("=== Seed locations ===")
location_manager.ensure_seeded()
locs = location_manager.list_locations()
print(f"Locations: {len(locs)}")
loc_a = locs[0]
loc_b = locs[1] if len(locs) > 1 else loc_a
print(f"  A: {loc_a['name']}")
print(f"  B: {loc_b['name']}")

print("\n=== Start AC01 ArduCopter/quad at", loc_a['name'], "===")
try:
    f1 = sitl_fleet.start_instance("ArduCopter", "quad", location_id=loc_a["id"])
    print(json.dumps([{k: i.get(k) for k in ("id","vehicle","mavlink_port","location_name","running","connection_ready")} for i in f1["instances"]], indent=2))
except Exception as e:
    print("FAIL:", e)
    sys.exit(1)

time.sleep(8)

print("\n=== Start AC02 Rover/rover at", loc_b['name'], "===")
try:
    f2 = sitl_fleet.start_instance("Rover", "rover", location_id=loc_b["id"])
    print(json.dumps([{k: i.get(k) for k in ("id","vehicle","mavlink_port","location_name","running","connection_ready")} for i in f2["instances"]], indent=2))
except Exception as e:
    print("FAIL:", e)
    sys.exit(1)

if f2["running_count"] < 2:
    print("WARN: expected 2 running, got", f2["running_count"])

time.sleep(5)

print("\n=== Start AC03 ArduPlane/plane ===")
try:
    f2b = sitl_fleet.start_instance("ArduPlane", "plane", location_id=loc_a["id"])
    print("Running:", f2b["running_count"])
except Exception as e:
    print("FAIL AC03:", e)
    sys.exit(1)

time.sleep(5)

print("\n=== Try 4th aircraft (should fail) ===")
try:
    sitl_fleet.start_instance("ArduSub", "vectored")
    print("FAIL: should have rejected 4th start")
    sys.exit(1)
except RuntimeError as e:
    print("OK rejected:", e)

print("\n=== Stop AC01 only ===")
f3 = sitl_fleet.stop_instance("AC01")
remaining = [i["id"] for i in f3["instances"]]
print("Remaining:", remaining)
if not any(i["id"] == "AC02" for i in f3["instances"]):
    print("FAIL: AC02 should still be running")
    sys.exit(1)
print("OK AC02 still running")

print("\n=== Stop all ===")
sitl_fleet.stop_all()
print("Fleet:", sitl_fleet.get_fleet_status()["running_count"], "running")
print("\n=== ALL TESTS PASSED ===")
