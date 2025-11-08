# polar_etl/notion_sleep.py
"""Fetch sleep data from Notion and sync to local database"""

import os
import re
import requests
from datetime import datetime
from typing import List, Dict, Optional
from polar_etl.db import get_conn, upsert_metrics

# Notion API configuration
NOTION_API_VERSION = "2022-06-28"
NOTION_BASE_URL = "https://api.notion.com/v1"

# Internal Integration Secret - set via NOTION_SECRET environment variable
NOTION_SECRET = os.getenv("NOTION_SECRET", "")

# Database ID - extract from Notion URL (the part between / and ?)
# Example: https://www.notion.so/workspace/DATABASE_ID?v=...
NOTION_DATABASE_ID = None  # Will be set via environment or config


def get_notion_headers():
    """Get headers for Notion API requests"""
    secret = os.getenv("NOTION_SECRET", NOTION_SECRET)
    if not secret:
        raise ValueError(
            "NOTION_SECRET not configured. Set NOTION_SECRET environment variable "
            "or update notion_sleep.py/notion_running.py with your secret."
        )
    return {
        "Authorization": f"Bearer {secret}",
        "Notion-Version": NOTION_API_VERSION,
        "Content-Type": "application/json",
    }


def parse_time_to_hours(time_str: str) -> Optional[float]:
    """Parse a variety of duration formats (HH:MM, 6h 30m, 6.5, etc.) into decimal hours."""
    if not time_str:
        return None

    raw_value = time_str
    time_str = time_str.strip()
    if not time_str:
        return None

    normalized = time_str.lower().replace(",", ".")

    # HH:MM[:SS] formats
    colon_match = re.match(r"^(?P<h>\d{1,2}):(?P<m>\d{1,2})(?::(?P<s>\d{1,2}))?$", normalized)
    if colon_match:
        hours = int(colon_match.group("h"))
        minutes = int(colon_match.group("m"))
        seconds = int(colon_match.group("s")) if colon_match.group("s") else 0
        return hours + minutes / 60.0 + seconds / 3600.0

    # Pure decimal representation (e.g. "6.5")
    if re.fullmatch(r"\d+(?:\.\d+)?", normalized):
        try:
            return float(normalized)
        except ValueError:
            pass

    # Compact forms like "6h30m" or "7h15"
    compact = re.sub(r"\s+", "", normalized)
    compact_match = re.match(r"^(?P<h>\d+)(?:h(?P<m>\d{1,2})?)?(?:m(?P<mm>\d{1,2})?)?$", compact)
    if compact_match:
        hours = int(compact_match.group("h"))
        minutes = compact_match.group("m") or compact_match.group("mm")
        minutes_val = int(minutes) if minutes else 0
        return hours + minutes_val / 60.0

    # Textual tokens like "6 h 30 m" or "6 hours 15 minutes"
    total_hours = 0.0
    found = False
    for value, unit in re.findall(r"(\d+(?:\.\d+)?)\s*(h|hr|hrs|hour|hours|m|min|mins|minute|minutes|s|sec|secs|second|seconds)", normalized):
        try:
            number = float(value)
        except ValueError:
            continue
        unit = unit[0]  # h, m, or s
        if unit == "h":
            total_hours += number
        elif unit == "m":
            total_hours += number / 60.0
        elif unit == "s":
            total_hours += number / 3600.0
        found = True
    if found and total_hours > 0:
        return total_hours

    # Fallback: attempt to extract the first floating point number
    generic_number = re.search(r"\d+(?:\.\d+)?", normalized)
    if generic_number:
        try:
            return float(generic_number.group(0))
        except ValueError:
            pass

    print(f"Warning: Could not parse sleep duration value '{raw_value}'")
    return None


def extract_property_value(prop: Dict, prop_type: str) -> Optional[any]:
    """Extract value from Notion property based on type"""
    if prop_type == "title":
        return "".join([text.get("plain_text", "") for text in prop.get("title", [])])
    elif prop_type == "rich_text":
        return "".join([text.get("plain_text", "") for text in prop.get("rich_text", [])])
    elif prop_type == "number":
        return prop.get("number")
    elif prop_type == "date":
        date_obj = prop.get("date")
        if date_obj:
            return date_obj.get("start")  # Returns YYYY-MM-DD format
        return None
    elif prop_type == "checkbox":
        return prop.get("checkbox", False)
    elif prop_type == "formula":
        formula = prop.get("formula")
        if formula:
            formula_type = formula.get("type")
            if formula_type == "number":
                return formula.get("number")
            elif formula_type == "string":
                return formula.get("string")
    return None


