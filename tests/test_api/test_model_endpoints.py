# tests/test_api/test_model_endpoints.py
"""
Test cases for model management endpoints
"""
import pytest
from fastapi import status

class TestModelEndpoints:
    """Test model management API endpoints"""
    
    def test_get_model_info(self, client):
        """Test getting model information"""
        response = client.get("/api/v1/model/info")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "name" in data
        assert "status" in data
        assert "supported_languages" in data
        assert isinstance(data["supported_languages"], list)
    
    def test_get_model_status(self, client):
        """Test getting model status"""
        response = client.get("/api/v1/model/status")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "status" in data
        assert "loaded" in data
        assert "memory_usage" in data
        assert isinstance(data["loaded"], bool)
    
    def test_get_supported_languages(self, client):
        """Test getting supported languages"""
        response = client.get("/api/v1/model/languages")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "languages" in data
        assert isinstance(data["languages"], list)
        assert len(data["languages"]) > 0
    
    def test_model_warmup(self, client):
        """Test model warmup endpoint"""
        response = client.post("/api/v1/model/warmup")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "message" in data
        assert "time_taken" in data
        assert isinstance(data["time_taken"], (int, float))
    
    def test_model_health_check(self, client):
        """Test model health check"""
        response = client.get("/api/v1/model/health")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "healthy" in data
        assert "checks" in data
        assert isinstance(data["healthy"], bool)
        assert isinstance(data["checks"], dict)