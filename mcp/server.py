from pathlib import Path
import sqlite3
from typing import List, Dict, Optional
from fastmcp import FastMCP
import os
import sys

DB_PATH = Path(__file__).parent.parent / "data" / "polar.db"

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

mcp = FastMCP("Marathon Polar")


def get_conn():
    if not DB_PATH.exists():
        raise FileNotFoundError(f"DB not found at {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@mcp.tool()
def get_recent_sessions(limit: int = 10) -> List[Dict]:
    """
    Return most recent sessions (runs) from SQLite.
    
    Args:
        limit: Number of sessions to return (1-100)
    """
    if limit < 1 or limit > 100:
        raise ValueError("limit must be between 1 and 100")
    
    try:
        conn = get_conn()
    except FileNotFoundError as e:
        raise ValueError(f"Database error: {e}")

    rows = conn.execute(
        """
        SELECT session_id, ts_start, ts_end, sport, 
            distance_m, duration_s, kcal, 
            avg_hr, max_hr, device, training_load
        FROM sessions
        ORDER BY ts_start DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    conn.close()

    return [
        {
            "session_id": r["session_id"],
            "ts_start": r["ts_start"],
            "ts_end": r["ts_end"],
            "sport": r["sport"],
            "distance_m": r["distance_m"],
            "duration_s": r["duration_s"],
            "kcal": r["kcal"],
            "avg_hr": r["avg_hr"],
            "max_hr": r["max_hr"],
            "device": r["device"],
            "training_load": r["training_load"],
        }
        for r in rows
    ]


@mcp.tool()
def get_recent_metrics(limit: int = 14) -> List[Dict]:
    """
    Return recent daily metrics (hrv, rhr, vo2, weight, sleep).
    
    Args:
        limit: Number of days to return (1-60)
    """
    if limit < 1 or limit > 60:
        raise ValueError("limit must be between 1 and 60")
    
    try:
        conn = get_conn()
    except FileNotFoundError as e:
        raise ValueError(f"Database error: {e}")

    rows = conn.execute(
        """
        SELECT date,
               resting_hr,
               hrv_rmssd,
               vo2max,
               weight_kg,
               sleep_hours
        FROM metrics
        ORDER BY date DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    conn.close()

    return [
        {
            "date": r["date"],
            "resting_hr": r["resting_hr"],
            "hrv_rmssd": r["hrv_rmssd"],
            "vo2max": r["vo2max"],
            "weight_kg": r["weight_kg"],
            "sleep_hours": r["sleep_hours"],
        }
        for r in rows
    ]


@mcp.tool()
def write_to_notion_running(
    week: str,
    status: str = "In Progress",
    weekly_goal: Optional[str] = None,
    progress_notes: Optional[str] = None,
    action_items: Optional[str] = None,
    distance_km: Optional[float] = None,
    sessions_count: Optional[int] = None,
    next_week_focus: Optional[str] = None,
    week_start_date: Optional[str] = None,
    database_id: Optional[str] = None,
    update_existing: bool = True,
) -> Dict:
    """
    Write running progress and coaching data to Notion running database.
    
    Creates a new page or updates existing page for the week.
    
    Args:
        week: Week identifier (e.g., "Week of 2025-11-04")
        status: Status - one of: "Not started", "In progress", "Done" (or "Planning", "In Progress", "Completed" which will be mapped)
        weekly_goal: Main goal for the week
        progress_notes: Progress updates and reflections
        action_items: Action items (comma-separated string or single item)
        distance_km: Total distance run this week in kilometers
        sessions_count: Number of running sessions this week
        next_week_focus: What to focus on next week
        week_start_date: Week start date (YYYY-MM-DD format)
        database_id: Notion database ID (optional, uses config if not provided)
        update_existing: If True, update existing page for this week; if False, create new
    
    Returns:
        Created or updated page data from Notion
    """
    try:
        from polar_etl.notion_running import (
            create_running_page,
            update_running_page,
            find_running_page_by_week,
        )
        # Import utils from accesslink-example-python
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent / "accesslink-example-python"))
        from utils import load_config
    except ImportError as e:
        raise ValueError(f"Could not import Notion modules: {e}")
    
    # Get database ID from config if not provided
    if not database_id:
        try:
            config_path = Path(__file__).parent.parent / "accesslink-example-python" / "config.yml"
            config = load_config(str(config_path))
            database_id = config.get("notion_running_db_id")
            if not database_id:
                raise ValueError(
                    "Notion running database ID not configured. "
                    "Set notion_running_db_id in config.yml or provide database_id parameter"
                )
        except Exception as e:
            raise ValueError(f"Could not load config: {e}")
    
    # Parse action_items if it's a string
    action_items_list = None
    if action_items:
        if isinstance(action_items, str):
            # Split by comma or newline
            action_items_list = [item.strip() for item in action_items.replace("\n", ",").split(",") if item.strip()]
        elif isinstance(action_items, list):
            action_items_list = action_items
    
    try:
        if update_existing:
            # Try to find existing page
            existing_page = find_running_page_by_week(database_id, week)
            if existing_page:
                # Update existing page
                result = update_running_page(
                    existing_page["id"],
                    status=status,
                    weekly_goal=weekly_goal,
                    progress_notes=progress_notes,
                    action_items=action_items_list,
                    distance_km=distance_km,
                    sessions_count=sessions_count,
                    next_week_focus=next_week_focus,
                )
                return {
                    "success": True,
                    "action": "updated",
                    "page_id": existing_page["id"],
                    "week": week,
                    "data": result,
                }
        
        # Create new page
        result = create_running_page(
            database_id,
            week=week,
            status=status,
            weekly_goal=weekly_goal,
            progress_notes=progress_notes,
            action_items=action_items_list,
            distance_km=distance_km,
            sessions_count=sessions_count,
            next_week_focus=next_week_focus,
            week_start_date=week_start_date,
        )
        return {
            "success": True,
            "action": "created",
            "page_id": result.get("id"),
            "week": week,
            "data": result,
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "week": week,
        }


if __name__ == "__main__":
    mcp.run()