# polar_etl/db.py
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "polar.db"


def get_conn():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def upsert_session(conn, s):
    conn.execute(
        """
    INSERT INTO sessions (session_id, ts_start, ts_end, sport,
                          distance_m, duration_s, kcal, avg_hr, max_hr,
                          device, training_load)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(session_id) DO UPDATE SET
      ts_start=excluded.ts_start,
      ts_end=excluded.ts_end,
      sport=excluded.sport,
      distance_m=excluded.distance_m,
      duration_s=excluded.duration_s,
      kcal=excluded.kcal,
      avg_hr=excluded.avg_hr,
      max_hr=excluded.max_hr,
      device=excluded.device,
      training_load=excluded.training_load
    """,
        (
            s["session_id"],
            s["ts_start"],
            s["ts_end"],
            s["sport"],
            s["distance_m"],
            s["duration_s"],
            s["kcal"],
            s["avg_hr"],
            s["max_hr"],
            s["device"],
            s["training_load"],
        ),
    )


def upsert_metrics(conn, date, resting_hr=None, hrv_rmssd=None, vo2max=None, weight_kg=None, sleep_hours=None):
    # Build the update clause dynamically to only update non-None fields
    updates = []
    insert_params = [date, resting_hr, hrv_rmssd, vo2max, weight_kg, sleep_hours]
    update_params = []
    
    if resting_hr is not None:
        updates.append("resting_hr=?")
        update_params.append(resting_hr)
    if hrv_rmssd is not None:
        updates.append("hrv_rmssd=?")
        update_params.append(hrv_rmssd)
    if vo2max is not None:
        updates.append("vo2max=?")
        update_params.append(vo2max)
    if weight_kg is not None:
        updates.append("weight_kg=?")
        update_params.append(weight_kg)
    if sleep_hours is not None:
        updates.append("sleep_hours=?")
        update_params.append(sleep_hours)
    
    if not updates:
        # If no fields to update, just insert the date (or do nothing on conflict)
        conn.execute(
            """
            INSERT INTO metrics (date) VALUES (?)
            ON CONFLICT(date) DO NOTHING
            """,
            (date,),
        )
        return
    
    # Build the full query
    update_clause = ", ".join(updates)
    query = f"""
    INSERT INTO metrics (date, resting_hr, hrv_rmssd, vo2max, weight_kg, sleep_hours)
    VALUES (?, ?, ?, ?, ?, ?)
    ON CONFLICT(date) DO UPDATE SET
      {update_clause}
    """
    conn.execute(query, insert_params + update_params)
