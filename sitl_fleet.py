#!/usr/bin/env python3
"""Multi-aircraft SITL fleet manager (max 3 concurrent instances)."""

from __future__ import annotations

import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

import location_manager
import px4_manager as px4
import sitl_manager as sm

MAX_INSTANCES = 3
STACK_ARDUPILOT = "ardupilot"
STACK_PX4 = "px4"

SLOT_TABLE = [
    {
        "id": "AC01",
        "slot": 0,
        "mav_sysid": 1,
        "sitl_tcp_port": 5760,
        "mavlink_port": 14550,
        "screen": "sitl-ac01",
    },
    {
        "id": "AC02",
        "slot": 1,
        "mav_sysid": 2,
        "sitl_tcp_port": 5770,
        "mavlink_port": 14551,
        "screen": "sitl-ac02",
    },
    {
        "id": "AC03",
        "slot": 2,
        "mav_sysid": 3,
        "sitl_tcp_port": 5780,
        "mavlink_port": 14552,
        "screen": "sitl-ac03",
    },
]

FLEET_PATH = Path.home() / ".hivecard" / "sitl_fleet.json"
FLEET_PATH.parent.mkdir(parents=True, exist_ok=True)


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _slot_by_id(aircraft_id: str) -> dict | None:
    for slot in SLOT_TABLE:
        if slot["id"] == aircraft_id:
            return slot
    return None


def _load_fleet() -> dict:
    if FLEET_PATH.exists():
        with open(FLEET_PATH) as f:
            data = json.load(f)
        if isinstance(data, dict) and "instances" in data:
            return data
    return {"instances": []}


def _save_fleet(data: dict) -> None:
    with open(FLEET_PATH, "w") as f:
        json.dump(data, f, indent=2)


def _migrate_legacy_state() -> None:
    if FLEET_PATH.exists():
        return
    if not sm.STATE_PATH.exists():
        _save_fleet({"instances": []})
        return
    legacy = sm.load_state()
    instances = []
    if legacy.get("running") or legacy.get("vehicle"):
        instances.append(
            {
                "id": "AC01",
                "stack": STACK_ARDUPILOT,
                "vehicle": legacy.get("vehicle", "ArduCopter"),
                "frame": legacy.get("frame", "quad"),
                "mav_sysid": 1,
                "sitl_tcp_port": 5760,
                "mavlink_port": 14550,
                "slot": 0,
                "screen": "sitl-ac01",
                "location": location_manager.get_default_location(),
                "display_name": f"{legacy.get('frame', 'quad').upper().replace('-', '_')}_01",
                "speedup": legacy.get("speedup", 1),
                "running": False,
                "started_at": None,
            }
        )
    _save_fleet({"instances": instances})


def _screen_running(screen: str) -> bool:
    try:
        out = subprocess.check_output(
            ["/usr/bin/screen", "-ls", screen], stderr=subprocess.STDOUT, text=True
        )
        return f".{screen}\t" in out or f".{screen} " in out
    except (subprocess.CalledProcessError, OSError):
        return False


def _instance_process_running(instance: dict) -> bool:
    stack = instance.get("stack", STACK_ARDUPILOT)
    if stack == STACK_PX4:
        return px4.instance_running(instance["slot"], instance["mavlink_port"])
    if _screen_running(instance["screen"]):
        return True
    tcp = instance["sitl_tcp_port"]
    try:
        out = subprocess.check_output(["ss", "-tln"], text=True)
        return any(f":{tcp}" in line and "LISTEN" in line for line in out.splitlines())
    except (subprocess.CalledProcessError, OSError):
        return False


def _instance_ports_ready(instance: dict) -> bool:
    stack = instance.get("stack", STACK_ARDUPILOT)
    if stack == STACK_PX4:
        return px4._px4_ports_ready(instance["slot"], instance["mavlink_port"])
    return sm._sitl_ports_ready(instance["sitl_tcp_port"], instance["mavlink_port"])


def _sync_running_flags(instances: list[dict]) -> list[dict]:
    synced = []
    for inst in instances:
        copy = dict(inst)
        copy["running"] = _instance_process_running(copy)
        synced.append(copy)
    return synced


def _prune_stale_instances() -> list[dict]:
    fleet = _load_fleet()
    instances = _sync_running_flags(fleet.get("instances", []))
    active = [i for i in instances if i["running"]]
    if len(active) != len(instances):
        fleet["instances"] = active
        _save_fleet(fleet)
    return active


def list_instances() -> list[dict]:
    _migrate_legacy_state()
    return _prune_stale_instances()


def allocate_slot() -> dict:
    active = list_instances()
    used_ids = {i["id"] for i in active}
    if len(active) >= MAX_INSTANCES:
        raise RuntimeError(f"Maximum of {MAX_INSTANCES} aircraft already running")
    for slot in SLOT_TABLE:
        if slot["id"] not in used_ids:
            return dict(slot)
    raise RuntimeError(f"Maximum of {MAX_INSTANCES} aircraft already running")


