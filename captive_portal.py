#!/usr/bin/env python3
"""Captive portal helpers — redirect WiFi clients to the HiveCard login page."""

from __future__ import annotations

from flask import Flask, redirect, request, url_for

# OS connectivity-check URLs (DNS for these should point at the AP gateway).
CAPTIVE_PORTAL_HOSTS = frozenset(
    {
        "connectivitycheck.gstatic.com",
        "clients3.google.com",
        "www.google.com",
        "captive.apple.com",
        "www.apple.com",
        "msftconnecttest.com",
        "www.msftconnecttest.com",
        "detectportal.firefox.com",
        "nmcheck.gnome.org",
    }
)

CAPTIVE_PORTAL_PATHS = frozenset(
    {
        "/generate_204",
        "/gen_204",
        "/hotspot-detect.html",
        "/library/test/success.html",
        "/connecttest.txt",
        "/redirect",
        "/ncsi.txt",
        "/success.txt",
    }
)

IOS_SUCCESS_HTML = b"<HTML><HEAD><TITLE>Success</TITLE></HEAD><BODY>Success</BODY></HTML>"


def hotspot_login_url() -> str:
    """Default hotspot URL (port 80 on AP is redirected to the web GUI)."""
    return "http://hivecard/login"


def register_captive_portal(app: Flask, session_valid) -> None:
    """Register routes and hooks for mobile captive-portal detection."""

    @app.route("/hotspot")
    def hotspot_landing():
        if session_valid():
            return redirect(url_for("dashboard"))
        return redirect(url_for("login"))

    @app.route("/generate_204")
    @app.route("/gen_204")
    def android_captive_probe():
        if session_valid():
            return "", 204
        return redirect(url_for("login"))

    @app.route("/hotspot-detect.html")
    @app.route("/library/test/success.html")
    def ios_captive_probe():
        if session_valid():
            return IOS_SUCCESS_HTML
        return redirect(url_for("login"))

    @app.route("/connecttest.txt")
    @app.route("/ncsi.txt")
    @app.route("/success.txt")
    def windows_captive_probe():
        if session_valid():
            return "Microsoft Connect Test", 200, {"Content-Type": "text/plain"}
        return redirect(url_for("login"))

    @app.before_request
    def captive_portal_before_request():
        if request.method not in {"GET", "HEAD"}:
            return None
        host = (request.host or "").split(":")[0].lower()
        if host not in CAPTIVE_PORTAL_HOSTS and request.path not in CAPTIVE_PORTAL_PATHS:
            return None
        if request.path in CAPTIVE_PORTAL_PATHS:
            return None
        if session_valid():
            if host in {"connectivitycheck.gstatic.com", "clients3.google.com"}:
                return "", 204
            if host in {"captive.apple.com", "www.apple.com"}:
                return IOS_SUCCESS_HTML
            return redirect(url_for("dashboard"))
        return redirect(url_for("login"))
