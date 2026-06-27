#!/usr/bin/env python3
"""Manage ArduPilot SITL instances using vehicleinfo.json frame definitions."""

from __future__ import annotations

import json
import os
import re
import socket
import signal
import subprocess
import sys
import time
from pathlib import Path

ARDUPILOT_DIR = Path(os.environ.get("ARDUPILOT_DIR", Path.home() / "ardupilot"))
BUILD_BIN_DIR = ARDUPILOT_DIR / "build" / "sitl" / "bin"
VEHICLEINFO_PATH = ARDUPILOT_DIR / "Tools" / "autotest" / "pysim" / "vehicleinfo.json"
VENV_BIN = Path(os.environ.get("VENV_BIN", Path.home() / "venv-ardupilot" / "bin"))
MAVPROXY = VENV_BIN / "mavproxy.py"
STATE_PATH = Path(os.environ.get("HIVECARD_STATE", Path.home() / ".hivecard" / "sitl_state.json"))
CONFIG_PATH = Path(os.environ.get("HIVECARD_CONFIG", Path.home() / ".hivecard" / "config.json"))
LOG_DIR = Path.home() / ".hivecard" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
STATE_PATH.parent.mkdir(parents=True, exist_ok=True)

DEFAULTS = {
    "vehicle": "ArduCopter",
    "frame": "quad",
    "speedup": 1,
    "mavlink_port": 14550,
    "sitl_port": 5760,
}

WAF_TARGETS = {
    "ArduCopter": "copter",
    "Helicopter": "heli",
    "ArduPlane": "plane",
    "Rover": "rover",
    "ArduSub": "sub",
    "Blimp": "blimp",
    "AntennaTracker": "antennatracker",
}

# AP_Periph (sitl_periph_universal) is not buildable on the sitl board.

# Hidden from vehicle/frame pickers (still stoppable if running).
HIDDEN_VEHICLES = frozenset({"AntennaTracker", "sitl_periph_universal", "sitl_periph_PPP"})

BUILD_PROGRESS_RE = re.compile(r"\[\s*(\d+)/(\d+)\]")


def load_config() -> dict:
    defaults = {"host_name": f"{socket.gethostname()}.local"}
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            return {**defaults, **json.load(f)}
    return defaults


def get_host_name() -> str:
    return load_config()["host_name"]


def get_hotspot_ip() -> str:
    """Gateway IP on the hotspot interface (fallback for clients without mDNS)."""
    try:
        out = subprocess.check_output(["ip", "-4", "addr", "show", "wlan0"], text=True)
        for line in out.splitlines():
            line = line.strip()
            if line.startswith("inet ") and not line.startswith("inet 127."):
                return line.split()[1].split("/")[0]
    except (subprocess.CalledProcessError, IndexError, OSError):
        pass
    return "10.42.0.1"


def _load_vehicleinfo() -> dict:
    with open(VEHICLEINFO_PATH) as f:
        return json.load(f)


def _frame_info(vehicle: str, frame: str) -> dict:
    info = _load_vehicleinfo()
    if vehicle not in info:
        raise ValueError(f"Unknown vehicle: {vehicle}")
    frames = info[vehicle]["frames"]
    if frame in frames:
        ret = dict(frames[frame])
    else:
        ret = {}
        for prefix in (
            "octa", "tri", "y6", "firefly", "heli", "gazebo", "last_letter",
            "jsbsim", "quadplane", "plane-elevon", "plane-vtail", "plane",
            "airsim",
        ):
            if frame.startswith(prefix) and prefix in frames:
                ret = dict(frames[prefix])
                break
        if not ret and frame.endswith("-heli") and "heli" in frames:
            ret = dict(frames["heli"])
    if not ret:
        raise ValueError(f"Unknown frame '{frame}' for {vehicle}")
    if "model" not in ret:
        ret["model"] = frame
    if "waf_target" not in ret:
        default_frame = info[vehicle]["default_frame"]
        ret["waf_target"] = info[vehicle]["frames"][default_frame]["waf_target"]
    return ret


def _binary_path(waf_target: str) -> Path:
    name = Path(waf_target).name
    return BUILD_BIN_DIR / name


