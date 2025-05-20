import os
import json
import pytest
from dotenv import load_dotenv

# Load the actual environment variables first
load_dotenv()

# Set up test environment variables, using actual tokens if available
if not os.getenv("GITHUB_TOKEN"):
    os.environ["GITHUB_TOKEN"] = "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"
if not os.getenv("GITHUB_WEBHOOK_SECRET"):
    os.environ["GITHUB_WEBHOOK_SECRET"] = "685947e52e52c473b403fcc6f572c7f19955c4d3"
if not os.getenv("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = "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"

from fastapi.testclient import TestClient
from app.main import app
from app.config import Settings

client = TestClient(app)

def test_webhook_without_signature():
    """Test webhook endpoint without signature."""
    response = client.post("/webhook/github", json={
        "action": "opened",
        "pull_request": {
            "number": 1,
            "head": {
                "repo": {"full_name": "test/repo"},
                "sha": "test-sha"
            }
        }
    })
    assert response.status_code == 401
    assert response.json()["detail"] == "No signature provided"

def test_webhook_with_invalid_signature():
    """Test webhook endpoint with invalid signature."""
    response = client.post(
        "/webhook/github",
        json={
            "action": "opened",
            "pull_request": {
                "number": 1,
                "head": {
                    "repo": {"full_name": "test/repo"},
                    "sha": "test-sha"
                }
            }
        },
        headers={"X-Hub-Signature-256": "invalid"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid signature"

def test_get_reviews_empty():
    """Test getting reviews when none exist."""
    response = client.get("/api/reviews")
    assert response.status_code == 200
    assert response.json() == []

def test_get_review_status_not_found():
    """Test getting status of non-existent review."""
    response = client.get("/status/999")
    assert response.status_code == 200
    assert response.json() == {"status": "not_found"}

def test_root_endpoint():
    """Test root endpoint returns HTML."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"

@pytest.fixture(autouse=True)
def cleanup():
    """Clean up after tests."""
    yield
    if os.path.exists("security_reviews.db"):
        os.remove("security_reviews.db") 