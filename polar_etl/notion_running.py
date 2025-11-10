# polar_etl/notion_running.py
"""Write running progress and coaching data to Notion"""

import requests
from datetime import datetime
from typing import Dict, Optional, List

from polar_etl.notion_utils import (
    NOTION_API_VERSION,
    NOTION_BASE_URL,
    extract_property_value,
    fetch_notion_database,
    get_notion_headers,
)


def _normalize_status(status: str) -> str:
    """Normalize status to match Notion database options"""
    status_map = {
        "Planning": "Not started",
        "In Progress": "In progress",
        "Completed": "Done",
    }
    return status_map.get(status, status)


def create_running_page(
    database_id: str,
    week: str,
    status: str = "In progress",
    weekly_goal: Optional[str] = None,
    progress_notes: Optional[str] = None,
    action_items: Optional[List[str]] = None,
    distance_km: Optional[float] = None,
    sessions_count: Optional[int] = None,
    next_week_focus: Optional[str] = None,
    week_start_date: Optional[str] = None,
) -> Dict:
    """
    Create a new page in the Notion running database.
    
    Args:
        database_id: Notion database ID
        week: Week identifier (e.g., "Week of 2025-11-04")
        status: Status (Planning, In Progress, Completed)
        weekly_goal: Main goal for the week
        progress_notes: Progress updates and reflections
        action_items: List of action items/tasks
        distance_km: Total distance run this week
        sessions_count: Number of running sessions this week
        next_week_focus: What to focus on next week
        week_start_date: Week start date (YYYY-MM-DD)
    
    Returns:
        Created page data
    """
    url = f"{NOTION_BASE_URL}/pages"
    headers = get_notion_headers()
    
    # Build properties
    properties = {
        "Week": {
            "title": [
                {
                    "text": {
                        "content": week
                    }
                }
            ]
        },
        "Status": {
            "status": {
                "name": _normalize_status(status)
            }
        }
    }
    
    # Add optional fields
    if week_start_date:
        properties["Date"] = {
            "date": {
                "start": week_start_date
            }
        }
    
    if weekly_goal:
        properties["Weekly Goal"] = {
            "rich_text": [
                {
                    "text": {
                        "content": weekly_goal
                    }
                }
            ]
        }
    
    if progress_notes:
        properties["Progress Notes"] = {
            "rich_text": [
                {
                    "text": {
                        "content": progress_notes
                    }
                }
            ]
        }
    
    if action_items:
        if isinstance(action_items, list):
            # Use multi-select if multiple items, or rich_text if single
            if len(action_items) == 1:
                properties["Action Items"] = {
                    "rich_text": [
                        {
                            "text": {
                                "content": action_items[0]
                            }
                        }
                    ]
                }
            else:
                properties["Action Items"] = {
                    "multi_select": [
                        {"name": item} for item in action_items
                    ]
                }
        else:
            properties["Action Items"] = {
                "rich_text": [
                    {
                        "text": {
                            "content": str(action_items)
                        }
                    }
                ]
            }
    
    if distance_km is not None:
        properties["Distance This Week"] = {
            "number": float(distance_km)
        }
    
    if sessions_count is not None:
        properties["Sessions This Week"] = {
            "number": int(sessions_count)
        }
    
    if next_week_focus:
        properties["Next Week Focus"] = {
            "rich_text": [
                {
                    "text": {
                        "content": next_week_focus
                    }
                }
            ]
        }
    
    payload = {
        "parent": {
            "database_id": database_id
        },
        "properties": properties
    }
    
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()


def update_running_page(
    page_id: str,
    status: Optional[str] = None,
    weekly_goal: Optional[str] = None,
    progress_notes: Optional[str] = None,
    action_items: Optional[List[str]] = None,
    distance_km: Optional[float] = None,
    sessions_count: Optional[int] = None,
    next_week_focus: Optional[str] = None,
) -> Dict:
    """
    Update an existing page in the Notion running database.
    
    Args:
        page_id: Notion page ID to update
        status: Status (Planning, In Progress, Completed)
        weekly_goal: Main goal for the week
        progress_notes: Progress updates and reflections
        action_items: List of action items/tasks
        distance_km: Total distance run this week
        sessions_count: Number of running sessions this week
        next_week_focus: What to focus on next week
    
    Returns:
        Updated page data
    """
    url = f"{NOTION_BASE_URL}/pages/{page_id}"
    headers = get_notion_headers()
    
    properties = {}
    
    if status:
        properties["Status"] = {
            "status": {
                "name": _normalize_status(status)
            }
        }
    
    if weekly_goal:
        properties["Weekly Goal"] = {
            "rich_text": [
                {
                    "text": {
                        "content": weekly_goal
                    }
                }
            ]
        }
    
    if progress_notes:
        properties["Progress Notes"] = {
            "rich_text": [
                {
                    "text": {
                        "content": progress_notes
                    }
                }
            ]
        }
    
    if action_items:
        if isinstance(action_items, list):
            if len(action_items) == 1:
                properties["Action Items"] = {
                    "rich_text": [
                        {
                            "text": {
                                "content": action_items[0]
                            }
                        }
                    ]
                }
            else:
                properties["Action Items"] = {
                    "multi_select": [
                        {"name": item} for item in action_items
                    ]
                }
        else:
            properties["Action Items"] = {
                "rich_text": [
                    {
                        "text": {
                            "content": str(action_items)
                        }
                    }
                ]
            }
    
    if distance_km is not None:
        properties["Distance This Week"] = {
            "number": float(distance_km)
        }
    
    if sessions_count is not None:
        properties["Sessions This Week"] = {
            "number": int(sessions_count)
        }
    
    if next_week_focus:
        properties["Next Week Focus"] = {
            "rich_text": [
                {
                    "text": {
                        "content": next_week_focus
                    }
                }
            ]
        }
    
    if not properties:
        raise ValueError("At least one property must be provided for update")
    
    payload = {
        "properties": properties
    }
    
    response = requests.patch(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()


def find_running_page_by_week(database_id: str, week: str) -> Optional[Dict]:
    """Find a page by week name"""
    pages = fetch_notion_database(database_id)
    for page in pages:
        properties = page.get("properties", {})
        week_prop = properties.get("Week")
        if week_prop:
            week_type = week_prop.get("type")
            week_title = extract_property_value(week_prop, week_type)
            if week_title == week:
                return page
    return None

