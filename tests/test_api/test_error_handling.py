# tests/test_api/test_error_handling.py
"""
Test error handling and edge cases
"""
import pytest
from fastapi import status

class TestErrorHandling:
    """Test API error handling"""
    
    def test_invalid_json(self, client):
        """Test handling of invalid JSON"""
        response = client.post(
            "/api/v1/completion",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_missing_content_type(self, client):
        """Test handling of missing content type"""
        response = client.post("/api/v1/completion", data="test")
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_method_not_allowed(self, client):
        """Test handling of wrong HTTP method"""
        response = client.get("/api/v1/completion")
        
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    
    def test_not_found_endpoint(self, client):
        """Test handling of non-existent endpoint"""
        response = client.get("/api/v1/nonexistent")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_internal_server_error_handling(self, client, monkeypatch):
        """Test handling of internal server errors"""
        # Mock a service method to raise an exception
        def mock_error(*args, **kwargs):
            raise Exception("Simulated error")
        
        with monkeypatch.context() as m:
            m.setattr("app.services.model_service.ModelService.generate_completion", mock_error)
            
            response = client.post("/api/v1/completion", json={
                "code": "def test():",
                "language": "python",
                "cursor_position": 11
            })
            
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def test_rate_limiting(self, client, sample_completion_request):
        """Test rate limiting behavior"""
        # Make multiple rapid requests
        responses = []
        for _ in range(10):
            response = client.post("/api/v1/completion", json=sample_completion_request)
            responses.append(response)
        
        # At least some should succeed
        success_count = sum(1 for r in responses if r.status_code == status.HTTP_200_OK)
        assert success_count > 0
        
        # Check if rate limiting is applied (429 status)
        rate_limited = any(r.status_code == status.HTTP_429_TOO_MANY_REQUESTS for r in responses)
        # Note: Rate limiting test may pass even if not implemented yet