def load_state() -> dict:
    if STATE_PATH.exists():
        with open(STATE_PATH) as f:
            state = json.load(f)
        return {**DEFAULTS, **state}
    return dict(DEFAULTS)


def save_state(state: dict) -> None:
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)


def list_models(simulatable_only: bool = False) -> list[dict]:
    info = _load_vehicleinfo()
    models = []
    for vehicle, vdata in sorted(info.items()):
        if vehicle in HIDDEN_VEHICLES:
            continue
        default_frame = vdata.get("default_frame", "")
        for frame in sorted(vdata.get("frames", {}).keys()):
            try:
                finfo = _frame_info(vehicle, frame)
            except ValueError:
                continue
            binary = _binary_path(finfo["waf_target"])
            entry = {
                "vehicle": vehicle,
                "frame": frame,
                "model": finfo["model"],
                "binary": binary.name,
                "binary_exists": binary.is_file(),
                "is_default": frame == default_frame,
            }
            if simulatable_only and not entry["binary_exists"]:
                continue
            models.append(entry)
    return models


def list_simulatable_models() -> list[dict]:
    return list_models(simulatable_only=True)


def list_vehicles(simulatable_only: bool = False) -> list[dict]:
    info = _load_vehicleinfo()
    result = []
    for vehicle, vdata in sorted(info.items()):
        if vehicle in HIDDEN_VEHICLES:
            continue
        sim_frames = []
        for frame in sorted(vdata.get("frames", {}).keys()):
            try:
                finfo = _frame_info(vehicle, frame)
                if _binary_path(finfo["waf_target"]).is_file():
                    sim_frames.append(frame)
            except ValueError:
                continue
        if simulatable_only and not sim_frames:
            continue
        default_frame = vdata.get("default_frame", "")
        if simulatable_only and default_frame not in sim_frames and sim_frames:
            default_frame = sim_frames[0]
        waf_target = vdata["frames"][vdata.get("default_frame", default_frame)]["waf_target"]
        binary = _binary_path(waf_target)
        result.append(
            {
                "vehicle": vehicle,
                "default_frame": default_frame,
                "frames": sim_frames if simulatable_only else sorted(vdata.get("frames", {}).keys()),
                "binary_exists": binary.is_file(),
                "waf_target": WAF_TARGETS.get(vehicle),
            }
        )
    return result


def list_simulatable_vehicles() -> list[dict]:
    return list_vehicles(simulatable_only=True)


def list_buildable_vehicles() -> list[dict]:
    """Vehicle types whose SITL binary is not yet built."""
    built_binaries = {p.name for p in BUILD_BIN_DIR.glob("*") if p.is_file()}
    result = []
    seen_targets = set()
    for vehicle, target in sorted(WAF_TARGETS.items()):
        if vehicle in HIDDEN_VEHICLES:
            continue
        binary_name = {
            "copter": "arducopter",
            "heli": "arducopter-heli",
            "plane": "arduplane",
            "rover": "ardurover",
            "sub": "ardusub",
            "blimp": "blimp",
            "antennatracker": "antennatracker",
        }.get(target, Path(target).name)
        if binary_name in built_binaries or target in seen_targets:
            continue
        seen_targets.add(target)
        result.append({"vehicle": vehicle, "target": target, "binary": binary_name})
    return result


def _build_log_path(vehicle: str) -> Path:
    target = WAF_TARGETS.get(vehicle, vehicle)
    return LOG_DIR / f"build-{target}.log"


def _parse_build_log(log_path: Path) -> dict:
    current, total, percent = 0, 0, 0
    status = "idle"
    message = ""
    if log_path.exists():
        text = log_path.read_text(errors="replace")
        for line in reversed(text.splitlines()):
            m = BUILD_PROGRESS_RE.search(line)
            if m:
                current, total = int(m.group(1)), int(m.group(2))
                percent = round(current * 100 / total) if total else 0
                message = line.strip()
                status = "building"
                break
        if "finished successfully" in text:
            status = "done"
            percent = 100
            message = next(
                (ln.strip() for ln in reversed(text.splitlines()) if "finished successfully" in ln),
                "Build finished successfully",
            )
        elif status == "idle" and text.strip():
            status = "building"
            message = text.splitlines()[-1].strip()
    return {
        "current": current,
        "total": total,
        "percent": percent,
        "status": status,
        "message": message,
    }


