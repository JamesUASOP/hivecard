#!/usr/bin/env python3
"""HiveCard SITL Web GUI."""

from __future__ import annotations

import json
import secrets
from functools import wraps
from pathlib import Path

from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

import hotspot_manager
import location_manager
import px4_manager
import sitl_fleet
import sitl_manager
from captive_portal import hotspot_login_url, register_captive_portal
from docs_routes import DOCS_SECTIONS, ONLINE_DOCS_URL, load_videos, register_docs_routes

APP_DIR = Path(__file__).resolve().parent
CONFIG_PATH = APP_DIR / "config.json"


def load_config() -> dict:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            return json.load(f)
    return {
        "username": "hivecard",
        "password_hash": generate_password_hash("hivecard"),
        "secret_key": secrets.token_hex(32),
        "host": "0.0.0.0",
        "port": 8080,
    }


def save_config(cfg: dict) -> None:
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)
        f.write("\n")


config = load_config()
app = Flask(__name__)
app.secret_key = config.get("secret_key", secrets.token_hex(32))

# New on each service start (power cycle / restart) — invalidates prior browser sessions.
SESSION_BOOT_ID = secrets.token_hex(16)

_build_jobs: dict[str, dict] = {}


def _session_valid() -> bool:
    return session.get("logged_in") and session.get("boot_id") == SESSION_BOOT_ID


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not _session_valid():
            session.clear()
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped


register_captive_portal(app, _session_valid)
register_docs_routes(app)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        auth = load_config()
        if username == auth["username"] and check_password_hash(
            auth["password_hash"], password
        ):
            session["logged_in"] = True
            session["username"] = username
            session["boot_id"] = SESSION_BOOT_ID
            return redirect(url_for("dashboard"))
        flash("Invalid username or password.", "error")
    return render_template("login.html", online_docs_url=ONLINE_DOCS_URL)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
@login_required
def dashboard():
    fleet = sitl_fleet.get_fleet_status()
    status = sitl_manager.get_status()
    vehicles = sitl_manager.list_simulatable_vehicles()
    models = sitl_manager.list_simulatable_models()
    buildable = sitl_manager.list_buildable_vehicles()
    locations = location_manager.list_locations()
    px4_status = px4_manager.get_status()
    return render_template(
        "dashboard.html",
        status=status,
        fleet=fleet,
        vehicles=vehicles,
        models=models,
        buildable=buildable,
        locations=locations,
        px4_status=px4_status,
        px4_models=px4_manager.list_models(),
        log=sitl_manager.tail_log(30),
        hotspot_login_url=hotspot_login_url(),
        hotspot_status=hotspot_manager.get_hotspot_status(),
        docs_sections=DOCS_SECTIONS,
        docs_videos=load_videos(),
        online_docs_url=ONLINE_DOCS_URL,
    )


@app.route("/api/status")
@login_required
def api_status():
    return jsonify(sitl_manager.get_status())


@app.route("/api/fleet")
@login_required
def api_fleet():
    return jsonify(sitl_fleet.get_fleet_status())


@app.route("/api/fleet/start", methods=["POST"])
@login_required
def api_fleet_start():
    data = request.get_json(silent=True) or request.form
    vehicle = data.get("vehicle")
    frame = data.get("frame")
    stack = (data.get("stack") or "ardupilot").lower()
    if not vehicle or not frame:
        return jsonify({"error": "vehicle and frame are required"}), 400
    try:
        fleet = sitl_fleet.start_instance(
            vehicle=vehicle,
            frame=frame,
            location_id=data.get("location_id"),
            location=data.get("location"),
            speedup=int(data.get("speedup", 1)),
            stack=stack,
            px4_model=data.get("px4_model"),
        )
        return jsonify({"ok": True, "fleet": fleet})
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 400
    except FileNotFoundError as exc:
        return jsonify({"error": str(exc)}), 400
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/fleet/stop/<aircraft_id>", methods=["POST"])
@login_required
def api_fleet_stop_one(aircraft_id: str):
    try:
        fleet = sitl_fleet.stop_instance(aircraft_id.upper())
        return jsonify({"ok": True, "fleet": fleet})
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@app.route("/api/fleet/stop-all", methods=["POST"])
@login_required
def api_fleet_stop_all():
    fleet = sitl_fleet.stop_all()
    state = sitl_manager.load_state()
    state["running"] = False
    sitl_manager.save_state(state)
    return jsonify({"ok": True, "fleet": fleet})


@app.route("/api/locations")
@login_required
def api_locations_list():
    category = request.args.get("category")
    favorites = request.args.get("favorites") == "1"
    source = request.args.get("source")
    search = request.args.get("search")
    return jsonify(
        location_manager.list_locations(
            category=category,
            favorites_only=favorites,
            source=source or None,
            search=search or None,
        )
    )


@app.route("/api/locations/<location_id>")
@login_required
def api_locations_get(location_id: str):
    loc = location_manager.get_location(location_id)
    if not loc:
        return jsonify({"error": "not found"}), 404
    return jsonify(loc)


@app.route("/api/locations", methods=["POST"])
@login_required
def api_locations_create():
    data = request.get_json(silent=True) or {}
    try:
        loc = location_manager.create_location(data)
        return jsonify({"ok": True, "location": loc})
    except (ValueError, KeyError) as exc:
        return jsonify({"error": str(exc)}), 400


