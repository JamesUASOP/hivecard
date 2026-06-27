#!/usr/bin/env python3
"""PX4 SIH SITL manager for HiveCard."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import sitl_manager as sm

PX4_DIR = Path(os.environ.get("PX4_DIR", Path.home() / "PX4-Autopilot"))
PX4_BUILD_ROOT = PX4_DIR / "build" / "px4_sitl_default"
PX4_BUILD_ROOT_ALT = PX4_DIR / "build" / "px4_sitl"
PX4_BUILD_BIN = PX4_BUILD_ROOT / "bin" / "px4"
PX4_BUILD_BIN_ALT = PX4_BUILD_ROOT_ALT / "bin" / "px4"
PX4_DATA_ROOT = Path.home() / ".hivecard" / "px4"
PX4_DATA_ROOT.mkdir(parents=True, exist_ok=True)

PX4_MODELS = [
    {
        "model": "sihsim_quadx",
        "vehicle": "PX4",
        "frame": "quad",
        "label": "Quadcopter",
        "description": "SIH quad-X multicopter",
    },
    {
        "model": "sihsim_hex",
        "vehicle": "PX4",
        "frame": "hexa",
        "label": "Hexacopter",
        "description": "SIH hexacopter",
    },
    {
        "model": "sihsim_standard_vtol",
        "vehicle": "PX4",
        "frame": "standard_vtol",
        "label": "Standard VTOL",
        "description": "SIH standard VTOL",
    },
    {
        "model": "sihsim_rover_ackermann",
        "vehicle": "PX4",
        "frame": "rover_ackermann",
        "label": "Rover",
        "description": "SIH Ackermann rover",
    },
]

MODEL_BY_FRAME = {m["frame"]: m for m in PX4_MODELS}
MODEL_BY_MODEL = {m["model"]: m for m in PX4_MODELS}


def px4_mavlink_local_port(instance_index: int) -> int:
    return 18570 + instance_index


def resolve_px4_model(vehicle: str | None = None, frame: str | None = None, model: str | None = None) -> dict:
    if model and model in MODEL_BY_MODEL:
        return MODEL_BY_MODEL[model]
    if frame and frame in MODEL_BY_FRAME:
        return MODEL_BY_FRAME[frame]
    if vehicle == "PX4" and frame:
        if frame in MODEL_BY_FRAME:
            return MODEL_BY_FRAME[frame]
    raise ValueError(f"Unknown PX4 model/frame: vehicle={vehicle!r} frame={frame!r} model={model!r}")


def find_px4_build_root() -> Path | None:
    for root in (PX4_BUILD_ROOT, PX4_BUILD_ROOT_ALT):
        if (root / "bin" / "px4").is_file() and (root / "etc").is_dir():
            return root
    return None


def find_px4_binary() -> Path | None:
    root = find_px4_build_root()
    if root:
        return root / "bin" / "px4"
    for candidate in (
        Path(shutil.which("px4") or ""),
        Path("/opt/px4/bin/px4"),
        Path("/usr/bin/px4"),
    ):
        if candidate and candidate.is_file():
            return candidate
    return None


def is_installed() -> bool:
    return find_px4_binary() is not None


def instance_data_dir(instance_index: int) -> Path:
    path = PX4_DATA_ROOT / f"instance-{instance_index}"
    path.mkdir(parents=True, exist_ok=True)
    return path


def px4_rootfs_dir(instance_index: int) -> Path | None:
    root = find_px4_build_root()
    if not root:
        return None
    return root / "rootfs" / str(instance_index)


def px4_home_from_location(location: dict) -> dict[str, float]:
    """PX4 SIH home: lat/lon/alt (MSL). Heading is ArduPilot-only."""
    lat = float(location["latitude"])
    lon = float(location["longitude"])
    alt = float(location["altitude"])
    if not (-90 <= lat <= 90):
        raise ValueError(f"PX4 home latitude out of range: {lat}")
    if not (-180 <= lon <= 180):
        raise ValueError(f"PX4 home longitude out of range: {lon}")
    return {"lat": lat, "lon": lon, "alt": alt}


def _home_stamp(home: dict[str, float]) -> str:
    return f"{home['lat']:.7f},{home['lon']:.7f},{home['alt']:.1f}"


def prepare_instance_for_location(instance_index: int, location: dict) -> dict[str, float]:
    """Reset persisted SIH home params when the spawn location changes."""
    home = px4_home_from_location(location)
    stamp = _home_stamp(home)
    data_dir = instance_data_dir(instance_index)
    stamp_path = data_dir / "home.stamp"

    def write_home_record() -> None:
        (data_dir / "last_home.json").write_text(
            json.dumps(
                {
                    "latitude": home["lat"],
                    "longitude": home["lon"],
                    "altitude": home["alt"],
                    "location_id": location.get("id"),
                    "location_name": location.get("name"),
                },
                indent=2,
            )
            + "\n"
        )

    if stamp_path.exists() and stamp_path.read_text().strip() == stamp:
        write_home_record()
        return home

    rootfs = px4_rootfs_dir(instance_index)
    if rootfs and rootfs.is_dir():
        for name in ("parameters.bson", "parameters_backup.bson", "dataman"):
            target = rootfs / name
            if target.exists() or target.is_symlink():
                target.unlink(missing_ok=True)

    stamp_path.write_text(stamp + "\n")
    write_home_record()
    return home


def get_version() -> str:
    binary = find_px4_binary()
    if not binary:
        return "Not installed"
    try:
        out = subprocess.check_output(
            [str(binary), "-v"], text=True, stderr=subprocess.STDOUT, timeout=10
        )
        match = re.search(r"PX4\s+v?([0-9][^\s]+)", out)
        if match:
            return f"PX4 {match.group(1)}"
        first = out.strip().splitlines()[0] if out.strip() else "PX4 SIH"
        return first[:80]
    except (subprocess.CalledProcessError, OSError, subprocess.TimeoutExpired):
        return "PX4 SIH"


def list_models() -> list[dict]:
    return [dict(m) for m in PX4_MODELS]


def get_status() -> dict:
    binary = find_px4_binary()
    return {
        "installed": binary is not None,
        "binary": str(binary) if binary else None,
        "version": get_version() if binary else "Not installed",
        "models": list_models(),
        "build_path": str(PX4_BUILD_BIN if PX4_BUILD_BIN.is_file() else PX4_BUILD_BIN_ALT),
    }


def _px4_ports_ready(instance_index: int, mavlink_port: int) -> bool:
    local_port = px4_mavlink_local_port(instance_index)
    try:
        udp_out = subprocess.check_output(["ss", "-ulnp"], text=True)
        local_ok = any(f":{local_port}" in line for line in udp_out.splitlines())
        gcs_ok = any(f":{mavlink_port}" in line for line in udp_out.splitlines())
        return local_ok and gcs_ok
    except (subprocess.CalledProcessError, OSError):
        return False


def _px4_process_running(instance_index: int) -> bool:
    try:
        out = subprocess.check_output(["pgrep", "-af", "px4"], text=True)
    except subprocess.CalledProcessError:
        return False
    marker = f"-i {instance_index}"
    alt_marker = f"-i{instance_index}"
    for line in out.splitlines():
        if "mavproxy" in line.lower() or "SCREEN" in line:
            continue
        if marker in line or alt_marker in line:
            return True
    return False


def instance_running(instance_index: int, mavlink_port: int) -> bool:
    if not _px4_process_running(instance_index):
        return False
    local_port = px4_mavlink_local_port(instance_index)
    try:
        udp_out = subprocess.check_output(["ss", "-ulnp"], text=True)
        return any(f":{local_port}" in line and "px4" in line for line in udp_out.splitlines())
    except (subprocess.CalledProcessError, OSError):
        return False


def build_start_shell_command(
    model: str,
    instance_index: int,
    mavlink_port: int,
    location: dict,
    log_file: Path,
) -> str:
    build_root = find_px4_build_root()
    binary = find_px4_binary()
    if not binary:
        raise FileNotFoundError(
            "PX4 SIH is not installed. Build with: cd ~/PX4-Autopilot && make px4_sitl -j4"
        )

    home = prepare_instance_for_location(instance_index, location)
    lat, lon, alt = home["lat"], home["lon"], home["alt"]
    local_port = px4_mavlink_local_port(instance_index)
    data_dir = instance_data_dir(instance_index)
    cwd = build_root if build_root else binary.parent.parent
    px4_cmd = "./bin/px4" if build_root else str(binary)

    return (
        f"cd {cwd} && "
        f"export XDG_DATA_HOME={data_dir} && "
        f"export PX4_SIM_MODEL={model} && "
        f"export PX4_HOME_LAT={lat:.6f} && "
        f"export PX4_HOME_LON={lon:.6f} && "
        f"export PX4_HOME_ALT={alt:.1f} && "
        f"echo 'PX4 SIH home: lat={lat:.6f} lon={lon:.6f} alt={alt:.1f}m (MSL)' >> {log_file} && "
        f"( {px4_cmd} -i {instance_index} >> {log_file} 2>&1 < /dev/null ) & "
        f"for i in $(seq 1 45); do ss -ulnp | grep -q ':{local_port}' && break; sleep 1; done && "
        f"exec {sm.MAVPROXY} --master=udpout:127.0.0.1:{local_port} "
        f"--out=udpin:0.0.0.0:{mavlink_port}"
    )


def stop_px4_instance(instance_index: int, mavlink_port: int, screen: str | None = None) -> None:
    if screen:
        subprocess.run(["/usr/bin/screen", "-S", screen, "-X", "quit"], check=False)
    subprocess.run(["pkill", "-f", f"udpout:127.0.0.1:{px4_mavlink_local_port(instance_index)}"], check=False)
    subprocess.run(["pkill", "-f", f"udp:127.0.0.1:{px4_mavlink_local_port(instance_index)}"], check=False)
    subprocess.run(["pkill", "-f", f"udpin:0.0.0.0:{mavlink_port}"], check=False)
    subprocess.run(["pkill", "-f", f"bin/px4 -i {instance_index}"], check=False)
    subprocess.run(["pkill", "-f", f"bin/px4 -i{instance_index}"], check=False)
    subprocess.run(["pkill", "-f", f"px4 -i {instance_index}"], check=False)
    subprocess.run(["pkill", "-f", f"px4 -i{instance_index}"], check=False)
    try:
        out = subprocess.check_output(["lsof", "-ti", f"udp:{mavlink_port}"], text=True)
        for pid in out.split():
            subprocess.run(["kill", "-9", pid.strip()], check=False)
    except subprocess.CalledProcessError:
        pass
    local_port = px4_mavlink_local_port(instance_index)
    try:
        out = subprocess.check_output(["lsof", "-ti", f"udp:{local_port}"], text=True)
        for pid in out.split():
            subprocess.run(["kill", "-9", pid.strip()], check=False)
    except subprocess.CalledProcessError:
        pass


def firmware_version_for_log(log_file: Path) -> str:
    if not log_file.exists():
        return get_version()
    text = sm._read_log_tail_text(log_file)
    match = re.search(r"PX4\s+v?([0-9][^\s]+)", text)
    if match:
        return f"PX4 {match.group(1)}"
    if "px4" in text.lower():
        return get_version()
    return "PX4 SIH"
