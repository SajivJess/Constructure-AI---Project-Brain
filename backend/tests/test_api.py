"""
API endpoint tests
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_authentication_endpoint():
    """Test authentication"""
    response = client.post(
        "/api/auth/login",
        json={
            "email": "testingcheckuser1234@gmail.com",
            "password": "any_password"
        }
    )
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_invalid_authentication():
    """Test invalid authentication"""
    response = client.post(
        "/api/auth/login",
        json={
            "email": "wrong@email.com",
            "password": "wrong"
        }
    )
    assert response.status_code == 401

def test_chat_endpoint_requires_auth():
    """Test that chat endpoint requires authentication"""
    response = client.post(
        "/api/chat",
        json={"query": "Test query"}
    )
    # Should require authorization
    assert response.status_code in [401, 403]

def test_document_upload_requires_auth():
    """Test that upload requires authentication"""
    response = client.post("/api/documents/upload")
    assert response.status_code in [401, 403]

def test_projects_list():
    """Test listing projects"""
    # First authenticate
    auth_response = client.post(
        "/api/auth/login",
        json={
            "email": "testingcheckuser1234@gmail.com",
            "password": "any"
        }
    )
    token = auth_response.json()["access_token"]
    
    # Then get projects
    response = client.get(
        "/api/projects",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_cors_headers():
    """Test that CORS headers are set"""
    response = client.options("/api/chat")
    assert "access-control-allow-origin" in response.headers

def test_evaluation_endpoint():
    """Test evaluation endpoint exists"""
    response = client.post("/api/evaluation/run")
    # May require auth, but should exist
    assert response.status_code in [200, 401, 403]

def test_openapi_docs():
    """Test that API documentation is available"""
    response = client.get("/docs")
    assert response.status_code == 200

def test_redoc_docs():
    """Test that ReDoc documentation is available"""
    response = client.get("/redoc")
    assert response.status_code == 200

def test_chat_with_valid_auth():
    """Test chat endpoint with valid authentication"""
    # Authenticate
    auth_response = client.post(
        "/api/auth/login",
        json={
            "email": "testingcheckuser1234@gmail.com",
            "password": "any"
        }
    )
    token = auth_response.json()["access_token"]
    
    # Send chat query
    response = client.post(
        "/api/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "query": "What is the fire rating?",
            "project_id": 1
        }
    )
    
    # Should process (may return empty if no docs, but shouldn't error)
    assert response.status_code == 200

def test_extraction_endpoint():
    """Test structured extraction endpoint"""
    # Authenticate
    auth_response = client.post(
        "/api/auth/login",
        json={
            "email": "testingcheckuser1234@gmail.com",
            "password": "any"
        }
    )
    token = auth_response.json()["access_token"]
    
    # Request extraction
    response = client.post(
        "/api/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "query": "Generate a door schedule",
            "project_id": 1
        }
    )
    
    assert response.status_code == 200

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
