#!/usr/bin/env python3
"""Verify PX4 SIH and mixed ArduPilot+PX4 fleet on hivecard."""
import json
import sys
import time

sys.path.insert(0, "/home/uasop/hivecard-web")
import location_manager
import px4_manager
import sitl_fleet

PX4_MODELS = [
    "sihsim_quadx",
    "sihsim_hex",
    "sihsim_standard_vtol",
    "sihsim_rover_ackermann",
]


def assert_px4_installed() -> None:
    if not px4_manager.is_installed():
        print("FAIL: PX4 binary not found")
        sys.exit(1)
    print("OK PX4 installed:", px4_manager.get_version())


def test_px4_models(loc) -> None:
    for model in PX4_MODELS:
        print(f"\n=== PX4 model smoke: {model} ===")
        sitl_fleet.stop_all()
        time.sleep(5)
        info = px4_manager.resolve_px4_model(model=model)
        fleet = sitl_fleet.start_instance(
            vehicle="PX4",
            frame=info["frame"],
            location_id=loc["id"],
            stack="px4",
            px4_model=model,
        )
        if not fleet["instances"]:
            print("FAIL: fleet empty after start for", model)
            print(sitl_fleet.tail_fleet_log("AC01", 30))
            sys.exit(1)
        inst = fleet["instances"][0]
        print(json.dumps({k: inst.get(k) for k in ("id", "stack", "px4_model", "running", "connection_ready", "mavlink_port")}, indent=2))
        if not inst.get("running"):
            print("FAIL: PX4 instance not running for", model)
            print(px4_manager.find_px4_binary())
            print(sitl_fleet.tail_fleet_log(inst["id"], 20))
            sys.exit(1)
        if not inst.get("connection_ready"):
            print("WARN: PX4 not connection_ready yet for", model)
        sitl_fleet.stop_instance(inst["id"])
        time.sleep(2)
        print("OK", model)


def test_px4_location_change() -> None:
    locs = location_manager.list_locations()
    if len(locs) < 2:
        print("SKIP location change test (need 2+ locations)")
        return
    loc_a, loc_b = locs[0], locs[1]
    print(f"\n=== PX4 location: {loc_a['name']} then {loc_b['name']} ===")
    sitl_fleet.stop_all()
    time.sleep(3)

    fleet = sitl_fleet.start_instance(
        "PX4", "quad", location_id=loc_a["id"], stack="px4", px4_model="sihsim_quadx"
    )
    time.sleep(8)
    home_a = px4_manager.px4_home_from_location(loc_a)
    stamp_a = px4_manager.instance_data_dir(0) / "last_home.json"
    if not stamp_a.is_file() or abs(json.loads(stamp_a.read_text())["latitude"] - home_a["lat"]) > 1e-5:
        print("FAIL: first PX4 start did not record expected home")
        print(stamp_a.read_text() if stamp_a.is_file() else "no stamp")
        sys.exit(1)
    sitl_fleet.stop_instance("AC01")
    time.sleep(3)

    fleet = sitl_fleet.start_instance(
        "PX4", "quad", location_id=loc_b["id"], stack="px4", px4_model="sihsim_quadx"
    )
    time.sleep(8)
    home_b = px4_manager.px4_home_from_location(loc_b)
    stamp_b = px4_manager.instance_data_dir(0) / "last_home.json"
    if not stamp_b.is_file() or abs(json.loads(stamp_b.read_text())["latitude"] - home_b["lat"]) > 1e-5:
        print("FAIL: second PX4 start did not record expected home")
        print(stamp_b.read_text() if stamp_b.is_file() else "no stamp")
        sys.exit(1)
    sitl_fleet.stop_all()
    print("OK PX4 location changes applied")


def main() -> None:
    print("=== PX4 install check ===")
    assert_px4_installed()

    print("\n=== Stop all (clean slate) ===")
    sitl_fleet.stop_all()
    time.sleep(2)

    print("\n=== Seed locations ===")
    location_manager.ensure_seeded()
    locs = location_manager.list_locations()
    loc = locs[0]
    print("Using location:", loc["name"])

    test_px4_models(loc)
    test_px4_location_change()

    print("\n=== Mixed fleet: AC01 ArduPilot + AC02 PX4 ===")
    sitl_fleet.stop_all()
    time.sleep(2)
    f1 = sitl_fleet.start_instance("ArduCopter", "quad", location_id=loc["id"], stack="ardupilot")
    time.sleep(10)
    f2 = sitl_fleet.start_instance("PX4", "quad", location_id=loc["id"], stack="px4", px4_model="sihsim_quadx")
    time.sleep(10)
    fleet = sitl_fleet.get_fleet_status()
    print(json.dumps([{k: i.get(k) for k in ("id", "stack", "vehicle", "px4_model", "running", "connection_ready", "mavlink_port")} for i in fleet["instances"]], indent=2))
    if fleet["running_count"] < 2:
        print("FAIL: expected 2 running in mixed fleet")
        sys.exit(1)

    print("\n=== Stop AC01 only (keep PX4) ===")
    f3 = sitl_fleet.stop_instance("AC01")
    remaining = [i["id"] for i in f3["instances"]]
    print("Remaining:", remaining)
    if "AC02" not in remaining:
        print("FAIL: AC02 PX4 should remain running")
        sys.exit(1)

    print("\n=== Stop all ===")
    sitl_fleet.stop_all()
    print("Fleet:", sitl_fleet.get_fleet_status()["running_count"], "running")
    print("\n=== ALL PX4 TESTS PASSED ===")


if __name__ == "__main__":
    main()
