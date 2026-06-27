#!/usr/bin/env python3
"""HiveCard WiFi hotspot (NetworkManager AP) settings."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

HOTSPOT_CONNECTION = os.environ.get("HIVECARD_HOTSPOT_CONN", "HiveCard-Hotspot")
SET_SSID_SCRIPT = Path("/usr/local/sbin/hivecard-set-wifi-ssid.sh")


def _run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, capture_output=True, check=check)


def validate_ssid(ssid: str) -> str:
    ssid = (ssid or "").strip()
    if not ssid:
        raise ValueError("WiFi name cannot be empty")
    if len(ssid.encode("utf-8")) > 32:
        raise ValueError("WiFi name must be 32 bytes or fewer")
    if any(ord(ch) < 32 for ch in ssid):
        raise ValueError("WiFi name contains invalid characters")
    return ssid


def find_hotspot_connection() -> str | None:
    try:
        out = _run(["nmcli", "-t", "-f", "NAME,TYPE", "connection", "show"], check=True).stdout
    except (subprocess.CalledProcessError, OSError):
        return None
    for line in out.splitlines():
        if not line or ":" not in line:
            continue
        name, typ = line.split(":", 1)
        if typ != "802-11-wireless":
            continue
        try:
            mode = _run(
                ["nmcli", "-g", "802-11-wireless.mode", "connection", "show", name],
                check=True,
            ).stdout.strip()
        except (subprocess.CalledProcessError, OSError):
            continue
        if mode == "ap":
            return name
    return HOTSPOT_CONNECTION if _connection_exists(HOTSPOT_CONNECTION) else None


def _connection_exists(name: str) -> bool:
    try:
        _run(["nmcli", "connection", "show", name], check=True)
        return True
    except (subprocess.CalledProcessError, OSError):
        return False


def _connection_active(name: str) -> bool:
    try:
        out = _run(["nmcli", "-t", "-f", "NAME", "connection", "show", "--active"], check=True).stdout
        return any(line.strip() == name for line in out.splitlines())
    except (subprocess.CalledProcessError, OSError):
        return False


def get_hotspot_status() -> dict:
    conn = find_hotspot_connection()
    if not conn:
        return {
            "available": False,
            "connection": None,
            "ssid": None,
            "active": False,
            "error": "No hotspot connection profile found",
        }
    try:
        ssid = _run(
            ["nmcli", "-g", "802-11-wireless.ssid", "connection", "show", conn],
            check=True,
        ).stdout.strip()
    except (subprocess.CalledProcessError, OSError) as exc:
        return {
            "available": False,
            "connection": conn,
            "ssid": None,
            "active": False,
            "error": str(exc),
        }
    return {
        "available": True,
        "connection": conn,
        "ssid": ssid,
        "active": _connection_active(conn),
        "error": None,
    }


def set_hotspot_ssid(ssid: str) -> dict:
    ssid = validate_ssid(ssid)
    conn = find_hotspot_connection()
    if not conn:
        raise RuntimeError("No hotspot connection profile found on this device")

    if SET_SSID_SCRIPT.is_file():
        result = _run(["sudo", "-n", str(SET_SSID_SCRIPT), ssid, conn], check=False)
    else:
        result = _run(
            ["sudo", "-n", "nmcli", "connection", "modify", conn, "802-11-wireless.ssid", ssid],
            check=False,
        )
        if result.returncode == 0 and _connection_active(conn):
            _run(["sudo", "-n", "nmcli", "connection", "down", conn], check=False)
            _run(["sudo", "-n", "nmcli", "connection", "up", conn], check=False)

    if result.returncode != 0:
        err = (result.stderr or result.stdout or "").strip()
        if "password" in err.lower() or "a password is required" in err.lower():
            raise PermissionError(
                "Cannot update WiFi name: install hotspot controls with "
                "sudo bash deploy/install-hotspot-controls.sh"
            )
        raise RuntimeError(err or "Failed to update WiFi name")

    status = get_hotspot_status()
    status["ok"] = True
    return status
