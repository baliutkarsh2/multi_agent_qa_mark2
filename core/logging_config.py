import logging, sys
from core.config import LOG_LEVEL

LOG_FORMAT = "%(asctime)s | %(name)-15s | %(levelname)-8s | %(message)s"

# Convert string log level to logging constant
LOG_LEVEL_MAP = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL
}

log_level = LOG_LEVEL_MAP.get(LOG_LEVEL.upper(), logging.INFO)

logging.basicConfig(
    level=log_level, 
    format=LOG_FORMAT, 
    handlers=[logging.StreamHandler(sys.stdout)]
)

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name) 