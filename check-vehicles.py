#!/usr/bin/env python3
import json
import sys
sys.path.insert(0, "/home/uasop/hivecard-web")
import sitl_manager as s

print("simulatable:", json.dumps([v["vehicle"] for v in s.list_simulatable_vehicles()]))
print("buildable:", json.dumps(s.list_buildable_vehicles(), indent=2))
