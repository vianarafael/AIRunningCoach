#!/usr/bin/env python
"""Test script to verify Notion integration and extract database ID"""

import sys
import re

from polar_etl.notion_utils import NOTION_BASE_URL, get_notion_headers

def extract_database_id_from_url(url: str) -> str:
    """Extract database ID from Notion URL"""
    # Pattern: https://www.notion.so/workspace/DATABASE_ID?v=...
    # or: https://www.notion.so/DATABASE_ID?v=...
    match = re.search(r'notion\.so/(?:[^/]+/)?([a-f0-9]{32})', url)
    if match:
        db_id = match.group(1)
        # Format as UUID with hyphens
        return f"{db_id[:8]}-{db_id[8:12]}-{db_id[12:16]}-{db_id[16:20]}-{db_id[20:]}"
    return None

def test_notion_connection():
    """Test connection to Notion API"""
    import requests
    
    # Test with a simple API call
    url = f"{NOTION_BASE_URL}/users/me"
    headers = get_notion_headers()
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        user_info = response.json()
        print(f"✓ Successfully connected to Notion API")
        print(f"  User: {user_info.get('name', 'Unknown')}")
        return True
    except Exception as e:
        print(f"✗ Failed to connect to Notion API: {e}")
        return False

def list_databases():
    """List accessible databases (requires search API)"""
    import requests
    
    url = f"{NOTION_BASE_URL}/search"
    headers = get_notion_headers()
    
    payload = {
        "filter": {
            "value": "database",
            "property": "object"
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        results = response.json().get("results", [])
        
        print(f"\nFound {len(results)} accessible databases:")
        for db in results:
            title = "Untitled"
            if "title" in db:
                title_parts = db["title"]
                if isinstance(title_parts, list) and len(title_parts) > 0:
                    title = title_parts[0].get("plain_text", "Untitled")
            
            db_id = db.get("id", "")
            print(f"  - {title}")
            print(f"    ID: {db_id}")
            print(f"    URL: https://www.notion.so/{db_id.replace('-', '')}")
            print()
    except Exception as e:
        print(f"Could not list databases: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Extract database ID from URL if provided
        url = sys.argv[1]
        db_id = extract_database_id_from_url(url)
        if db_id:
            print(f"Extracted database ID: {db_id}")
            print(f"\nAdd this to your config.yml:")
            print(f"notion_running_db_id: {db_id}")
            print(f"\nOr set environment variable:")
            print(f"export NOTION_RUNNING_DB_ID={db_id}")
        else:
            print("Could not extract database ID from URL")
            print("Please provide the database ID directly (32-char hex string)")
    else:
        print("Notion Integration Test")
        print("=" * 50)
        
        # Test connection
        if test_notion_connection():
            print("\n" + "=" * 50)
            print("\nTo get your database ID:")
            print("1. Open your target Notion database (e.g., running tracker)")
            print("2. Copy the URL from your browser")
            print("3. Run: python -m polar_etl.test_notion <notion_url>")
            print("\nOr list all accessible databases:")
            list_databases()

