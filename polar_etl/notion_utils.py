"""Shared helpers for interacting with the Notion API."""

import os
from typing import Dict, List, Optional

import requests
from dotenv import load_dotenv

# Load environment variables from .env if present (for NOTION_SECRET, etc.)
load_dotenv()

NOTION_API_VERSION = "2022-06-28"
NOTION_BASE_URL = "https://api.notion.com/v1"


def _get_secret() -> str:
    secret = os.getenv("NOTION_SECRET", "")
    if not secret:
        raise ValueError(
            "NOTION_SECRET not configured. Set NOTION_SECRET environment variable "
            "or update your configuration with the Notion integration secret."
        )
    return secret


def get_notion_headers() -> Dict[str, str]:
    """Return the standard headers required for Notion API requests."""
    secret = _get_secret()
    return {
        "Authorization": f"Bearer {secret}",
        "Notion-Version": NOTION_API_VERSION,
        "Content-Type": "application/json",
    }


def fetch_notion_database(database_id: str) -> List[Dict]:
    """Fetch all pages from a Notion database."""
    url = f"{NOTION_BASE_URL}/databases/{database_id}/query"
    headers = get_notion_headers()

    all_pages: List[Dict] = []
    has_more = True
    start_cursor: Optional[str] = None

    while has_more:
        payload: Dict[str, str] = {}
        if start_cursor:
            payload["start_cursor"] = start_cursor

        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()

        data = response.json()
        all_pages.extend(data.get("results", []))

        has_more = data.get("has_more", False)
        start_cursor = data.get("next_cursor")

    return all_pages


def extract_property_value(prop: Dict, prop_type: str) -> Optional[any]:
    """Extract a usable value from a Notion property based on its type."""
    if prop_type == "title":
        return "".join([text.get("plain_text", "") for text in prop.get("title", [])])
    if prop_type == "rich_text":
        return "".join([text.get("plain_text", "") for text in prop.get("rich_text", [])])
    if prop_type == "number":
        return prop.get("number")
    if prop_type == "date":
        date_obj = prop.get("date")
        if date_obj:
            return date_obj.get("start")
        return None
    if prop_type == "checkbox":
        return prop.get("checkbox", False)
    if prop_type == "formula":
        formula = prop.get("formula")
        if formula:
            formula_type = formula.get("type")
            if formula_type == "number":
                return formula.get("number")
            if formula_type == "string":
                return formula.get("string")
    return None