def release_slot(aircraft_id: str) -> None:
    fleet = _load_fleet()
    fleet["instances"] = [i for i in fleet.get("instances", []) if i["id"] != aircraft_id]
    _save_fleet(fleet)


def _firmware_version_for_instance(inst: dict) -> str:
    log_file = sm.LOG_DIR / f"{inst['id'].lower()}.log"
    if inst.get("stack", STACK_ARDUPILOT) == STACK_PX4:
        return px4.firmware_version_for_log(log_file)
    return sm._firmware_version_for_log(log_file)


def _enrich_instance(inst: dict) -> dict:
    ip = sm.get_hotspot_ip()
    running = _instance_process_running(inst)
    ports_ready = _instance_ports_ready(inst)
    connection_ready = running and ports_ready
    loc = inst.get("location") or {}
    stack = inst.get("stack", STACK_ARDUPILOT)
    stack_label = "PX4" if stack == STACK_PX4 else "ArduPilot"
    return {
        **inst,
        "stack": stack,
        "stack_label": stack_label,
        "running": running,
        "connection_ready": connection_ready,
        "connection_status": "Ready" if connection_ready else ("Starting" if running else "Stopped"),
        "hotspot_ip": ip,
        "mavlink_tcp": f"{ip}:{inst['sitl_tcp_port']}" if stack == STACK_ARDUPILOT else "—",
        "mavlink_udp": f"{ip}:{inst['mavlink_port']}",
        "mavlink_connect": f"UDP {ip}:{inst['mavlink_port']}",
        "location_name": loc.get("name", "—"),
        "firmware_version": _firmware_version_for_instance(inst),
        "px4_model": inst.get("px4_model"),
        "px4_home": (
            px4.px4_home_from_location(loc)
            if stack == STACK_PX4 and loc.get("latitude") is not None
            else None
        ),
    }


def get_fleet_status() -> dict:
    instances = [_enrich_instance(i) for i in list_instances()]
    running_count = sum(1 for i in instances if i["running"])
    ready_count = sum(1 for i in instances if i.get("connection_ready"))
    ip = sm.get_hotspot_ip()
    host = sm.get_host_name()
    return {
        "instances": instances,
        "max_instances": MAX_INSTANCES,
        "running_count": running_count,
        "connected_count": ready_count,
        "error_count": 0,
        "slots_available": MAX_INSTANCES - len(instances),
        "host_name": host,
        "hotspot_ip": ip,
        "web_url": f"http://{host}:{sm.load_config().get('web_port', 8080)}",
        "px4_installed": px4.is_installed(),
    }


def _stop_ardupilot_slot(slot: dict) -> None:
    screen = slot["screen"]
    tcp_port = slot["sitl_tcp_port"]
    mavlink_port = slot["mavlink_port"]
    subprocess.run(["/usr/bin/screen", "-S", screen, "-X", "quit"], check=False)
    subprocess.run(["pkill", "-f", f"master=tcp:127.0.0.1:{tcp_port}"], check=False)
    try:
        out = subprocess.check_output(["lsof", "-ti", f":{tcp_port}"], text=True)
        for pid in out.split():
            subprocess.run(["kill", "-9", pid.strip()], check=False)
    except subprocess.CalledProcessError:
        pass
    try:
        out = subprocess.check_output(["lsof", "-ti", f"udp:{mavlink_port}"], text=True)
        for pid in out.split():
            subprocess.run(["kill", "-9", pid.strip()], check=False)
    except subprocess.CalledProcessError:
        pass


def stop_instance(aircraft_id: str) -> dict:
    fleet = _load_fleet()
    inst = next((i for i in fleet.get("instances", []) if i["id"] == aircraft_id), None)
    slot = _slot_by_id(aircraft_id)
    if not slot:
        raise ValueError(f"Unknown aircraft_id: {aircraft_id}")

    if inst and inst.get("stack", STACK_ARDUPILOT) == STACK_PX4:
        px4.stop_px4_instance(inst["slot"], inst["mavlink_port"], screen=inst["screen"])
    else:
        _stop_ardupilot_slot(slot)

    release_slot(aircraft_id)
    time.sleep(1)
    return get_fleet_status()


def stop_all() -> dict:
    fleet = _load_fleet()
    for inst in list(fleet.get("instances", [])):
        try:
            stop_instance(inst["id"])
        except ValueError:
            pass
    sm.stop_sitl_legacy()
    _save_fleet({"instances": []})
    return get_fleet_status()


