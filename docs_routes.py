#!/usr/bin/env python3
"""Public and shared documentation routes for HiveCard."""

from __future__ import annotations

import json
import re
from pathlib import Path

from flask import Flask, abort, render_template

APP_DIR = Path(__file__).resolve().parent
VIDEOS_PATH = APP_DIR / "data" / "videos.json"

ONLINE_DOCS_URL = "https://jamesuasop.github.io/hivecard/"

DOCS_SECTIONS: list[dict[str, str]] = [
    {
        "id": "getting_started",
        "title": "Getting Started",
        "summary": "Join the HiveCard WiFi, open the web app, and sign in.",
        "video_key": "getting_started",
    },
    {
        "id": "dashboard_fleet",
        "title": "Dashboard & Fleet",
        "summary": "View running aircraft, connection details, and stop controls.",
        "video_key": "dashboard_fleet",
    },
    {
        "id": "start_aircraft",
        "title": "Start Aircraft",
        "summary": "Launch ArduPilot or PX4 simulators with a chosen airframe and location.",
        "video_key": "start_aircraft",
    },
    {
        "id": "connect_qgc",
        "title": "Connect QGroundControl",
        "summary": "Link your phone or tablet to a simulated aircraft over UDP.",
        "video_key": "connect_qgc",
    },
    {
        "id": "locations",
        "title": "Locations",
        "summary": "Add, edit, and favorite starting locations for spawns.",
        "video_key": "locations",
    },
    {
        "id": "settings",
        "title": "Settings",
        "summary": "Change WiFi name, login credentials, and build SITL binaries.",
        "video_key": "settings",
    },
    {
        "id": "logs_troubleshooting",
        "title": "Logs & Troubleshooting",
        "summary": "Read system logs and resolve common issues.",
        "video_key": "logs_troubleshooting",
    },
]

_SECTION_BY_ID = {section["id"]: section for section in DOCS_SECTIONS}


def load_videos() -> dict:
    if not VIDEOS_PATH.exists():
        return {}
    with open(VIDEOS_PATH, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        return {}
    enriched: dict = {}
    for key, entry in data.items():
        if not isinstance(entry, dict):
            continue
        enriched[key] = {
            **entry,
            "embed_url": embed_url(entry.get("youtube_url", "")),
        }
    return enriched


def embed_url(raw_url: str) -> str:
    url = (raw_url or "").strip()
    if not url:
        return ""
    if "youtube.com/watch" in url:
        match = re.search(r"[?&]v=([^&]+)", url)
        if match:
            return f"https://www.youtube.com/embed/{match.group(1)}"
    if "youtu.be/" in url:
        video_id = url.rstrip("/").split("/")[-1].split("?")[0]
        if video_id:
            return f"https://www.youtube.com/embed/{video_id}"
    return url


def register_docs_routes(app: Flask) -> None:
    videos = load_videos()

    @app.route("/help")
    def help_index():
        return render_template(
            "docs/help_index.html",
            docs_sections=DOCS_SECTIONS,
            videos=videos,
            static_docs=False,
            online_docs_url=ONLINE_DOCS_URL,
        )

    @app.route("/help/<section_id>")
    def help_section(section_id: str):
        section = _SECTION_BY_ID.get(section_id)
        if not section:
            abort(404)
        return render_template(
            "docs/help_section.html",
            section=section,
            docs_sections=DOCS_SECTIONS,
            videos=videos,
            docs_brief=True,
            static_docs=False,
            online_docs_url=ONLINE_DOCS_URL,
        )