def _waf_build_running() -> bool:
    try:
        out = subprocess.check_output(
            ["pgrep", "-f", str(ARDUPILOT_DIR / "waf")], text=True
        )
        return bool(out.strip())
    except subprocess.CalledProcessError:
        return False


def get_build_status(vehicle: str | None = None) -> dict:
    if vehicle:
        log_path = _build_log_path(vehicle)
        parsed = _parse_build_log(log_path)
        running = _waf_build_running()
        if parsed["status"] == "building" and not running:
            if "finished successfully" in (log_path.read_text(errors="replace") if log_path.exists() else ""):
                parsed["status"] = "done"
                parsed["percent"] = 100
            elif parsed["percent"] > 0:
                parsed["status"] = "done" if parsed["percent"] >= 100 else "failed"
            else:
                parsed["status"] = "idle"
        elif parsed["status"] != "done" and running:
            parsed["status"] = "building"
        return {"vehicle": vehicle, "running": running, **parsed}

    jobs = []
    for v in WAF_TARGETS:
        st = get_build_status(v)
        if st["status"] != "idle":
            jobs.append(st)
    return {"jobs": jobs, "any_running": any(j["running"] for j in jobs)}


def build_vehicle(vehicle: str) -> subprocess.Popen:
    target = WAF_TARGETS.get(vehicle)
    if not target:
        raise ValueError(f"Cannot build unknown vehicle: {vehicle}")
    log_file = _build_log_path(vehicle)
    log_file.write_text("")
    return subprocess.Popen(
        ["./waf", target, "-j4"],
        cwd=ARDUPILOT_DIR,
        stdout=open(log_file, "w"),
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )


def _pids_for(name: str) -> list[int]:
    try:
        out = subprocess.check_output(["pgrep", "-f", name], text=True)
        return [int(x) for x in out.split()]
    except subprocess.CalledProcessError:
        return []


def _read_log_tail_text(log_path: Path, max_bytes: int = 262144) -> str:
    """Read only the tail of a log file (avoids loading multi-MB SITL logs)."""
    try:
        if not log_path.exists():
            return ""
        with open(log_path, "rb") as f:
            f.seek(0, 2)
            size = f.tell()
            f.seek(max(0, size - min(size, max_bytes)))
            return f.read().decode("utf-8", errors="replace")
    except OSError:
        return ""


def _firmware_version_for_log(log_path: Path) -> str:
    try:
        if not log_path.exists():
            return "ArduPilot SITL"
        text = _read_log_tail_text(log_path)
        for line in reversed(text.splitlines()):
            if any(
                tag in line
                for tag in (
                    "ArduCopter V",
                    "ArduPlane V",
                    "Rover V",
                    "ArduSub V",
                    "Blimp V",
                    "Tracker V",
                    "AP_Periph",
                )
            ):
                return line.split("AP:")[-1].strip() if "AP:" in line else line.strip()
    except OSError:
        pass
    return "ArduPilot SITL"


def _firmware_version() -> str:
    paths = list(LOG_DIR.glob("ac*.log")) + list(LOG_DIR.glob("*.log")) + [Path.home() / "sitl.log"]
    for path in paths:
        ver = _firmware_version_for_log(path)
        if ver != "ArduPilot SITL":
            return ver
    return "ArduPilot SITL"


def build_start_shell_command(
    binary: Path,
    model: str,
    instance_index: int,
    mav_sysid: int,
    sitl_tcp_port: int,
    mavlink_port: int,
    location: dict,
    speedup: int,
    log_file: Path,
) -> str:
    lat = float(location["latitude"])
    lon = float(location["longitude"])
    alt = float(location["altitude"])
    heading = float(location["heading"])
    sitl_ctrl_port = 5501 + instance_index * 10
    loc_arg = f"-O {lat:.6f},{lon:.6f},{alt:.1f},{heading:.1f}"

    return (
        f"source {VENV_BIN.parent}/bin/activate && "
        f"( : ; {binary} --model {model} --speedup {speedup} "
        f"--sysid {mav_sysid} -I{instance_index} {loc_arg} "
        f"--slave 0 --sim-address=127.0.0.1 >> {log_file} 2>&1 < /dev/null ) & "
        f"for i in $(seq 1 30); do ss -tln | grep -q ':{sitl_tcp_port}' && break; sleep 1; done && "
        f"exec {MAVPROXY} --retries 10 --master=tcp:127.0.0.1:{sitl_tcp_port} "
        f"--sitl=127.0.0.1:{sitl_ctrl_port} --out=udpin:0.0.0.0:{mavlink_port}"
    )


