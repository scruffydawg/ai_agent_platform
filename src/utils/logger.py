import logging
from pathlib import Path
from src.config import PROJECT_ROOT

LOG_DIR = PROJECT_ROOT / "data" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

class AgentLogger:
    """
    Centralized structured logging.
    Keeps CLI clean for the user while storing deep debug info for developers/LLMs.
    """
    def __init__(self, name: str = "AgentPlatform"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        # File Handler (Detailed)
        log_file = LOG_DIR / "system.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        
        # Format the log output
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        
        # Add handler
        # Avoid adding multiple handlers if logger is re-instantiated
        if not self.logger.handlers:
            self.logger.addHandler(file_handler)

    def debug(self, msg: str):
        self.logger.debug(msg)

    def info(self, msg: str):
        self.logger.info(msg)

    def warning(self, msg: str):
        self.logger.warning(msg)

    def error(self, msg: str):
        self.logger.error(msg)
        
    def critical(self, msg: str):
         self.logger.critical(msg)

# Singleton
logger = AgentLogger()
