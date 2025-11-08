# Changelog

## [Unreleased]

### Added
- Comprehensive README with setup instructions
- SETUP.md with detailed configuration guide
- CONTRIBUTING.md for contributors
- .gitignore to exclude sensitive files
- config.yml.example template
- .env.example for environment variables
- .gitattributes for consistent line endings

### Changed
- Moved hardcoded Notion secrets to environment variables
- Made setup_cron.sh use relative paths
- Improved error messages for missing configuration
- Better documentation throughout

### Security
- Removed hardcoded credentials from code
- Added .gitignore to prevent committing secrets
- Configuration now uses environment variables or config files

### Developer Experience
- Added example config files
- Clear setup documentation
- Debug scripts documented
- Contributing guidelines
