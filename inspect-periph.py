#!/usr/bin/env python3
import json
from pathlib import Path

p = Path.home() / "ardupilot/Tools/autotest/pysim/vehicleinfo.json"
d = json.loads(p.read_text())
for name in ("sitl_periph_universal", "sitl_periph_PPP"):
    v = d.get(name, {})
    print(f"\n{name}:")
    print(f"  default_frame={v.get('default_frame')}")
    for frame, finfo in sorted(v.get("frames", {}).items()):
        print(f"  {frame}: waf_target={finfo.get('waf_target')}")
