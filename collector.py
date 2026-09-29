@@ -1,273 +1 @@
"""
Astana Traffic Data Collector
==============================
Polls the 2GIS Routing API for a fixed set of road segments, records the
real-time travel duration/distance for each, pulls matching weather data,
and appends everything to a local SQLite database.

Run this once manually to test, then schedule it (cron / Task Scheduler /
a simple `while True: sleep()` loop) to run every POLL_INTERVAL_MINUTES.
You need several weeks of data at 5-15 min resolution before there's
enough signal to train a useful model.

Usage:
    python collector.py            # single poll, then exit
    python collector.py --loop     # poll forever at the configured interval
"""

"""
import os
import sys
import time
import sqlite3
import logging
import argparse
from datetime import datetime, timezone

import requests

import config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("collector")


def get_api_key() -> str:
    key = os.environ.get("GIS_API_KEY") or config.API_KEY
    if not key or key == "YOUR_2GIS_API_KEY_HERE":
        log.error("No 2GIS API key configured. Set GIS_API_KEY env var or edit config.py.")
        sys.exit(1)
    return key


def init_db(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS traffic_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            segment_id TEXT NOT NULL,
            segment_name TEXT,
            timestamp_utc TEXT NOT NULL,
            duration_sec INTEGER,
            distance_m INTEGER,
            avg_speed_kmh REAL,
            raw_response TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS weather_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp_utc TEXT NOT NULL,
            temperature_c REAL,
            precipitation_mm REAL,
            snowfall_cm REAL,
            wind_speed_kmh REAL,
            weather_code INTEGER
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_traffic_segment_time
        ON traffic_readings (segment_id, timestamp_utc)
    """)
    conn.commit()
    return conn


