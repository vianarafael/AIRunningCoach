# AI Running Coach - Fitness Data ETL & MCP Server

A simple system for syncing Polar fitness data and optionally updating a Notion running database, with an MCP (Model Context Protocol) server for easy access.

## Features

- **Polar API Integration**: Automatically syncs exercise sessions and fitness test data from Polar Flow
- **Notion Integration**: Writes running progress/coaching data to Notion
- **Daily ETL**: Automated daily data extraction via cron jobs
- **MCP Server**: FastMCP server exposing your fitness data via standardized tools
- **Database Backups**: Automated daily database backups

## Prerequisites

- Python 3.12+
- A Polar device (I used the Polar H10)
- Polar Flow account with API access
- Notion account with Internal Integration
- A MCP client (I used Cursor)


## Quick Start

> **For detailed setup instructions, see [SETUP.md](SETUP.md)**

### 1. Clone and Setup

```bash
git clone https://github.com/vianarafael/ai-running-coach.git
cd ai-running-coach
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Polar API

1. Get your Polar API credentials [Polar AccessLink API Docs](https://www.polar.com/accesslink-api)
2. Copy the example config:
   ```bash
   cp accesslink-example-python/config.yml.example accesslink-example-python/config.yml
   ```
3. Edit `accesslink-example-python/config.yml` with your credentials:
   ```yaml
   client_id: your_client_id
   client_secret: your_client_secret
   ```

### 3. Authorize Polar Access

Run the web app to authorize:
```bash
cd accesslink-example-python
python example_web_app.py
```

Visit `http://localhost:8000` and follow the OAuth flow. This will create `usertokens.yml`.

### 4. Configure Notion

1. Create a Notion Internal Integration at [notion.so/my-integrations](https://www.notion.so/my-integrations)
2. Copy the Internal Integration Secret
3. Create (or identify) your running database in Notion
4. Share the database with your integration
5. Add to `accesslink-example-python/config.yml`:
   ```yaml
   notion_running_db_id: your_running_database_id
   ```

### 5. Initialize Database

```bash
sqlite3 data/polar.db < sql/schema.sql
```

### 6. Test the ETL

```bash
python -m polar_etl.run
```

### 7. Setup Daily Cron Jobs (Optional)

```bash
./setup_cron.sh
```

Or manually edit crontab:
```bash
crontab -e
```

Add:
```
10 4 * * * cd /path/to/ai-running-coach && source venv/bin/activate && python -m polar_etl.run >> logs/etl.log 2>&1
15 4 * * * cd /path/to/ai-running-coach && sqlite3 data/polar.db ".backup 'data/backups/polar_$(date +\%F).sqlite'"
```

### 8. Run MCP Server

```bash
python -m mcp.server
```

## Project Structure

```
ai-running-coach/
├── accesslink-example-python/  # Polar API integration (from Polar SDK)
│   ├── config.yml              # Polar API credentials (not in git)
│   ├── usertokens.yml          # OAuth tokens (not in git)
│   └── ...
├── polar_etl/                  # ETL scripts
│   ├── db.py                   # Database operations
│   ├── normalize.py            # Data normalization
│   ├── notion_running.py        # Notion running sync
│   ├── notion_utils.py          # Shared Notion helpers
│   └── run.py                  # Main ETL script
├── mcp/                        # MCP server
│   └── server.py               # FastMCP server with tools
├── data/                       # Database and backups
│   ├── polar.db                # SQLite database
│   └── backups/                # Daily backups
├── sql/                        # Database schema
│   └── schema.sql
├── logs/                       # ETL logs
└── requirements.txt            # Python dependencies
```

## MCP Tools

The MCP server exposes the following tools:

- `get_recent_sessions(limit: int)` - Get recent running sessions
- `get_recent_metrics(limit: int)` - Get recent daily metrics (HRV, RHR, VO₂, weight, etc.)
- `write_to_notion_running(...)` - Write running progress to Notion

## Using with Cursor (MCP Client)

Cursor can act as an MCP client for this project. Once your virtual environment is set up and the database is initialized, add the server to Cursor:

1. Ensure the project virtual environment is created and `requirements.txt` is installed.
2. Create or update `~/.cursor/mcp.json` with an entry that points at the MCP server script:

```
{
  "mcpServers": {
    "ai-running-coach": {
      "command": "/absolute/path/to/venv/bin/python",
      "args": ["/absolute/path/to/mcp/server.py"],
      "env": {}
    }
  }
}
```

3. Replace the absolute paths with the location of your cloned repository and virtual environment.
4. Restart Cursor (or use "Reload MCP Servers" from the command palette) so it picks up the new configuration.
5. Open Cursor on the repository and invoke the MCP tools (for example, `@mcp AI Running Coach:get_recent_sessions`).

For more details about MCP in Cursor, see the [Cursor MCP docs](https://docs.cursor.com/context/mcp).

## Database Schema

### Sessions Table
- `session_id` (PRIMARY KEY)
- `ts_start`, `ts_end` - Session timestamps
- `sport` - Activity type
- `distance_m` - Distance in meters
- `duration_s` - Duration in seconds
- `kcal` - Calories burned
- `avg_hr`, `max_hr` - Heart rate data
- `device` - Device used
- `training_load` - Training load metric

### Metrics Table
- `date` (PRIMARY KEY) - Date in YYYY-MM-DD format
- `resting_hr` - Resting heart rate
- `hrv_rmssd` - Heart rate variability
- `vo2max` - VO₂ max estimate
- `weight_kg` - Weight
- `sleep_hours` - Sleep duration

## Notion Database Setup

See `NOTION_RUNNING_SETUP.md` for running database structure and property expectations.

## Configuration

All configuration is in `accesslink-example-python/config.yml`:

```yaml
# Polar API
client_id: your_client_id
client_secret: your_client_secret

# Notion Running Database
notion_running_db_id: your_database_id
```

## Environment Variables (Alternative)

You can also use environment variables instead of config.yml:

- `NOTION_SECRET` - Notion Internal Integration Secret
- `NOTION_RUNNING_DB_ID` - Notion running database ID

## Troubleshooting

### Polar API Issues
- Ensure `usertokens.yml` exists and contains valid tokens
- Re-run OAuth flow if tokens expire
- Check Polar API rate limits

### Notion API Issues
- Verify database is shared with your integration
- Check database field names match config
- Ensure Internal Integration Secret is correct

### Database Issues
- Run `sqlite3 data/polar.db < sql/schema.sql` to recreate schema
- Check file permissions on `data/` directory

## Development

### Running Tests
```bash
# Test Notion connection
python -m polar_etl.test_notion

# Debug Notion database structure
python -m polar_etl.debug_notion <database_id>
```

### Adding New Data Sources
1. Create new module in `polar_etl/`
2. Add sync function to `polar_etl/run.py`
3. Update database schema if needed
4. Add MCP tool if exposing via API

## License

This project uses the Polar AccessLink SDK which has its own license. See `accesslink-example-python/LICENSE`.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Security Notes

- Never commit `config.yml` or `usertokens.yml` to git
- Keep your Notion Internal Integration Secret secure
- Rotate API credentials if compromised
- Database backups are stored locally - secure appropriately

