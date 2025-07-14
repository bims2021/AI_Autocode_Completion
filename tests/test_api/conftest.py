# tests/test_api/conftest.py
"""
Pytest configuration and fixtures for API tests
"""
import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_model_service():
    """Mock AI model service for testing"""
    with patch('app.services.model_service.ModelService') as mock:
        mock_instance = Mock()
        mock_instance.generate_completion.return_value = {
            'code': 'def hello():\n    return "Hello, World!"',
            'confidence': 0.95,
            'language': 'python',
            'tokens_generated': 15
        }
        mock_instance.is_model_loaded.return_value = True
        mock_instance.get_model_info.return_value = {
            'name': 'test-model',
            'status': 'loaded',
            'supported_languages': ['python', 'javascript']
        }
        mock.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_cache_service():
    """Mock cache service for testing"""
    with patch('app.services.cache_service.CacheService') as mock:
        mock_instance = Mock()
        mock_instance.get.return_value = None
        mock_instance.set.return_value = True
        mock_instance.exists.return_value = False
        mock.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def client(mock_model_service, mock_cache_service):
    """Create test client with mocked dependencies"""
    from app.main import app
    return TestClient(app)

@pytest.fixture
def sample_completion_request():
    """Sample completion request data"""
    return {
        "code": "def fibonacci(n):\n    if n <= 1:\n        return n\n    return ",
        "language": "python",
        "cursor_position": 65,
        "max_tokens": 100,
        "temperature": 0.7,
        "context": {
            "file_path": "/test/fibonacci.py",
            "project_context": ["math", "algorithms"]
        }
    }

@pytest.fixture
def sample_search_request():
    """Sample code search request data"""
    return {
        "query": "implement binary search algorithm",
        "language": "python",
        "max_results": 10,
        "similarity_threshold": 0.8
    }
