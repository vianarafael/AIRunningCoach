#!/usr/bin/env python
"""Debug script to inspect Notion database structure"""

import sys
from polar_etl.notion_sleep import fetch_notion_database, extract_property_value

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m polar_etl.debug_notion <database_id>")
        sys.exit(1)
    
    database_id = sys.argv[1]
    pages = fetch_notion_database(database_id)
    
    print(f"Found {len(pages)} pages\n")
    
    if pages:
        # Inspect first page to see all properties
        first_page = pages[0]
        properties = first_page.get("properties", {})
        
        print("Available properties in database:")
        print("=" * 60)
        for prop_name, prop_data in properties.items():
            prop_type = prop_data.get("type", "unknown")
            value = extract_property_value(prop_data, prop_type)
            print(f"\n{prop_name}:")
            print(f"  Type: {prop_type}")
            print(f"  Value: {value}")
            print(f"  Raw: {prop_data}")
        
        print("\n" + "=" * 60)
        print("\nAll pages:")
        for i, page in enumerate(pages, 1):
            props = page.get("properties", {})
            print(f"\nPage {i}:")
            for prop_name, prop_data in props.items():
                prop_type = prop_data.get("type", "unknown")
                value = extract_property_value(prop_data, prop_type)
                print(f"  {prop_name} ({prop_type}): {value}")

