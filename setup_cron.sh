#!/bin/bash
# setup_cron.sh - Helper script to set up cron jobs for Polar ETL
# For macOS: This sets up cron jobs that will run daily

# Get project directory from script location
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CRON_LOG="$PROJECT_DIR/logs/cron.log"

# Get full paths for better reliability on macOS
# Use the venv python directly (more reliable than activating in cron)
PYTHON_PATH="$PROJECT_DIR/venv/bin/python"
SQLITE_PATH=$(which sqlite3)

# Create a temporary crontab file
TMP_CRON=$(mktemp)

# Get existing crontab (if any)
crontab -l 2>/dev/null > "$TMP_CRON" || true

# Remove any existing polar ETL entries
grep -v "polar_etl.run" "$TMP_CRON" > "${TMP_CRON}.new" || true
grep -v "polar.db.*backup" "${TMP_CRON}.new" > "$TMP_CRON" || true

# Add new cron jobs with full paths and proper environment
cat >> "$TMP_CRON" << EOF

# Polar ETL - Daily data extraction at 4:10 AM
# Note: On macOS, cron runs with minimal environment. We set PATH and use full paths.
10 4 * * * PATH=/usr/local/bin:/usr/bin:/bin && cd $PROJECT_DIR && $PYTHON_PATH -m polar_etl.run >> $PROJECT_DIR/logs/etl.log 2>&1

# Polar DB - Daily backup at 4:15 AM
15 4 * * * PATH=/usr/local/bin:/usr/bin:/bin && cd $PROJECT_DIR && $SQLITE_PATH data/polar.db ".backup 'data/backups/polar_\$(date +\%F).sqlite'"
EOF

# Install the new crontab
crontab "$TMP_CRON"

# Clean up
rm -f "$TMP_CRON" "${TMP_CRON}.new"

echo "Cron jobs installed successfully!"
echo "To view your crontab: crontab -l"
echo "To remove these jobs: crontab -e (then delete the lines)"

