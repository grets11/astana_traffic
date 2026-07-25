"""
Configuration for the Astana traffic data collector.

SEGMENTS: coordinate pairs along 4 major Astana avenues, verified via
Google Places geocoded street addresses (not hand-guessed), so routes
follow the real road end-to-end.
"""

API_KEY = "YOUR_2GIS_API_KEY_HERE"  # not used on GitHub Actions — it reads GIS_API_KEY from secrets instead

ROUTING_URL = "https://routing.api.2gis.com/routing/7.0.0/global"

# Open-Meteo is free, no key required
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
ASTANA_LAT = 51.1605
ASTANA_LON = 71.4704

SEGMENTS = [
    {
        "id": "kabanbay_batyr",
        "name": "Kabanbay Batyr Avenue",
        "start": {"lat": 51.038731, "lon": 71.447182},  # Qabanbay Batyr Ave 1
        "end":   {"lat": 51.155397, "lon": 71.453405},  # Qabanbay Batyr Ave 30
    },
    {
        "id": "turan_ave",
        "name": "Turan Avenue",
        "start": {"lat": 51.155019, "lon": 71.453670},  # Turan Ave 1
        "end":   {"lat": 51.174146, "lon": 71.406732},  # Turan Ave 55
    },
    {
        "id": "mangilik_el",
        "name": "Mangilik El Avenue",
        "start": {"lat": 51.059462, "lon": 71.413841},  # Ministry of Education, Mangilik El Ave 8
        "end":   {"lat": 51.150303, "lon": 71.444596},  # Mangilik El Avenue 55/23
    },
    {
        "id": "tauelsizdik_ave",
        "name": "Tauelsizdik Avenue",
        "start": {"lat": 51.154514, "lon": 71.454131},  # Tauelsizdik Ave 1
        "end":   {"lat": 51.103720, "lon": 71.454710},  # Tauelsizdik Ave 34
    },
    {
        "id": "turan_ave_n",
        "name": "Turan Avenue (north stretch)",
        "start": {"lat": 51.1310, "lon": 71.4700},
        "end":   {"lat": 51.1450, "lon": 71.4670},
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
# in .github/workflows/collect-traffic.yml.
POLL_INTERVAL_MINUTES = 30

DB_PATH = "traffic_data.db"

