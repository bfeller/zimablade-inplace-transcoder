"""
Logging configuration for the transcoder application.
"""

import logging
import logging.handlers
import sys
from pathlib import Path


def setup_logging(config=None) -> logging.Logger:
    """Set up logging configuration."""
    # Get configuration values
    log_level = getattr(config, 'log_level', 'INFO') if config else 'INFO'
    log_file = getattr(config, 'log_file', '/data/logs/transcoder.log') if config else '/data/logs/transcoder.log'
    log_max_size = getattr(config, 'log_max_size', 10485760) if config else 10485760  # 10MB
    log_backup_count = getattr(config, 'log_backup_count', 5) if config else 5
    
    # Create logger
    logger = logging.getLogger('zimablade_transcoder')
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler with rotation
    try:
        # Ensure log directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=log_max_size,
            backupCount=log_backup_count
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
    except Exception as e:
        logger.warning("Failed to setup file logging: %s", e)
    
    # Prevent duplicate logs
    logger.propagate = False
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(f'zimablade_transcoder.{name}')
