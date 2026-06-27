#!/usr/bin/env python3
import json
from pathlib import Path

p = Path.home() / "ardupilot/Tools/autotest/pysim/vehicleinfo.json"
d = json.loads(p.read_text())
for name in ("Helicopter", "Blimp", "ArduSub", "sitl_periph_universal"):
    v = d.get(name, {})
    df = v.get("default_frame")
    wt = v.get("frames", {}).get(df, {}).get("waf_target") if df else None
    print(f"{name}: default={df} waf_target={wt}")
    if name == "Helicopter":
        for frame, finfo in sorted(v.get("frames", {}).items()):
            print(f"  {frame}: {finfo.get('waf_target')}")
