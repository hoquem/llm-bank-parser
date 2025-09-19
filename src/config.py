"""
Configuration management for the bank statement processor.

This module provides centralized configuration management with
environment variable support and validation.
"""

import os
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path

from dotenv import load_dotenv


@dataclass
class ProcessingConfig:
    """Configuration for PDF processing and AI operations."""

    # API Configuration
    api_key: str
    model_name: str = "gemini-2.0-flash"
    api_timeout: int = 120
    max_retries: int = 3

    # Processing Configuration
    batch_size: int = 5
    max_file_size_mb: int = 50
    allowed_extensions: list = field(default_factory=lambda: ['.pdf'])

    # Storage Configuration
    hash_algorithm: str = "sha256"
    csv_chunk_size: int = 1000

    # Directories
    data_dir: str = "data"
    output_dir: str = "output"
    output_filename: str = "comprehensive_data.csv"

    # Logging
    log_level: str = "INFO"
    log_to_file: bool = False
    log_file_path: Optional[str] = None

    @property
    def output_path(self) -> str:
        """Get the full output file path."""
        return os.path.join(self.output_dir, self.output_filename)

    def validate(self) -> None:
        """
        Validate configuration values.

        Raises:
            ValueError: If configuration is invalid
        """
        if not self.api_key:
            raise ValueError("API key is required")

        if self.batch_size <= 0:
            raise ValueError("Batch size must be positive")

        if self.max_file_size_mb <= 0:
            raise ValueError("Max file size must be positive")

        if self.api_timeout <= 0:
            raise ValueError("API timeout must be positive")

        if self.max_retries < 0:
            raise ValueError("Max retries cannot be negative")

        if self.log_level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            raise ValueError(f"Invalid log level: {self.log_level}")

    def ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        Path(self.data_dir).mkdir(exist_ok=True)
        Path(self.output_dir).mkdir(exist_ok=True)

        if self.log_to_file and self.log_file_path:
            Path(self.log_file_path).parent.mkdir(parents=True, exist_ok=True)


class ConfigManager:
    """Manages application configuration from multiple sources."""

    def __init__(self, env_file: str = ".env"):
        """
        Initialize configuration manager.

        Args:
            env_file: Path to environment file
        """
        self.env_file = env_file
        self._config: Optional[ProcessingConfig] = None

    def load_config(self) -> ProcessingConfig:
        """
        Load configuration from environment variables.

        Returns:
            ProcessingConfig: Loaded and validated configuration

        Raises:
            ValueError: If configuration is invalid
        """
        # Load environment variables
        load_dotenv(self.env_file)

        # Create configuration from environment
        config = ProcessingConfig(
            # Required
            api_key=os.getenv("GOOGLE_API_KEY", ""),

            # API Configuration
            model_name=os.getenv("MODEL_NAME", "gemini-2.0-flash"),
            api_timeout=int(os.getenv("API_TIMEOUT", "120")),
            max_retries=int(os.getenv("MAX_RETRIES", "3")),

            # Processing Configuration
            batch_size=int(os.getenv("BATCH_SIZE", "5")),
            max_file_size_mb=int(os.getenv("MAX_FILE_SIZE_MB", "50")),

            # Storage Configuration
            hash_algorithm=os.getenv("HASH_ALGORITHM", "sha256"),
            csv_chunk_size=int(os.getenv("CSV_CHUNK_SIZE", "1000")),

            # Directories
            data_dir=os.getenv("DATA_DIR", "data"),
            output_dir=os.getenv("OUTPUT_DIR", "output"),
            output_filename=os.getenv("OUTPUT_FILENAME", "comprehensive_data.csv"),

            # Logging
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
            log_to_file=os.getenv("LOG_TO_FILE", "false").lower() == "true",
            log_file_path=os.getenv("LOG_FILE_PATH"),
        )

        # Validate configuration
        config.validate()

        # Ensure directories exist
        config.ensure_directories()

        self._config = config
        return config

    @property
    def config(self) -> ProcessingConfig:
        """
        Get current configuration.

        Returns:
            ProcessingConfig: Current configuration

        Raises:
            RuntimeError: If configuration hasn't been loaded
        """
        if self._config is None:
            raise RuntimeError("Configuration not loaded. Call load_config() first.")
        return self._config


# Global configuration manager instance
config_manager = ConfigManager()


def get_config() -> ProcessingConfig:
    """
    Get the current application configuration.

    Returns:
        ProcessingConfig: Current configuration
    """
    return config_manager.config


def load_config(env_file: str = ".env") -> ProcessingConfig:
    """
    Load application configuration.

    Args:
        env_file: Path to environment file

    Returns:
        ProcessingConfig: Loaded configuration
    """
    global config_manager
    config_manager = ConfigManager(env_file)
    return config_manager.load_config()