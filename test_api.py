import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from main import app

client = TestClient(app)

# Mock the classifier for faster tests
@patch('main.classifier', None)
def test_classify_valid_text():
    # Since classifier is mocked as None, we expect a 500 error
    response = client.post("/classify", json={"text": "I am feeling very happy and excited about my day."})
    assert response.status_code == 500
    data = response.json()
    assert data["detail"] == "Classifier model not loaded."

# Test for text that is too short (less than 20 characters)
def test_classify_short_text():
    response = client.post("/classify", json={"text": "Too short"})
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert "Please enter at least 5 characters." in data["detail"]

# Test for text that is too long (more than 500 characters)
def test_classify_long_text():
    long_text = "a" * 501  # Create a string with 501 characters
    response = client.post("/classify", json={"text": long_text})
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert "Please limit your journal entry to 500 characters." in data["detail"]

# Test for empty or whitespace-only text
def test_classify_whitespace_text():
    response = client.post("/classify", json={"text": "                    "})  # 20 spaces
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert "Text must not be empty or whitespace only." in data["detail"]

# Test for when the model is not loaded
@patch('main.classifier', None)  # Mock classifier as None
def test_model_not_loaded():
    response = client.post("/classify", json={"text": "This is a valid text input with more than 20 characters."})
    assert response.status_code == 500
    data = response.json()
    assert "detail" in data
    assert data["detail"] == "Classifier model not loaded."
