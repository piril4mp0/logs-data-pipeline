import os
from typing import Optional
from dotenv import load_dotenv

class Settings:
    """
    Settings class to manage configuration and connection details
    for the logs data pipeline.
    
    It supports loading configurations from environment variables,
    with fallback default values. It also attempts to load variables
    from a .env file located at the project root.
    """
    def __init__(self, env_file_path: Optional[str] = None):
        if env_file_path is None:
            # Default to .env in the root directory (parent of src)
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            env_file_path = os.path.join(base_dir, ".env")
        
        self.env_file_path = env_file_path
        self._load_env_file()

        # ClickHouse Connection Details
        self.ch_host: str = os.getenv("CH_HOST", "localhost")
        self.ch_port: str = os.getenv("CH_PORT", "8123")
        self.ch_user: str = os.getenv("CH_USER", "admin")
        self.ch_password: str = os.getenv("CH_PASSWORD", "admin")
        self.ch_database: str = os.getenv("CH_DATABASE", "logs")

    def _load_env_file(self) -> None:
        """Loads environment variables from .env file using python-dotenv."""
        if os.path.exists(self.env_file_path):
            load_dotenv(self.env_file_path)

    @property
    def connection_url(self) -> str:
        """Returns the ClickHouse HTTP query URL."""
        return f"http://{self.ch_host}:{self.ch_port}/?user={self.ch_user}&password={self.ch_password}"

# Instantiate a default settings object for ease of use
settings = Settings()