def _start_ardupilot_instance(
    slot: dict,
    vehicle: str,
    frame: str,
    loc: dict,
    speedup: int,
) -> dict:
    finfo = sm._frame_info(vehicle, frame)
    binary = sm._binary_path(finfo["waf_target"])
    if not binary.is_file():
        raise FileNotFoundError(
            f"Binary {binary.name} not built. Build {vehicle} in Settings first."
        )

    model = finfo["model"]
    log_file = sm.LOG_DIR / f"{slot['id'].lower()}.log"
    display_name = f"{frame.upper().replace('-', '_')}_{slot['id'][-2:]}"

    cmd = sm.build_start_shell_command(
        binary=binary,
        model=model,
        instance_index=slot["slot"],
        mav_sysid=slot["mav_sysid"],
        sitl_tcp_port=slot["sitl_tcp_port"],
        mavlink_port=slot["mavlink_port"],
        location=loc,
        speedup=speedup,
        log_file=log_file,
    )

    subprocess.run(
        ["/usr/bin/screen", "-dmS", slot["screen"], "bash", "-c", cmd],
        check=True,
    )

    return {
        "id": slot["id"],
        "stack": STACK_ARDUPILOT,
        "vehicle": vehicle,
        "frame": frame,
        "model": model,
        "binary": binary.name,
        "mav_sysid": slot["mav_sysid"],
        "sitl_tcp_port": slot["sitl_tcp_port"],
        "mavlink_port": slot["mavlink_port"],
        "slot": slot["slot"],
        "screen": slot["screen"],
        "location": loc,
        "display_name": display_name,
        "speedup": speedup,
        "running": True,
        "started_at": _utc_now(),
    }


def _start_px4_instance(
    slot: dict,
    vehicle: str,
    frame: str,
    loc: dict,
    px4_model: str | None = None,
) -> dict:
    if not px4.is_installed():
        raise FileNotFoundError(
            "PX4 SIH is not installed on this device. Build it with: "
            "cd ~/PX4-Autopilot && make px4_sitl -j4"
        )

    model_info = px4.resolve_px4_model(vehicle=vehicle, frame=frame, model=px4_model)
    model = model_info["model"]
    log_file = sm.LOG_DIR / f"{slot['id'].lower()}.log"
    display_name = f"PX4_{model_info['frame'].upper()}_{slot['id'][-2:]}"

    cmd = px4.build_start_shell_command(
        model=model,
        instance_index=slot["slot"],
        mavlink_port=slot["mavlink_port"],
        location=loc,
        log_file=log_file,
    )

    subprocess.run(
        ["/usr/bin/screen", "-dmS", slot["screen"], "bash", "-c", cmd],
        check=True,
    )

    return {
        "id": slot["id"],
        "stack": STACK_PX4,
        "vehicle": "PX4",
        "frame": model_info["frame"],
        "px4_model": model,
        "model": model,
        "binary": "px4",
        "mav_sysid": slot["mav_sysid"],
        "sitl_tcp_port": slot["sitl_tcp_port"],
        "mavlink_port": slot["mavlink_port"],
        "slot": slot["slot"],
        "screen": slot["screen"],
        "location": loc,
        "display_name": display_name,
        "speedup": 1,
        "running": True,
        "started_at": _utc_now(),
    }


def start_instance(
    vehicle: str,
    frame: str,
    location: dict | None = None,
    location_id: str | None = None,
    speedup: int = 1,
    stack: str = STACK_ARDUPILOT,
    px4_model: str | None = None,
) -> dict:
    _migrate_legacy_state()
    stack = (stack or STACK_ARDUPILOT).lower()
    if stack not in {STACK_ARDUPILOT, STACK_PX4}:
        raise ValueError(f"Unknown stack: {stack}")

    loc = location_manager.resolve_location(location_id=location_id, location=location)
    slot = allocate_slot()

    if stack == STACK_PX4:
        instance = _start_px4_instance(slot, vehicle, frame, loc, px4_model=px4_model)
    else:
        if vehicle in sm.HIDDEN_VEHICLES:
            raise ValueError(f"{vehicle} is not available for simulation")
        instance = _start_ardupilot_instance(slot, vehicle, frame, loc, speedup)

    fleet = _load_fleet()
    fleet.setdefault("instances", []).append(instance)
    _save_fleet(fleet)

    for _ in range(45):
        enriched = _enrich_instance(instance)
        if stack == STACK_PX4:
            if enriched["connection_ready"]:
                break
        elif enriched["connection_ready"] or enriched["running"]:
            break
        time.sleep(1)

    sm.sync_legacy_state_from_fleet(get_fleet_status())
    return get_fleet_status()


def tail_fleet_log(aircraft_id: str | None = None, lines: int = 40) -> str:
    if aircraft_id:
        log_file = sm.LOG_DIR / f"{aircraft_id.lower()}.log"
        if log_file.exists():
            text = sm._read_log_tail_text(log_file)
            return "\n".join(text.splitlines()[-lines:])
    parts = []
    for inst in list_instances():
        log_file = sm.LOG_DIR / f"{inst['id'].lower()}.log"
        if log_file.exists():
            stack = inst.get("stack_label", inst.get("stack", "ArduPilot"))
            header = f"=== {inst['id']} ({stack} {inst.get('vehicle', '?')}) ==="
            text = sm._read_log_tail_text(log_file)
            content = text.splitlines()[-lines:]
            parts.append(header + "\n" + "\n".join(content))
    return "\n\n".join(parts) if parts else "No log output yet."
