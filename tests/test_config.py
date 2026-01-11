"""Tests for configuration management."""
import pytest
from src.utils.config import Config, get_config


def test_config_loading():
    """Test that configuration loads correctly."""
    config = Config()
    assert config is not None
    assert config.data is not None
    assert config.model is not None
    assert config.api is not None


def test_config_get_method():
    """Test configuration get method with dot notation."""
    config = Config()

    # Test getting nested values
    assert config.get('api.port') == 8000
    assert config.get('api.host') == '0.0.0.0'
    assert config.get('data.random_state') == 21


def test_config_get_default():
    """Test configuration get method with default value."""
    config = Config()

    # Test non-existent key with default
    assert config.get('nonexistent.key', 'default_value') == 'default_value'


def test_config_singleton():
    """Test that get_config returns same instance."""
    config1 = get_config()
    config2 = get_config()

    assert config1 is config2


def test_config_properties():
    """Test configuration property accessors."""
    config = Config()

    assert isinstance(config.data, dict)
    assert isinstance(config.model, dict)
    assert isinstance(config.api, dict)
    assert isinstance(config.aws, dict)
    assert isinstance(config.logging, dict)
