#!/usr/bin/env python
"""
Helper script to create a Notion database for running progress/coaching.
This script will create a database with the proper structure.

Usage:
    python -m polar_etl.create_notion_running_db [parent_page_id]

If parent_page_id is not provided, it will create the database in your workspace root.
"""

import sys
import requests
from pathlib import Path
from polar_etl.notion_sleep import get_notion_headers, NOTION_BASE_URL

import os
NOTION_SECRET = os.getenv("NOTION_SECRET", "")


def create_running_database(parent_page_id: str = None) -> dict:
    """
    Create a Notion database for running progress and coaching.
    
    Database structure:
    - Week (Title) - Week identifier
    - Date (Date) - Week start date
    - Status (Select) - Planning, In Progress, Completed
    - Weekly Goal (Rich Text) - Main goal for the week
    - Progress Notes (Rich Text) - Updates and reflections
    - Action Items (Multi-select) - Specific tasks
    - Distance This Week (Number) - Total km
    - Sessions This Week (Number) - Count of runs
    - Next Week Focus (Rich Text) - What to focus on next week
    """
    url = f"{NOTION_BASE_URL}/databases"
    headers = get_notion_headers()
    
    # Parent - use provided page or workspace root
    if parent_page_id:
        parent = {"page_id": parent_page_id}
    else:
        # Will create in workspace root (requires page_id in parent)
        raise ValueError("Please provide a parent_page_id. Create a page in Notion first, then use its ID.")
    
    properties = {
        "Week": {
            "title": {}
        },
        "Date": {
            "date": {}
        },
        "Status": {
            "select": {
                "options": [
                    {"name": "Planning", "color": "blue"},
                    {"name": "In Progress", "color": "yellow"},
                    {"name": "Completed", "color": "green"},
                ]
            }
        },
        "Weekly Goal": {
            "rich_text": {}
        },
        "Progress Notes": {
            "rich_text": {}
        },
        "Action Items": {
            "multi_select": {}
        },
        "Distance This Week": {
            "number": {
                "format": "number"
            }
        },
        "Sessions This Week": {
            "number": {
                "format": "number"
            }
        },
        "Next Week Focus": {
            "rich_text": {}
        },
    }
    
    payload = {
        "parent": parent,
        "title": [
            {
                "type": "text",
                "text": {
                    "content": "Running Progress & Coaching"
                }
            }
        ],
        "properties": properties,
    }
    
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    print("=" * 60)
    print("Notion Running Database Creator")
    print("=" * 60)
    print()
    print("This script will create a Notion database for running progress.")
    print()
    print("STEPS:")
    print("1. Create a new page in Notion (or use an existing page)")
    print("2. Copy the page ID from the URL")
    print("   (The part between notion.so/ and ? or the 32-char hex string)")
    print("3. Run this script with the page ID:")
    print("   python -m polar_etl.create_notion_running_db <page_id>")
    print()
    
    if len(sys.argv) > 1:
        parent_id = sys.argv[1]
        # Format as UUID if needed
        if len(parent_id) == 32 and '-' not in parent_id:
            parent_id = f"{parent_id[:8]}-{parent_id[8:12]}-{parent_id[12:16]}-{parent_id[16:20]}-{parent_id[20:]}"
        
        try:
            result = create_running_database(parent_id)
            db_id = result.get("id", "").replace("-", "")
            
            print("✓ Database created successfully!")
            print()
            print(f"Database ID: {db_id}")
            print(f"URL: https://www.notion.so/{db_id}")
            print()
            print("Add this to your config.yml:")
            print(f"notion_running_db_id: {db_id}")
            print()
        except Exception as e:
            print(f"✗ Error creating database: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("Please provide a parent page ID as an argument.")
        print("Example: python -m polar_etl.create_notion_running_db abc123def456...")