@app.route("/api/locations/<location_id>", methods=["PUT"])
@login_required
def api_locations_update(location_id: str):
    data = request.get_json(silent=True) or {}
    try:
        loc = location_manager.update_location(location_id, data)
        return jsonify({"ok": True, "location": loc})
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@app.route("/api/locations/<location_id>", methods=["DELETE"])
@login_required
def api_locations_delete(location_id: str):
    try:
        location_manager.delete_location(location_id)
        return jsonify({"ok": True})
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@app.route("/api/px4/status")
@login_required
def api_px4_status():
    return jsonify(px4_manager.get_status())


@app.route("/api/models")
@login_required
def api_models():
    return jsonify(sitl_manager.list_simulatable_models())


@app.route("/api/start", methods=["POST"])
@login_required
def api_start():
    data = request.get_json(silent=True) or request.form
    vehicle = data.get("vehicle")
    frame = data.get("frame")
    if not vehicle or not frame:
        return jsonify({"error": "vehicle and frame are required"}), 400
    try:
        status = sitl_manager.start_sitl(
            vehicle,
            frame,
            speedup=data.get("speedup"),
            location_id=data.get("location_id"),
            location=data.get("location"),
        )
        return jsonify({"ok": True, "status": status, "fleet": sitl_fleet.get_fleet_status()})
    except FileNotFoundError as exc:
        return jsonify({"error": str(exc)}), 400
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 400
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/stop", methods=["POST"])
@login_required
def api_stop():
    sitl_manager.stop_sitl()
    state = sitl_manager.load_state()
    state["running"] = False
    sitl_manager.save_state(state)
    return jsonify({"ok": True, "status": sitl_manager.get_status(), "fleet": sitl_fleet.get_fleet_status()})


@app.route("/api/log")
@login_required
def api_log():
    aircraft_id = request.args.get("aircraft_id")
    return jsonify({"log": sitl_manager.tail_log(50) if not aircraft_id else sitl_fleet.tail_fleet_log(aircraft_id, 50)})


@app.route("/api/build", methods=["POST"])
@login_required
def api_build():
    data = request.get_json(silent=True) or request.form
    vehicle = data.get("vehicle")
    if not vehicle:
        return jsonify({"error": "vehicle is required"}), 400
    existing = _build_jobs.get(vehicle)
    if existing and existing["proc"].poll() is None:
        return jsonify({"ok": True, "message": "Build already in progress", "status": sitl_manager.get_build_status(vehicle)})
    try:
        proc = sitl_manager.build_vehicle(vehicle)
        _build_jobs[vehicle] = {"proc": proc, "vehicle": vehicle}
        return jsonify({
            "ok": True,
            "message": f"Building {vehicle}...",
            "status": sitl_manager.get_build_status(vehicle),
        })
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@app.route("/api/build/status")
@login_required
def api_build_status():
    vehicle = request.args.get("vehicle")
    status = sitl_manager.get_build_status(vehicle)
    if vehicle and vehicle in _build_jobs:
        proc = _build_jobs[vehicle]["proc"]
        if proc.poll() is not None and status.get("percent", 0) >= 100:
            status["running"] = False
            status["status"] = "done" if proc.returncode == 0 else "failed"
    return jsonify(status)


@app.route("/api/account", methods=["PUT"])
@login_required
def api_account_update():
    data = request.get_json(silent=True) or {}
    current_password = data.get("current_password") or ""
    new_username = (data.get("new_username") or "").strip()
    new_password = data.get("new_password") or ""
    confirm_password = data.get("confirm_password") or ""

    if not current_password:
        return jsonify({"error": "Current password is required"}), 400

    auth = load_config()
    if not check_password_hash(auth.get("password_hash", ""), current_password):
        return jsonify({"error": "Current password is incorrect"}), 403

    if not new_username and not new_password:
        return jsonify({"error": "Enter a new username and/or new password"}), 400

    if new_username:
        if len(new_username) < 3:
            return jsonify({"error": "Username must be at least 3 characters"}), 400
        auth["username"] = new_username
        session["username"] = new_username

    if new_password:
        if len(new_password) < 4:
            return jsonify({"error": "Password must be at least 4 characters"}), 400
        if new_password != confirm_password:
            return jsonify({"error": "New passwords do not match"}), 400
        auth["password_hash"] = generate_password_hash(new_password)

    save_config(auth)
    global config
    config = auth
    return jsonify({"ok": True, "username": auth["username"]})


@app.route("/api/hotspot")
@login_required
def api_hotspot_get():
    return jsonify(hotspot_manager.get_hotspot_status())


@app.route("/api/hotspot", methods=["PUT"])
@login_required
def api_hotspot_update():
    data = request.get_json(silent=True) or {}
    ssid = data.get("ssid")
    if ssid is None or not str(ssid).strip():
        return jsonify({"error": "ssid is required"}), 400
    try:
        status = hotspot_manager.set_hotspot_ssid(str(ssid))
        return jsonify(status)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except PermissionError as exc:
        return jsonify({"error": str(exc)}), 403
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 500


if __name__ == "__main__":
    location_manager.ensure_seeded()
    app.run(
        host=config.get("host", "0.0.0.0"),
        port=int(config.get("port", 8080)),
        debug=False,
    )