def fetch_notion_database(database_id: str) -> List[Dict]:
    """Fetch all pages from a Notion database"""
    url = f"{NOTION_BASE_URL}/databases/{database_id}/query"
    headers = get_notion_headers()
    
    all_pages = []
    has_more = True
    start_cursor = None
    
    while has_more:
        payload = {}
        if start_cursor:
            payload["start_cursor"] = start_cursor
        
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        data = response.json()
        all_pages.extend(data.get("results", []))
        
        has_more = data.get("has_more", False)
        start_cursor = data.get("next_cursor")
    
    return all_pages


def parse_sleep_page(page: Dict, date_field: str = "Date", sleep_field: str = "Sleep Hours") -> Optional[Dict]:
    """Parse a Notion page to extract sleep data"""
    properties = page.get("properties", {})
    
    # Get date
    date_prop = properties.get(date_field)
    if not date_prop:
        return None
    
    date_type = date_prop.get("type")
    date_value = extract_property_value(date_prop, date_type)
    
    if not date_value:
        return None
    
    # Extract date in YYYY-MM-DD format
    if isinstance(date_value, str):
        # If it's a datetime string, extract just the date part
        if "T" in date_value:
            date_value = date_value.split("T")[0]
        date_str = date_value[:10]  # Take first 10 chars (YYYY-MM-DD)
    else:
        return None
    
    # Get sleep hours - can be from number field or time string in title/rich_text
    sleep_prop = properties.get(sleep_field)
    sleep_hours = None
    if sleep_prop:
        sleep_type = sleep_prop.get("type")
        sleep_value = extract_property_value(sleep_prop, sleep_type)
        
        if sleep_value is not None:
            # If it's already a number, use it directly
            if isinstance(sleep_value, (int, float)):
                sleep_hours = float(sleep_value)
            # If it's a string (like "06:19"), parse it as time
            elif isinstance(sleep_value, str):
                sleep_hours = parse_time_to_hours(sleep_value)
    
    return {
        "page_id": page.get("id"),
        "date": date_str,
        "sleep_hours": sleep_hours,
    }


def update_notion_checkbox(page_id: str, property_name: str = "Synced to ETL", checked: bool = True):
    """Update a checkbox property in a Notion page"""
    url = f"{NOTION_BASE_URL}/pages/{page_id}"
    headers = get_notion_headers()
    
    payload = {
        "properties": {
            property_name: {
                "checkbox": checked
            }
        }
    }
    
    response = requests.patch(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()


def sync_notion_sleep_to_db(database_id: str, date_field: str = "Date", 
                            sleep_field: str = "Sleep Hours", 
                            synced_field: str = "Synced to ETL"):
    """Fetch sleep data from Notion and sync to local database"""
    print(f"Fetching sleep data from Notion database: {database_id}")
    
    # Fetch all pages from Notion
    pages = fetch_notion_database(database_id)
    print(f"Found {len(pages)} pages in Notion database")
    
    conn = get_conn()
    synced_count = 0
    error_count = 0
    
    try:
        for page in pages:
            try:
                # Parse sleep data from page
                sleep_data = parse_sleep_page(page, date_field, sleep_field)
                
                if not sleep_data or not sleep_data.get("date"):
                    continue
                
                date = sleep_data["date"]
                sleep_hours = sleep_data.get("sleep_hours")
                page_id = sleep_data["page_id"]
                
                # Update database with sleep hours
                if sleep_hours is not None:
                    upsert_metrics(conn, date, sleep_hours=sleep_hours)
                    print(f"Updated sleep data for {date}: {sleep_hours} hours")
                else:
                    print(f"Skipping {date}: no sleep hours data (value: {sleep_value})")
                
                # Check if already synced
                properties = page.get("properties", {})
                synced_prop = properties.get(synced_field)
                if synced_prop:
                    synced_type = synced_prop.get("type")
                    is_synced = extract_property_value(synced_prop, synced_type)
                    
                    # Update checkbox if not already synced
                    if not is_synced:
                        try:
                            update_notion_checkbox(page_id, synced_field, True)
                            print(f"Marked {date} as synced in Notion")
                        except Exception as e:
                            print(f"Warning: Could not update checkbox for {date}: {e}")
                
                synced_count += 1
                
            except Exception as e:
                error_count += 1
                print(f"Error processing page {page.get('id', 'unknown')}: {e}")
                continue
        
        conn.commit()
        print(f"\nSync complete: {synced_count} pages processed, {error_count} errors")
        
    finally:
        conn.close()


if __name__ == "__main__":
    # For testing - database ID should be provided
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m polar_etl.notion_sleep <database_id>")
        print("Database ID can be extracted from Notion URL")
        sys.exit(1)
    
    database_id = sys.argv[1]
    sync_notion_sleep_to_db(database_id)

