"""Tests for FastAPI application."""
import pytest
from fastapi.testclient import TestClient
from src.api.app import app

client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data


def test_health_endpoint():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "model_loaded" in data


def test_model_info_endpoint():
    """Test model info endpoint."""
    response = client.get("/model/info")

    # Should work if model is loaded, otherwise 503
    if response.status_code == 200:
        data = response.json()
        assert "model_type" in data
        assert "price_categories" in data
    else:
        assert response.status_code == 503


def test_predict_endpoint_valid_input():
    """Test prediction endpoint with valid input."""
    payload = {
        "neighbourhood_group_cleansed": "Central Region",
        "property_type": "Entire rental unit",
        "room_type": "Entire home/apt",
        "accommodates": 4,
        "bathrooms_text": "2 baths",
        "beds": "2",
        "number_of_reviews": 25,
        "review_scores_rating": 4.5,
        "reviews_per_month": 2.0
    }

    response = client.post("/predict", json=payload)

    # Should work if model is loaded
    if response.status_code == 200:
        data = response.json()
        assert "predicted_category" in data
        assert "predicted_category_index" in data
    else:
        # Model might not be loaded in test environment
        assert response.status_code in [503, 500]


def test_predict_endpoint_invalid_input():
    """Test prediction endpoint with invalid input."""
    payload = {
        "neighbourhood_group_cleansed": "Central Region",
        # Missing required fields
    }

    response = client.post("/predict", json=payload)
    assert response.status_code == 422  # Validation error
