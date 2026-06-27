#!/usr/bin/env python3
"""Build static HiveCard documentation for GitHub Pages."""

from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = ROOT / "templates"
OUT_DIR = ROOT / "docs"
VIDEOS_PATH = ROOT / "data" / "videos.json"
ASSETS_SRC = ROOT / "static"
ASSETS_OUT = OUT_DIR / "assets"

DOCS_SECTIONS = [
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


def load_videos() -> dict:
    if not VIDEOS_PATH.exists():
        return {}
    with open(VIDEOS_PATH, encoding="utf-8") as handle:
        data = json.load(handle)
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


def build() -> None:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    videos = load_videos()
    common = {
        "static_docs": True,
        "docs_sections": DOCS_SECTIONS,
        "videos": videos,
        "online_docs_url": "https://jamesuasop.github.io/hivecard/",
    }
    env.globals.update(common)

    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True)
    ASSETS_OUT.mkdir(parents=True)

    if ASSETS_SRC.exists():
        shutil.copytree(ASSETS_SRC, ASSETS_OUT, dirs_exist_ok=True)

    index_html = env.get_template("docs/help_index.html").render(**common)
    (OUT_DIR / "index.html").write_text(index_html, encoding="utf-8")

    for section in DOCS_SECTIONS:
        html = env.get_template("docs/help_section.html").render(
            section=section,
            docs_brief=False,
            **common,
        )
        (OUT_DIR / f"{section['id']}.html").write_text(html, encoding="utf-8")

    print(f"Built GitHub Pages site in {OUT_DIR}")


if __name__ == "__main__":
    try:
        build()
    except Exception as exc:
        print(f"Build failed: {exc}", file=sys.stderr)
        raise