def fetch_segment_duration(session: requests.Session, api_key: str, segment: dict) -> dict | None:
    """Call 2GIS Routing API for one segment under real-time traffic."""
    payload = {
        "points": [
            {"type": "stop", "lat": segment["start"]["lat"], "lon": segment["start"]["lon"]},
            {"type": "stop", "lat": segment["end"]["lat"], "lon": segment["end"]["lon"]},
        ],
        "locale": "en",
        "transport": "driving",
        "route_mode": "fastest",
        "traffic_mode": "jam",  # real-time traffic
    }
    try:
        resp = session.post(
            config.ROUTING_URL,
            params={"key": api_key},
            json=payload,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        results = data.get("result") or []
        if not results:
            log.warning(f"No route returned for segment {segment['id']}")
            return None
        best = results[0]
        duration_sec = best.get("total_duration")
        distance_m = best.get("total_distance")
        avg_speed_kmh = None
        if duration_sec and distance_m and duration_sec > 0:
            avg_speed_kmh = (distance_m / 1000) / (duration_sec / 3600)
        return {
            "duration_sec": duration_sec,
            "distance_m": distance_m,
            "avg_speed_kmh": avg_speed_kmh,
            "raw": str(data)[:2000],  # trimmed for storage
        }
    except requests.RequestException as e:
        log.error(f"Request failed for segment {segment['id']}: {e}")
        return None


def fetch_segment_duration_with_retry(session: requests.Session, api_key: str, segment: dict, max_retries: int = 2) -> dict | None:
    """Calls the routing API directly (rather than reusing fetch_segment_duration)
    so we can inspect the raw status code and retry specifically on 429
    (rate limited) responses. Your 2GIS key appears to hit short,
    self-resolving rate limits (not the monthly quota) — a brief pause and
    retry avoids silently losing that segment's reading for this poll."""
    payload = {
        "points": [
            {"type": "stop", "lat": segment["start"]["lat"], "lon": segment["start"]["lon"]},
            {"type": "stop", "lat": segment["end"]["lat"], "lon": segment["end"]["lon"]},
        ],
        "locale": "en",
        "transport": "driving",
        "route_mode": "fastest",
        "traffic_mode": "jam",
    }
    for attempt in range(max_retries + 1):
        try:
            resp = session.post(config.ROUTING_URL, params={"key": api_key}, json=payload, timeout=15)
        except requests.RequestException as e:
            log.error(f"{segment['id']}: request failed: {e}")
            return None

        if resp.status_code == 429:
            if attempt < max_retries:
                wait = 5 * (attempt + 1)
                log.warning(f"{segment['id']}: rate limited (429), retrying in {wait}s (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait)
                continue
            log.error(f"{segment['id']}: still rate limited after {max_retries} retries, giving up for this poll")
            return None

        try:
            resp.raise_for_status()
        except requests.RequestException as e:
            log.error(f"{segment['id']}: request failed: {e}")
            return None

        data = resp.json()
        results = data.get("result") or []
        if not results:
            log.warning(f"No route returned for segment {segment['id']}")
            return None
        best = results[0]
        duration_sec = best.get("total_duration")
        distance_m = best.get("total_distance")
        avg_speed_kmh = None
        if duration_sec and distance_m and duration_sec > 0:
            avg_speed_kmh = (distance_m / 1000) / (duration_sec / 3600)
        return {
            "duration_sec": duration_sec,
            "distance_m": distance_m,
            "avg_speed_kmh": avg_speed_kmh,
            "raw": str(data)[:2000],
        }
    return None


def fetch_weather(session: requests.Session) -> dict | None:
    """Pull current weather for Astana from Open-Meteo (free, no key)."""
    params = {
        "latitude": config.ASTANA_LAT,
        "longitude": config.ASTANA_LON,
        "current": "temperature_2m,precipitation,snowfall,wind_speed_10m,weather_code",
        "timezone": "UTC",
    }
    try:
        resp = session.get(config.WEATHER_URL, params=params, timeout=15)
        resp.raise_for_status()
        current = resp.json().get("current", {})
        return {
            "temperature_c": current.get("temperature_2m"),
            "precipitation_mm": current.get("precipitation"),
            "snowfall_cm": current.get("snowfall"),
            "wind_speed_kmh": current.get("wind_speed_10m"),
            "weather_code": current.get("weather_code"),
        }
    except requests.RequestException as e:
        log.error(f"Weather request failed: {e}")
        return None


def poll_once(conn: sqlite3.Connection, api_key: str) -> None:
    session = requests.Session()
    timestamp = datetime.now(timezone.utc).isoformat()
    succeeded = 0
    failed = 0

    weather = fetch_weather(session)
    if weather:
        conn.execute(
            """INSERT INTO weather_readings
               (timestamp_utc, temperature_c, precipitation_mm, snowfall_cm, wind_speed_kmh, weather_code)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (timestamp, weather["temperature_c"], weather["precipitation_mm"],
             weather["snowfall_cm"], weather["wind_speed_kmh"], weather["weather_code"]),
        )

    for segment in config.SEGMENTS:
        result = fetch_segment_duration_with_retry(session, api_key, segment)
        if result:
            conn.execute(
                """INSERT INTO traffic_readings
                   (segment_id, segment_name, timestamp_utc, duration_sec, distance_m, avg_speed_kmh, raw_response)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (segment["id"], segment["name"], timestamp,
                 result["duration_sec"], result["distance_m"], result["avg_speed_kmh"], result["raw"]),
            )
            log.info(
                f"{segment['id']}: {result['duration_sec']}s, "
                f"{result['avg_speed_kmh']:.1f} km/h" if result["avg_speed_kmh"] else
                f"{segment['id']}: {result['duration_sec']}s"
            )
            succeeded += 1
        else:
            log.error(f"{segment['id']}: NO ROW SAVED this poll (see error above)")
            failed += 1
        # Slightly more spacing than before (was 0.5s) — with 8 segments now
        # instead of 4-5, tighter spacing was more likely to trip 2GIS's
        # short-term rate limit.
        time.sleep(1.5)

    conn.commit()
    if failed > 0:
        log.warning(f"Poll complete at {timestamp} \u2014 {succeeded} succeeded, {failed} FAILED (rows missing this cycle)")
    else:
        log.info(f"Poll complete at {timestamp} \u2014 all {succeeded} segments succeeded")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--loop", action="store_true", help="Poll continuously at the configured interval")
    args = parser.parse_args()

    api_key = get_api_key()
    conn = init_db(config.DB_PATH)

    if args.loop:
        interval_sec = config.POLL_INTERVAL_MINUTES * 60
        log.info(f"Starting continuous polling every {config.POLL_INTERVAL_MINUTES} min. Ctrl+C to stop.")
        try:
            while True:
                poll_once(conn, api_key)
                time.sleep(interval_sec)
        except KeyboardInterrupt:
            log.info("Stopped.")
    else:
        poll_once(conn, api_key)

    conn.close()


if __name__ == "__main__":
    main()
"""
