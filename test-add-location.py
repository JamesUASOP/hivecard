#!/usr/bin/env python3
import sys
sys.path.insert(0, "/home/uasop/hivecard-web")
import location_manager as lm

lm.create_location({
    "name": "Test Field Alpha",
    "latitude": 33.45,
    "longitude": -112.07,
    "altitude": 350,
    "heading": 90,
    "category": "Training",
    "is_favorite": True,
})
user_locs = lm.list_locations(source="user")
print("user locations:", len(user_locs))
print("latest:", user_locs[-1]["name"])
