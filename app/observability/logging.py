import logging
import sys
from pythonjsonlogger import jsonlogger
from app.core.config import settings

def setup_logging():
    """
    Configures the root logger to output JSON structured logs to stdout.
    This is best practice for containerized/cloud deployments (Splunk, ELK, Datadog).
    """
    logger = logging.getLogger()
    
    # Set level based on env
    level = logging.DEBUG if settings.DEBUG else logging.INFO
    logger.setLevel(level)

    # Clear existing handlers
    if logger.handlers:
        logger.handlers = []

    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    # Standard Readable Formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Allow uvicorn logs to show up
    # logging.getLogger("uvicorn.access").disabled = True 
    logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.WARNING)

    return logger

# Initialize immediately
logger = setup_logging()