def sync_legacy_state_from_fleet(fleet_status: dict) -> None:
    """Keep sitl_state.json in sync for backward compatibility."""
    instances = fleet_status.get("instances", [])
    if not instances:
        state = load_state()
        state["running"] = False
        save_state(state)
        return
    first = instances[0]
    save_state(
        {
            "vehicle": first.get("vehicle", "ArduCopter"),
            "frame": first.get("frame", "quad"),
            "speedup": first.get("speedup", 1),
            "mavlink_port": first.get("mavlink_port", 14550),
            "sitl_port": first.get("sitl_tcp_port", 5760),
            "model": first.get("model", first.get("frame", "quad")),
            "binary": first.get("binary"),
            "running": first.get("running", False),
        }
    )


def _sitl_ports_ready(sitl_port: int, mavlink_port: int) -> bool:
    try:
        tcp_out = subprocess.check_output(["ss", "-tln"], text=True)
        udp_out = subprocess.check_output(["ss", "-ulnp"], text=True)
        tcp_ok = any(
            f":{sitl_port}" in line and "LISTEN" in line for line in tcp_out.splitlines()
        )
        udp_ok = any(
            f":{mavlink_port}" in line for line in udp_out.splitlines()
        )
        return tcp_ok and udp_ok
    except (subprocess.CalledProcessError, OSError):
        return False


def get_status() -> dict:
    """Backward-compatible status; delegates to fleet when available."""
    try:
        import sitl_fleet

        fleet = sitl_fleet.get_fleet_status()
        sync_legacy_state_from_fleet(fleet)
        instances = fleet.get("instances", [])
        if instances:
            first = instances[0]
            return {
                **load_state(),
                "running": fleet["running_count"] > 0,
                "arducopter_pids": _pids_for("build/sitl/bin/"),
                "mavproxy_pids": _pids_for("mavproxy.py"),
                "binary": first.get("binary"),
                "binary_exists": True,
                "host_name": fleet["host_name"],
                "hotspot_ip": fleet["hotspot_ip"],
                "vehicle": first.get("vehicle"),
                "frame": first.get("frame"),
                "model": first.get("model", first.get("frame")),
                "speedup": first.get("speedup", 1),
                "sitl_port": first.get("sitl_tcp_port", 5760),
                "mavlink_port": first.get("mavlink_port", 14550),
                "display_name": first.get("display_name"),
                "firmware_version": first.get("firmware_version", _firmware_version()),
                "mavlink_tcp": first.get("mavlink_tcp"),
                "mavlink_udp": first.get("mavlink_udp"),
                "mavlink_connect": first.get("mavlink_connect"),
                "sitl_connect": f"TCP {fleet['hotspot_ip']}:{first.get('sitl_tcp_port', 5760)}",
                "web_url": fleet["web_url"],
                "connection_ready": first.get("connection_ready", False),
                "connection_status": first.get("connection_status", "Not Ready"),
                "connected_count": fleet["connected_count"],
                "error_count": fleet["error_count"],
                "fleet": fleet,
            }
    except Exception:
        pass

    state = load_state()
    arducopter_pids = _pids_for("build/sitl/bin/")
    mavproxy_pids = _pids_for("mavproxy.py")
    running = bool(arducopter_pids and mavproxy_pids)
    binary = None
    binary_exists = False
    try:
        finfo = _frame_info(state["vehicle"], state["frame"])
        binary = _binary_path(finfo["waf_target"]).name
        binary_exists = _binary_path(finfo["waf_target"]).is_file()
    except ValueError:
        pass
    host = get_host_name()
    ip = get_hotspot_ip()
    frame = state.get("frame", "quad")
    ports_ready = _sitl_ports_ready(state["sitl_port"], state["mavlink_port"])
    connection_ready = running and ports_ready
    return {
        **state,
        "running": running,
        "arducopter_pids": arducopter_pids,
        "mavproxy_pids": mavproxy_pids,
        "binary": binary,
        "binary_exists": binary_exists,
        "host_name": host,
        "hotspot_ip": ip,
        "display_name": f"{frame.upper().replace('-', '_')}_01",
        "firmware_version": _firmware_version(),
        "mavlink_tcp": f"{ip}:{state['sitl_port']}",
        "mavlink_udp": f"{ip}:{state['mavlink_port']}",
        "mavlink_connect": f"UDP {ip}:{state['mavlink_port']}",
        "sitl_connect": f"TCP {ip}:{state['sitl_port']}",
        "web_url": f"http://{host}:{load_config().get('web_port', 8080)}",
        "connection_ready": connection_ready,
        "connection_status": "Ready" if connection_ready else "Not Ready",
        "connected_count": 1 if connection_ready else 0,
        "error_count": 0,
    }


