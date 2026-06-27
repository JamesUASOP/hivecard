#!/usr/bin/env python3
"""Saved starting locations for SITL fleet."""

from __future__ import annotations

import json
import re
import uuid
from pathlib import Path

LOCATIONS_PATH = Path.home() / ".hivecard" / "locations.json"
LOCATIONS_PATH.parent.mkdir(parents=True, exist_ok=True)

ARDUPILOT_LOCATIONS = Path.home() / "ardupilot" / "Tools" / "autotest" / "locations.txt"

DEFAULT_LOCATIONS = [
    {
        "name": "CMAC",
        "latitude": -35.363262,
        "longitude": 149.165237,
        "altitude": 584.0,
        "heading": 353.0,
        "category": "ArduPilot",
        "description": "Canberra Model Aircraft Club (ArduPilot default)",
        "is_favorite": True,
    },
    {
        "name": "Home Base",
        "latitude": 37.7749,
        "longitude": -122.4194,
        "altitude": 100.0,
        "heading": 0.0,
        "category": "General",
        "description": "Default home location for aircraft operations",
        "is_favorite": True,
    },
    {
        "name": "Training Area",
        "latitude": 37.7849,
        "longitude": -122.4094,
        "altitude": 150.0,
        "heading": 90.0,
        "category": "Training",
        "description": "Designated training area for flight practice",
        "is_favorite": True,
    },
    {
        "name": "Emergency Zone",
        "latitude": 37.7649,
        "longitude": -122.4294,
        "altitude": 200.0,
        "heading": 180.0,
        "category": "Emergency",
        "description": "Emergency response area for critical operations",
        "is_favorite": False,
    },
    {
        "name": "Mountain Peak",
        "latitude": 37.7949,
        "longitude": -122.4394,
        "altitude": 500.0,
        "heading": 45.0,
        "category": "General",
        "description": "High altitude mountain peak location",
        "is_favorite": False,
    },
    {
        "name": "Coastal Base",
        "latitude": 37.7549,
        "longitude": -122.3994,
        "altitude": 50.0,
        "heading": 270.0,
        "category": "General",
        "description": "Coastal base near the ocean",
        "is_favorite": False,
    },
    {
        "name": "Urban Center",
        "latitude": 37.8049,
        "longitude": -122.4494,
        "altitude": 300.0,
        "heading": 135.0,
        "category": "General",
        "description": "Urban center for city operations",
        "is_favorite": False,
    },
    {
        "name": "Forest Landing",
        "latitude": 37.7449,
        "longitude": -122.3894,
        "altitude": 75.0,
        "heading": 225.0,
        "category": "General",
        "description": "Forest landing zone for nature operations",
        "is_favorite": False,
    },
    {
        "name": "Desert Outpost",
        "latitude": 37.8149,
        "longitude": -122.4594,
        "altitude": 250.0,
        "heading": 315.0,
        "category": "General",
        "description": "Desert outpost for arid environment operations",
        "is_favorite": False,
    },
]

LOCATION_LINE_RE = re.compile(
    r"^([A-Za-z0-9_\-]+)=([-\d.]+),([-\d.]+),([-\d.]+),([-\d.]+)"
)


def _new_id() -> str:
    return str(uuid.uuid4())[:8]


def _load_raw() -> list[dict]:
    if not LOCATIONS_PATH.exists():
        return []
    with open(LOCATIONS_PATH) as f:
        data = json.load(f)
    return data if isinstance(data, list) else []


def _save_all(locations: list[dict]) -> None:
    with open(LOCATIONS_PATH, "w") as f:
        json.dump(locations, f, indent=2)


