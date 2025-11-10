# polar_etl/run.py
"""Headless ETL script to fetch and store Polar data"""

from datetime import datetime
from pathlib import Path
import sys
import os

# Add accesslink-example-python to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "accesslink-example-python"))

from utils import load_config  # type: ignore
from accesslink import AccessLink  # type: ignore

from polar_etl.db import get_conn, upsert_session, upsert_metrics
from polar_etl.normalize import normalize_exercise, is_fitness_test, parse_fitness_test

CONFIG_FILENAME = "accesslink-example-python/config.yml"
TOKEN_FILENAME = "accesslink-example-python/usertokens.yml"

# Redirect URL for OAuth (same as example web app)
CALLBACK_PORT = 8000
CALLBACK_ENDPOINT = "/oauth2_callback"
REDIRECT_URL = f"http://localhost:{CALLBACK_PORT}{CALLBACK_ENDPOINT}"


def _extract_date(value: str) -> str | None:
    if not value:
        return None
    trimmed = value.strip()
    if not trimmed:
        return None
    # Handle timestamps with optional timezone suffix
    normalized = trimmed.replace("Z", "")
    try:
        return datetime.fromisoformat(normalized).date().isoformat()
    except ValueError:
        return trimmed[:10]


def _propagate_latest_metric(conn, column: str, param_name: str):
    latest_row = conn.execute(
        f"SELECT date, {column} FROM metrics ORDER BY date DESC LIMIT 1"
    ).fetchone()
    if not latest_row:
        return

    latest_date, latest_value = latest_row
    if latest_value is not None:
        return

    source_row = conn.execute(
        f"SELECT {column} FROM metrics WHERE {column} IS NOT NULL ORDER BY date DESC LIMIT 1"
    ).fetchone()

    if not source_row:
        return

    value = source_row[0]
    if value is None:
        return

    upsert_metrics(conn, latest_date, **{param_name: value})


def sync_physical_info(accesslink: AccessLink, tokens):
    """Pull latest physical information (weight, VO2, resting HR) into metrics table."""
    with get_conn() as conn:
        for item in tokens:
            if not item:
                continue

            access_token = item.get("access_token")
            user_id = item.get("user_id")
            if not access_token or not user_id:
                continue

            processed = False
            try:
                transaction = accesslink.physical_info.create_transaction(
                    user_id=user_id, access_token=access_token
                )
            except Exception as e:
                print(f"Warning: Could not create physical info transaction for user {user_id}: {e}")
                transaction = None

            if transaction:
                try:
                    info_listing = transaction.list_physical_infos() or {}
                    urls = info_listing.get("physical-informations", [])
                    for url in urls:
                        try:
                            info = transaction.get_physical_info(url)
                        except Exception as info_err:
                            print(f"Warning: Could not fetch physical info from {url}: {info_err}")
                            continue

                        date_str = _extract_date(info.get("created"))
                        weight = info.get("weight")
                        resting_hr = info.get("resting-heart-rate")
                        vo2 = info.get("vo2-max")

                        if not date_str:
                            continue

                        upsert_metrics(
                            conn,
                            date_str,
                            resting_hr=resting_hr,
                            vo2max=vo2,
                            weight_kg=weight,
                        )
                        processed = True
                finally:
                    try:
                        transaction.commit()
                    except Exception as e:
                        print(f"Warning: Could not commit physical info transaction for user {user_id}: {e}")

            if not processed:
                # Fallback to ensure latest metrics row has weight if available
                try:
                    user_info = accesslink.users.get_information(user_id=user_id, access_token=access_token)
                except Exception as e:
                    print(f"Warning: Could not fetch user info for user {user_id}: {e}")
                    continue

                weight = user_info.get("weight")
                if weight is None:
                    continue

                cur = conn.execute(
                    "SELECT date, weight_kg FROM metrics ORDER BY date DESC LIMIT 1"
                )
                row = cur.fetchone()
                if not row:
                    continue
                latest_date, latest_weight = row
                try:
                    latest_weight_val = float(latest_weight) if latest_weight is not None else None
                except (TypeError, ValueError):
                    latest_weight_val = None

                if latest_weight_val is None or latest_weight_val != float(weight):
                    upsert_metrics(conn, latest_date, weight_kg=weight)

        # Ensure the latest row has values if prior measurements exist
        for column, param in (
            ("weight_kg", "weight_kg"),
            ("resting_hr", "resting_hr"),
            ("vo2max", "vo2max"),
        ):
            _propagate_latest_metric(conn, column, param)


def main():
    cfg = load_config(CONFIG_FILENAME)
    tokens = load_config(TOKEN_FILENAME).get("tokens", [])

    accesslink = AccessLink(
        client_id=cfg["client_id"],
        client_secret=cfg["client_secret"],
        redirect_url=REDIRECT_URL,
    )

    with get_conn() as conn:
        # Fetch and store Polar exercise data
        for item in tokens:
            if not item:
                continue
            access_token = item["access_token"]

            exercises = accesslink.get_exercises(access_token=access_token)
            for ex in exercises:
                if is_fitness_test(ex):
                    d, rhr, rmssd, vo2 = parse_fitness_test(ex)
                    if d:
                        upsert_metrics(conn, d, resting_hr=rhr, hrv_rmssd=rmssd, vo2max=vo2)
                else:
                    s = normalize_exercise(ex)
                    if s["session_id"]:
                        upsert_session(conn, s)
        
        conn.commit()
    
    sync_physical_info(accesslink, tokens)


if __name__ == "__main__":
    main()