def stop_sitl_legacy() -> None:
    """Kill all SITL-related processes (legacy single-instance cleanup)."""
    for screen in ("sitl", "sitl-ac01", "sitl-ac02", "sitl-ac03"):
        subprocess.run(["/usr/bin/screen", "-S", screen, "-X", "quit"], check=False)
    subprocess.run(["killall", "-q", "mavproxy.py"], check=False)
    subprocess.run(["killall", "-q", "arducopter"], check=False)
    subprocess.run(["killall", "-q", "arduplane"], check=False)
    subprocess.run(["killall", "-q", "ardurover"], check=False)
    subprocess.run(["killall", "-q", "ardusub"], check=False)
    subprocess.run(["killall", "-q", "blimp"], check=False)
    subprocess.run(["killall", "-q", "arducopter-heli"], check=False)
    subprocess.run(["killall", "-q", "antennatracker"], check=False)
    subprocess.run(["killall", "-q", "AP_Periph"], check=False)
    time.sleep(2)


def stop_sitl() -> None:
    """Stop all fleet instances."""
    import sitl_fleet

    sitl_fleet.stop_all()


def start_sitl(
    vehicle: str | None = None,
    frame: str | None = None,
    speedup: int | None = None,
    location_id: str | None = None,
    location: dict | None = None,
) -> dict:
    """Start one aircraft via fleet manager (backward-compatible wrapper)."""
    import sitl_fleet

    state = load_state()
    v = vehicle or state["vehicle"]
    if v in HIDDEN_VEHICLES:
        raise ValueError(f"{v} is not available for simulation")
    f = frame or state["frame"]
    sp = speedup or state.get("speedup", 1)
    sitl_fleet.start_instance(
        vehicle=v,
        frame=f,
        location_id=location_id,
        location=location,
        speedup=sp,
    )
    return get_status()


def tail_log(lines: int = 40) -> str:
    try:
        import sitl_fleet

        return sitl_fleet.tail_fleet_log(lines=lines)
    except Exception:
        pass
    state = load_state()
    try:
        binary = _binary_path(finfo["waf_target"])
        log_file = LOG_DIR / f"{binary.stem}.log"
        if log_file.exists():
            text = _read_log_tail_text(log_file)
            return "\n".join(text.splitlines()[-lines:])
    except (ValueError, OSError):
        pass
    sitl_log = Path.home() / "sitl.log"
    if sitl_log.exists():
        text = _read_log_tail_text(sitl_log)
        return "\n".join(text.splitlines()[-lines:])
    return "No log output yet."


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps(get_status(), indent=2))
        sys.exit(0)
    cmd = sys.argv[1]
    if cmd == "start":
        vehicle = sys.argv[2] if len(sys.argv) > 2 else None
        frame = sys.argv[3] if len(sys.argv) > 3 else None
        print(json.dumps(start_sitl(vehicle, frame), indent=2))
    elif cmd == "stop":
        stop_sitl()
        state = load_state()
        state["running"] = False
        save_state(state)
        print("stopped")
    elif cmd == "status":
        print(json.dumps(get_status(), indent=2))
    elif cmd == "models":
        print(json.dumps(list_simulatable_models(), indent=2))
    elif cmd == "build-status":
        vehicle = sys.argv[2] if len(sys.argv) > 2 else None
        print(json.dumps(get_build_status(vehicle), indent=2))
    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        sys.exit(1)