def _validate_location_data(data: dict, *, require_coords: bool = True) -> None:
    name = (data.get("name") or "").strip()
    if not name:
        raise ValueError("Location name is required")
    if require_coords:
        try:
            lat = float(data["latitude"])
            lon = float(data["longitude"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("Valid latitude and longitude are required") from exc
        if not (-90 <= lat <= 90):
            raise ValueError("Latitude must be between -90 and 90")
        if not (-180 <= lon <= 180):
            raise ValueError("Longitude must be between -180 and 180")


def _normalize_source(loc: dict) -> str:
    if loc.get("source"):
        return loc["source"]
    if loc.get("category") == "ArduPilot":
        return "ardupilot"
    if loc.get("name") in {d["name"] for d in DEFAULT_LOCATIONS}:
        return "default"
    return "user"


def _with_source(loc: dict) -> dict:
    out = dict(loc)
    out["source"] = _normalize_source(out)
    return out


def _import_ardupilot_locations(existing_names: set[str]) -> list[dict]:
    imported = []
    if not ARDUPILOT_LOCATIONS.is_file():
        return imported
    for line in ARDUPILOT_LOCATIONS.read_text(errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = LOCATION_LINE_RE.match(line)
        if not m:
            continue
        name = m.group(1)
        if name in existing_names:
            continue
        imported.append(
            {
                "id": _new_id(),
                "name": name,
                "latitude": float(m.group(2)),
                "longitude": float(m.group(3)),
                "altitude": float(m.group(4)),
                "heading": float(m.group(5)),
                "category": "ArduPilot",
                "description": f"Imported from locations.txt ({name})",
                "is_favorite": name in ("CMAC", "KSFO"),
                "source": "ardupilot",
            }
        )
        existing_names.add(name)
    return imported


def ensure_seeded() -> None:
    if LOCATIONS_PATH.exists() and _load_raw():
        return
    locations = []
    names: set[str] = set()
    for loc in DEFAULT_LOCATIONS:
        entry = {"id": _new_id(), "source": "default", **loc}
        locations.append(entry)
        names.add(loc["name"])
    locations.extend(_import_ardupilot_locations(names))
    _save_all(locations)


def list_locations(
    category: str | None = None,
    favorites_only: bool = False,
    source: str | None = None,
    search: str | None = None,
) -> list[dict]:
    ensure_seeded()
    items = [_with_source(x) for x in _load_raw()]
    if source:
        items = [x for x in items if x.get("source") == source]
    if category:
        items = [x for x in items if x.get("category") == category]
    if favorites_only:
        items = [x for x in items if x.get("is_favorite")]
    if search:
        q = search.strip().lower()
        if q:
            items = [
                x
                for x in items
                if q in x.get("name", "").lower()
                or q in x.get("category", "").lower()
                or q in x.get("description", "").lower()
            ]
    items.sort(
        key=lambda x: (
            not x.get("is_favorite", False),
            x.get("source") != "user",
            x.get("name", "").lower(),
        )
    )
    return items


def get_location(location_id: str) -> dict | None:
    ensure_seeded()
    for loc in _load_raw():
        if loc.get("id") == location_id:
            return _with_source(loc)
    return None


def get_default_location() -> dict:
    ensure_seeded()
    favorites = list_locations(favorites_only=True)
    if favorites:
        return dict(favorites[0])
    items = list_locations()
    if items:
        return dict(items[0])
    return {
        "id": "default",
        "name": "Default",
        "latitude": -35.363262,
        "longitude": 149.165237,
        "altitude": 584.0,
        "heading": 353.0,
        "category": "Default",
        "description": "ArduPilot CMAC default",
        "is_favorite": True,
    }


def resolve_location(
    location_id: str | None = None,
    location: dict | None = None,
) -> dict:
    if location_id:
        found = get_location(location_id)
        if not found:
            raise ValueError(f"Unknown location_id: {location_id}")
        return found
    if location:
        required = ("latitude", "longitude", "altitude", "heading")
        for key in required:
            if key not in location:
                raise ValueError(f"location.{key} is required")
        return {
            "id": location.get("id", "inline"),
            "name": location.get("name", "Custom"),
            "latitude": float(location["latitude"]),
            "longitude": float(location["longitude"]),
            "altitude": float(location["altitude"]),
            "heading": float(location["heading"]),
            "category": location.get("category", "Custom"),
            "description": location.get("description", ""),
            "is_favorite": bool(location.get("is_favorite", False)),
        }
    return get_default_location()


def create_location(data: dict) -> dict:
    ensure_seeded()
    _validate_location_data(data)
    name = data["name"].strip()
    locations = [_with_source(x) for x in _load_raw()]
    if any(x.get("name", "").lower() == name.lower() for x in locations):
        raise ValueError(f"A location named '{name}' already exists")
    entry = {
        "id": _new_id(),
        "name": name,
        "latitude": float(data["latitude"]),
        "longitude": float(data["longitude"]),
        "altitude": float(data.get("altitude", 0)),
        "heading": float(data.get("heading", 0)),
        "category": data.get("category", "General"),
        "description": data.get("description", ""),
        "is_favorite": bool(data.get("is_favorite", False)),
        "source": "user",
    }
    locations.append(entry)
    _save_all(locations)
    return entry


def update_location(location_id: str, data: dict) -> dict:
    ensure_seeded()
    locations = _load_raw()
    for i, loc in enumerate(locations):
        if loc.get("id") != location_id:
            continue
        merged = {**_with_source(loc), **data}
        _validate_location_data(merged)
        updated = dict(loc)
        if "name" in data:
            updated["name"] = str(data["name"]).strip()
        for key in ("latitude", "longitude", "altitude", "heading"):
            if key in data:
                updated[key] = float(data[key])
        for key in ("category", "description"):
            if key in data:
                updated[key] = data[key]
        if "is_favorite" in data:
            updated["is_favorite"] = bool(data["is_favorite"])
        if _normalize_source(loc) == "user" or updated.get("source") == "user":
            updated["source"] = "user"
        locations[i] = updated
        _save_all(locations)
        return _with_source(updated)
    raise ValueError(f"Unknown location_id: {location_id}")


def delete_location(location_id: str) -> None:
    ensure_seeded()
    locations = _load_raw()
    target = next((x for x in locations if x.get("id") == location_id), None)
    if not target:
        raise ValueError(f"Unknown location_id: {location_id}")
    if _normalize_source(target) == "ardupilot":
        raise ValueError("Built-in ArduPilot locations cannot be deleted")
    new_list = [x for x in locations if x.get("id") != location_id]
    _save_all(new_list)


def list_categories() -> list[str]:
    ensure_seeded()
    cats = sorted({x.get("category", "General") for x in _load_raw()})
    return cats
