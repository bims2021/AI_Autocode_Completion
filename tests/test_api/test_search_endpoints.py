# tests/test_api/test_search_endpoints.py
"""
Test cases for code search endpoints
"""
import pytest
from fastapi import status

class TestSearchEndpoints:
    """Test code search API endpoints"""
    
    def test_search_code_success(self, client, sample_search_request):
        """Test successful code search"""
        response = client.post("/api/v1/search", json=sample_search_request)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "results" in data
        assert "total_results" in data
        assert "query_time" in data
        assert isinstance(data["results"], list)
        assert isinstance(data["total_results"], int)
    
    def test_search_code_invalid_query(self, client, sample_search_request):
        """Test search with invalid query"""
        sample_search_request["query"] = ""
        response = client.post("/api/v1/search", json=sample_search_request)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "error" in data
    
    def test_search_code_with_filters(self, client, sample_search_request):
        """Test search with additional filters"""
        sample_search_request["filters"] = {
            "complexity": "medium",
            "tags": ["algorithm", "sorting"]
        }
        
        response = client.post("/api/v1/search", json=sample_search_request)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "results" in data
    
    def test_search_code_pagination(self, client, sample_search_request):
        """Test search with pagination"""
        sample_search_request["page"] = 1
        sample_search_request["page_size"] = 5
        
        response = client.post("/api/v1/search", json=sample_search_request)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "results" in data
        assert "page" in data
        assert "page_size" in data
        assert "total_pages" in data
        assert len(data["results"]) <= 5