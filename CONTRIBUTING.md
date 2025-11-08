# Contributing

Thank you for considering contributing to Marathon Polar!

## Development Setup

1. Fork the repository
2. Clone your fork
3. Set up development environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

## Code Style

- Follow PEP 8
- Use type hints where possible
- Add docstrings to functions and classes
- Keep functions focused and small

## Testing

Before submitting a PR:

1. Test your changes locally
2. Run the ETL: `python -m polar_etl.run`
3. Test MCP server: `python -m mcp.server`
4. Verify database operations work correctly

## Debug Scripts

The repository includes debug/test scripts in `polar_etl/`:
- `debug_notion.py` - Inspect Notion database structure
- `test_notion.py` - Test Notion API connection

These are useful for development but not required for production.

## Pull Request Process

1. Create a feature branch
2. Make your changes
3. Update documentation if needed
4. Test thoroughly
5. Submit PR with clear description

## Security

- Never commit secrets or credentials
- Use environment variables for sensitive data
- Update `.gitignore` if adding new sensitive files

