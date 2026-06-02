import logging
import sys

class PipelineFormatter(logging.Formatter):
    """Custom formatter to match the project's logging style."""
    def format(self, record):
        msg = record.getMessage()
        # Handle cases where messages start with a newline for spacing
        if msg.startswith('\n'):
            return f"\n[{record.name}] {msg[1:]}"
        return f"[{record.name}] {msg}"

class PipelineLogger:
    """
    A centralized logger for the data pipeline to reduce redundancy.
    It automatically prefixes messages with the job name.
    """
    def __init__(self, name: str = "SPARK-JOB"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(PipelineFormatter())
            self.logger.addHandler(handler)

    def info(self, msg: str):
        """Logs an informational message."""
        self.logger.info(msg)

    def error(self, msg: str):
        """Logs an error message with an additional [ERRO] tag."""
        self.logger.info(f"[ERRO] {msg}")

    def warn(self, msg: str):
        """Logs a warning message with an additional [AVISO] tag."""
        self.logger.info(f"[AVISO] {msg}")

# Create a default instance for the SPARK-JOB
logger = PipelineLogger()
