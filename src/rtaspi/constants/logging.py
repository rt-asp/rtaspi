"""
Constants for logging configuration.
"""

import logging

# Log levels
LOG_LEVEL_DEBUG = logging.DEBUG
LOG_LEVEL_INFO = logging.INFO
LOG_LEVEL_WARNING = logging.WARNING
LOG_LEVEL_ERROR = logging.ERROR
LOG_LEVEL_CRITICAL = logging.CRITICAL

# Default logging settings
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_STORAGE_PATH = "storage"
DEFAULT_LOG_DIR = "logs"
DEFAULT_LOG_BACKUP_COUNT = 30

# Log formatters
CONSOLE_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
FILE_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"

# Default logging configuration
DEFAULT_LOGGING_CONFIG = {
    "system": {
        "log_level": DEFAULT_LOG_LEVEL,
        "storage_path": DEFAULT_STORAGE_PATH
    }
}

# External loggers to suppress
EXTERNAL_LOGGERS = ["urllib3", "requests", "werkzeug"]
EXTERNAL_LOGGER_LEVEL = logging.WARNING
