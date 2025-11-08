# Setup Guide

## Initial Setup

### 1. Install Dependencies

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Polar API Setup

1. Register at [Polar AccessLink API](https://www.polar.com/accesslink-api)
2. Create a new application
3. Copy `client_id` and `client_secret`
4. Copy `config.yml.example` to `config.yml`:
   ```bash
   cp accesslink-example-python/config.yml.example accesslink-example-python/config.yml
   ```
5. Edit `config.yml` with your credentials

### 3. Authorize Polar Access

```bash
cd accesslink-example-python
python example_web_app.py
```

1. Visit `http://localhost:8000`
2. Click "Authorize"
3. Log in to Polar and authorize the app
4. You'll be redirected back and `usertokens.yml` will be created

### 4. Notion Setup

#### Create Internal Integration

1. Go to [notion.so/my-integrations](https://www.notion.so/my-integrations)
2. Click "New integration"
3. Choose "Internal" integration
4. Copy the "Internal Integration Secret"
5. Set as environment variable:
   ```bash
   export NOTION_SECRET="your_secret_here"
   ```
   Or add to your shell profile (`~/.zshrc` or `~/.bashrc`)

#### Create Sleep Database

1. Create a new database in Notion
2. Add these properties:
   - `Date` (Date) - Sleep date
   - `Length` or `Sleep Hours` (Title/Rich Text/Number) - Sleep duration
   - `Synced to ETL` (Checkbox) - Sync status
3. Share the database with your integration
4. Copy the database ID from the URL
5. Add to `config.yml`:
   ```yaml
   notion_sleep_db_id: your_database_id
   ```

#### Create Running Database

See `NOTION_RUNNING_SETUP.md` for detailed instructions.

Or use the helper script:
```bash
python -m polar_etl.create_notion_running_db <parent_page_id>
```

### 5. Initialize Database

```bash
mkdir -p data backups logs
sqlite3 data/polar.db < sql/schema.sql
```

### 6. Test Everything

```bash
# Test Polar sync
python -m polar_etl.run

# Test MCP server
python -m mcp.server
```

### 7. Configure Cursor as MCP Client (Optional)

If you use Cursor as your IDE, you can connect it directly to this MCP server:

1. Verify your virtual environment is created and dependencies are installed.
2. Create or update `~/.cursor/mcp.json` and add an entry for the server:

```
{
  "mcpServers": {
    "marathon-polar": {
      "command": "/absolute/path/to/venv/bin/python",
      "args": ["/absolute/path/to/mcp/server.py"],
      "env": {}
    }
  }
}
```

3. Replace the absolute paths with your repository location and virtual environment path.
4. Restart Cursor, or use the command palette option "Reload MCP Servers".
5. Open Cursor in the project directory and invoke the tools via `@mcp Marathon Polar:...`.

Refer to the [Cursor MCP documentation](https://docs.cursor.com/context/mcp) if you need additional guidance.

### 8. Setup Cron Jobs (Optional)

```bash
chmod +x setup_cron.sh
./setup_cron.sh
```

## Environment Variables

You can use environment variables instead of config files:

```bash
export NOTION_SECRET="your_notion_secret"
export NOTION_SLEEP_DB_ID="your_sleep_db_id"
export NOTION_RUNNING_DB_ID="your_running_db_id"
```

## Troubleshooting

### "NOTION_SECRET not configured"
Set the environment variable or update the code with your secret (not recommended for production).

### "Database not found"
Run `sqlite3 data/polar.db < sql/schema.sql` to create the database.

### "Polar API authentication failed"
Re-run the OAuth flow: `python accesslink-example-python/example_web_app.py`

### Cron jobs not running
- Check cron logs: `tail -f logs/etl.log`
- Verify paths in `setup_cron.sh` are correct
- On macOS, ensure Terminal has Full Disk Access

