import logging
import sys
from typing import Any, Dict

def setup_logging(level: str = "INFO") -> logging.Logger:
    """Configures structured application logging."""
    logger = logging.getLogger("swayin")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
    return logger

logger = setup_logging()

def log_event(event_type: str, details: Dict[str, Any]) -> None:
    """Utility for structured logging of system events without sensitive data."""
    # Mask any sensitive keys if present
    sanitized = {k: v for k, v in details.items() if "secret" not in k.lower() and "key" not in k.lower()}
    logger.info(f"EVENT: {event_type} | Details: {sanitized}")
