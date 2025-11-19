# Application Logging

This directory contains application log files with automatic daily rotation.

## Log Files

- `logs.log` - Current log file containing all application logs
- `logs.log.YYYY-MM-DD` - Rotated log files from previous days

## Configuration

Logging is configured in `src/app/utils/logger.py` with the following features:

### Features

1. **File-based logging**: All logs are written to `applog/logs.log`
2. **Console output**: Logs are also printed to console for development
3. **Daily rotation**: Log files rotate automatically at midnight
4. **30-day retention**: Keeps the last 30 days of logs
5. **Timestamped backups**: Rotated files are named with the date (e.g., `logs.log.2025-11-19`)

### Log Levels

You can configure the log level via the `LOG_LEVEL` environment variable in `.env`:

```bash
LOG_LEVEL=INFO  # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
```

### Log Format

Each log entry includes:
- Timestamp (YYYY-MM-DD HH:MM:SS)
- Logger name (module/component)
- Log level (INFO, ERROR, etc.)
- Message

Example:
```
2025-11-19 10:30:45 - src.app.routers.fabs - INFO - Creating new FAB for job_id=123
```

## Usage in Code

To use logging in your modules:

```python
from src.app.utils.logger import get_logger

logger = get_logger(__name__)

# Use the logger
logger.info("This is an info message")
logger.warning("This is a warning")
logger.error("This is an error")
logger.debug("This is a debug message")
```

## Viewing Logs

### View current log file
```bash
tail -f applog/logs.log
```

### View with timestamps
```bash
cat applog/logs.log
```

### Search logs
```bash
grep "ERROR" applog/logs.log
grep "job_id=123" applog/logs.log
```

### View specific date's logs
```bash
cat applog/logs.log.2025-11-19
```

## Maintenance

- Logs older than 30 days are automatically deleted
- No manual cleanup required
- The directory structure is preserved in git via `.gitkeep`
- Log files themselves are ignored by git (see `.gitignore`)
