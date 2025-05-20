import pytest
import os
from dotenv import load_dotenv

@pytest.fixture(autouse=True)
def setup_test_env():
    """Set up test environment variables."""
    # Load environment variables from .env file if it exists
    load_dotenv()
    
    # Set test environment variables if not already set
    if not os.getenv("GITHUB_TOKEN"):
        os.environ["GITHUB_TOKEN"] = "test-token"
    if not os.getenv("GITHUB_WEBHOOK_SECRET"):
        os.environ["GITHUB_WEBHOOK_SECRET"] = "test-secret"
    if not os.getenv("OPENAI_API_KEY"):
        os.environ["OPENAI_API_KEY"] = "test-key"
    
    yield
    
    # Clean up test database after tests
    if os.path.exists("security_reviews.db"):
        os.remove("security_reviews.db") 