# polar_etl/normalize.py
"""Functions to normalize Polar exercise data into database format"""

import re
from datetime import datetime, timedelta


def parse_duration(duration_str):
    """Convert ISO 8601 duration (e.g. PT1H5M12S) to seconds"""
    if not duration_str:
        return None

    # ISO 8601 duration pattern supporting days, hours, minutes, seconds
    match = re.match(
        r"^P(?:(?P<days>\d+)D)?"
        r"T(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+(?:\.\d+)?)S)?$",
        duration_str,
    )

    if not match:
        return None

    days = int(match.group("days")) if match.group("days") else 0
    hours = int(match.group("hours")) if match.group("hours") else 0
    minutes = int(match.group("minutes")) if match.group("minutes") else 0
    seconds = float(match.group("seconds")) if match.group("seconds") else 0.0

    total_seconds = seconds
    total_seconds += minutes * 60
    total_seconds += hours * 3600
    total_seconds += days * 86400

    return total_seconds


def is_fitness_test(ex):
    """Check if an exercise entry is a fitness test"""
    tt = (ex.get("test") or {}).get("type") or ex.get("test_type")
    return tt and tt.upper() in ("FITNESS_TEST", "ORTHOSTATIC_TEST")


def parse_fitness_test(ex):
    """Parse fitness test data from exercise entry"""
    date = ex.get("start_time", "")[:10]
    rhr = (ex.get("heart_rate") or {}).get("average")
    rmssd = (ex.get("heart_rate_variability") or {}).get("rmssd")
    vo2 = ex.get("vo2max")
    return date, rhr, rmssd, vo2


def normalize_exercise(ex):
    """Normalize a Polar exercise into sessions table format"""
    # adapt keys to what Polar returns in your payload
    session_id = (
        ex.get("id")
        or ex.get("list_item_id")
        or ex.get("transaction-id")
        or ex.get("url", "").split("/")[-1]
    )
    hr = ex.get("heart_rate") or {}
    
    # Extract training load from nested structure or top-level
    training_load = (
        ex.get("training_load")
        or (ex.get("training_load_pro") or {}).get("cardio-load")
    )
    
    # Parse duration from ISO 8601 format
    duration_raw = ex.get("duration")
    duration_s = parse_duration(duration_raw) if duration_raw else None
    
    # Calculate end time from start + duration
    ts_start = ex.get("start_time")
    ts_end = None
    if ts_start and duration_s:
        try:
            # Parse start time and add duration
            start_dt = datetime.fromisoformat(ts_start.replace('T', ' '))
            end_dt = start_dt + timedelta(seconds=duration_s)
            ts_end = end_dt.isoformat()
        except:
            pass
    
    return {
        "session_id": session_id,
        "ts_start": ts_start,
        "ts_end": ts_end,
        "sport": ex.get("sport", "UNKNOWN"),
        "distance_m": ex.get("distance", 0.0),
        "duration_s": float(duration_s) if duration_s is not None else 0.0,
        "kcal": ex.get("calories", 0.0),
        "avg_hr": hr.get("average"),
        "max_hr": hr.get("maximum") or hr.get("max"),  # handle both field names
        "device": ex.get("device", "Polar"),
        "training_load": training_load,
    }

