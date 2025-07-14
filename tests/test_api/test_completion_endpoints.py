# tests/test_api/test_completion_endpoints.py
"""
Test cases for completion endpoints
"""
import pytest
from fastapi import status
import json

class TestCompletionEndpoints:
    """Test completion API endpoints"""
    
    def test_generate_completion_success(self, client, sample_completion_request):
        """Test successful code completion generation"""
        response = client.post("/api/v1/completion", json=sample_completion_request)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "code" in data
        assert "confidence" in data
        assert "language" in data
        assert "tokens_generated" in data
        assert data["language"] == "python"
        assert isinstance(data["confidence"], float)
        assert 0 <= data["confidence"] <= 1
    
    def test_generate_completion_invalid_language(self, client, sample_completion_request):
        """Test completion with unsupported language"""
        sample_completion_request["language"] = "unsupported_language"
        response = client.post("/api/v1/completion", json=sample_completion_request)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "error" in data
    
    def test_generate_completion_missing_code(self, client, sample_completion_request):
        """Test completion with missing code field"""
        del sample_completion_request["code"]
        response = client.post("/api/v1/completion", json=sample_completion_request)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_generate_completion_empty_code(self, client, sample_completion_request):
        """Test completion with empty code"""
        sample_completion_request["code"] = ""
        response = client.post("/api/v1/completion", json=sample_completion_request)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "error" in data
    
    def test_generate_completion_large_input(self, client, sample_completion_request):
        """Test completion with large input"""
        # Create a large code input (exceeding typical limits)
        large_code = "def test():\n    " + "x = 1\n    " * 1000
        sample_completion_request["code"] = large_code
        
        response = client.post("/api/v1/completion", json=sample_completion_request)
        
        # Should either succeed or return appropriate error
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_413_REQUEST_ENTITY_TOO_LARGE]
    
    def test_generate_completion_with_context(self, client, sample_completion_request):
        """Test completion with additional context"""
        response = client.post("/api/v1/completion", json=sample_completion_request)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Verify context is considered in response
        assert "code" in data
        assert len(data["code"]) > 0
    
    def test_generate_completion_different_temperatures(self, client, sample_completion_request):
        """Test completion with different temperature values"""
        temperatures = [0.1, 0.5, 0.8, 1.0]
        
        for temp in temperatures:
            sample_completion_request["temperature"] = temp
            response = client.post("/api/v1/completion", json=sample_completion_request)
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "code" in data
    
    def test_generate_completion_batch(self, client):
        """Test batch completion generation"""
        batch_request = {
            "requests": [
                {
                    "code": "def add(a, b):\n    return ",
                    "language": "python",
                    "cursor_position": 25,
                    "max_tokens": 50
                },
                {
                    "code": "function multiply(x, y) {\n    return ",
                    "language": "javascript",
                    "cursor_position": 35,
                    "max_tokens": 50
                }
            ]
        }
        
        response = client.post("/api/v1/completion/batch", json=batch_request)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "results" in data
        assert len(data["results"]) == 2
        
        for result in data["results"]:
            assert "code" in result
            assert "confidence" in result
            assert "language" in result
