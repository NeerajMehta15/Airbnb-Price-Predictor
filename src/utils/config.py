"""Configuration management for Airbnb Price Predictor."""
import os
import yaml
from pathlib import Path
from typing import Any, Dict


class Config:
    """Configuration handler for loading and accessing application settings."""

    def __init__(self, config_path: str = None):
        """
        Initialize configuration from YAML file.

        Args:
            config_path: Path to configuration file. If None, uses default location.
        """
        if config_path is None:
            # Default to configs/config.yaml relative to project root
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / "configs" / "config.yaml"

        self.config_path = Path(config_path)
        self._config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)

        # Override with environment variables if present
        config = self._apply_env_overrides(config)
        return config

    def _apply_env_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply environment variable overrides to configuration."""
        # AWS Configuration
        if os.getenv('AWS_REGION'):
            config['aws']['region'] = os.getenv('AWS_REGION')
        if os.getenv('AWS_ECR_REPOSITORY'):
            config['aws']['ecr_repository'] = os.getenv('AWS_ECR_REPOSITORY')
        if os.getenv('AWS_ECS_CLUSTER'):
            config['aws']['ecs_cluster'] = os.getenv('AWS_ECS_CLUSTER')
        if os.getenv('AWS_S3_BUCKET'):
            config['aws']['s3_bucket'] = os.getenv('AWS_S3_BUCKET')

        # API Configuration
        if os.getenv('API_HOST'):
            config['api']['host'] = os.getenv('API_HOST')
        if os.getenv('API_PORT'):
            config['api']['port'] = int(os.getenv('API_PORT'))

        # Model path override
        if os.getenv('MODEL_PATH'):
            config['model']['model_path'] = os.getenv('MODEL_PATH')

        return config

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key using dot notation.

        Args:
            key: Configuration key in dot notation (e.g., 'data.raw_data_path')
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self._config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default

        return value

    @property
    def data(self) -> Dict[str, Any]:
        """Get data configuration."""
        return self._config.get('data', {})

    @property
    def model(self) -> Dict[str, Any]:
        """Get model configuration."""
        return self._config.get('model', {})

    @property
    def api(self) -> Dict[str, Any]:
        """Get API configuration."""
        return self._config.get('api', {})

    @property
    def aws(self) -> Dict[str, Any]:
        """Get AWS configuration."""
        return self._config.get('aws', {})

    @property
    def logging(self) -> Dict[str, Any]:
        """Get logging configuration."""
        return self._config.get('logging', {})


# Global configuration instance
_config_instance = None


def get_config(config_path: str = None) -> Config:
    """
    Get global configuration instance (singleton pattern).

    Args:
        config_path: Path to configuration file (only used on first call)

    Returns:
        Config instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config(config_path)
    return _config_instance
