"""
Configuration for the Astana traffic data collector.

SEGMENTS: fixed start/end coordinate pairs along major Astana roads.
These are approximate — open each pair in 2GIS (or maps.2gis.kz) and
drag-adjust to the exact stretch of road you want to monitor before
you start collecting real data. Coordinates are (lat, lon).

Add/remove segments freely. More segments = richer dataset, but each
segment costs one API call per poll, so keep an eye on your 2GIS quota.
"""

API_KEY = "YOUR_2GIS_API_KEY_HERE"  # not used on GitHub Actions — it reads GIS_API_KEY from secrets instead

ROUTING_URL = "https://routing.api.2gis.com/routing/7.0.0/global"

# Open-Meteo is free, no key required
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
ASTANA_LAT = 51.1605
ASTANA_LON = 71.4704

SEGMENTS = [
    {
        "id": "turan_ave_n",
        "name": "Turan Avenue (north stretch)",
        "start": {"lat": 51.1310, "lon": 71.4700},
        "end":   {"lat": 51.1450, "lon": 71.4670},
    },
    {
        "id": "kabanbay_batyr",
        "name": "Kabanbay Batyr Avenue",
        "start": {"lat": 51.1280, "lon": 71.4300},
        "end":   {"lat": 51.1320, "lon": 71.4650},
    },
    {
        "id": "dostyk_left_bank",
        "name": "Dostyk Street (left bank)",
        "start": {"lat": 51.1250, "lon": 71.4600},
        "end":   {"lat": 51.1360, "lon": 71.4550},
    },
    {
        "id": "respublika_ave",
        "name": "Respublika Avenue (right bank)",
        "start": {"lat": 51.1550, "lon": 71.4300},
        "end":   {"lat": 51.1750, "lon": 71.4400},
    },
    {
        "id": "abay_ave",
        "name": "Abay Avenue",
        "start": {"lat": 51.1600, "lon": 71.4100},
        "end":   {"lat": 51.1650, "lon": 71.4350},
    },
]

# How often to poll, in minutes. Keep this matching the cron schedule
# in .github/workflows/collect-traffic.yml (currently every 30 min).
POLL_INTERVAL_MINUTES = 30

DB_PATH = "traffic_data.db"
