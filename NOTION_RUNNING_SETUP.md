# Notion Running Database Setup

## Database Structure

The running progress/coaching database should have the following structure:

### Properties (Fields)

1. **Week** (Title) - Primary field
   - Format: "Week of 2025-11-04" or similar
   - This is the unique identifier for each week

2. **Date** (Date)
   - Week start date
   - Format: YYYY-MM-DD

3. **Status** (Select)
   - Options: "Planning", "In Progress", "Completed"
   - Colors: Blue, Yellow, Green respectively

4. **Weekly Goal** (Rich Text)
   - Main goal for the week
   - Free-form text

5. **Progress Notes** (Rich Text)
   - Updates and reflections throughout the week
   - Free-form text

6. **Action Items** (Multi-select)
   - Specific tasks/action items for the week
   - Can have multiple items selected

7. **Distance This Week** (Number)
   - Total distance run in kilometers
   - Format: Number (e.g., 25.5)

8. **Sessions This Week** (Number)
   - Count of running sessions
   - Format: Number (e.g., 4)

9. **Next Week Focus** (Rich Text)
   - What to focus on next week
   - Free-form text

## Setup Options

### Option 1: Create Database Manually

1. Create a new page in Notion
2. Type `/database` and select "Table - Inline"
3. Name it "Running Progress & Coaching"
4. Add the properties listed above with the correct types
5. For Status, add the three options: Planning, In Progress, Completed
6. Share the database with your Notion integration
7. Copy the database ID from the URL and add to config.yml:
   ```yaml
   notion_running_db_id: <your-database-id>
   ```

### Option 2: Use the Helper Script

1. Create a new page in Notion (or use an existing page)
2. Copy the page ID from the URL (32-char hex string)
3. Run:
   ```bash
   cd /Users/vianar/Projects/mcp/marathon_polar
   source venv/bin/activate
   python -m polar_etl.create_notion_running_db <page_id>
   ```
4. The script will create the database and show you the ID to add to config.yml

## Using the MCP Tool

Once the database is set up, you can use the MCP tool `write_to_notion_running` to:

- Create new weekly entries
- Update existing weekly entries
- Set goals, progress notes, action items
- Track distance and session counts

Example usage:
```python
write_to_notion_running(
    week="Week of 2025-11-04",
    status="In Progress",
    weekly_goal="Run 25km this week",
    progress_notes="Great start! 3 runs completed.",
    action_items="Long run Saturday, Easy run Monday, Tempo run Wednesday",
    distance_km=15.5,
    sessions_count=3,
    next_week_focus="Increase volume to 30km"
)
```

