import io
import os
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.config import API_PREFIX

@pytest.fixture(scope="module")
def client():
    return TestClient(app)

def test_root_endpoint(client):
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_upload_invalid_file_type(client):
    """Test uploading a file with invalid extension."""
    file_content = b"Invalid file content"
    response = client.post(
        f"{API_PREFIX}/documents/upload",
        files={"file": ("test.exe", io.BytesIO(file_content), "application/octet-stream")}
    )
    assert response.status_code == 400
    assert "File type not supported" in response.json()["detail"]


def test_upload_txt_file(client):
    """Test uploading a TXT file."""
    file_content = b"This is a test document.\nIt has multiple lines.\nThis is for testing the upload functionality."
    response = client.post(
        f"{API_PREFIX}/documents/upload",
        files={"file": ("test.txt", io.BytesIO(file_content), "text/plain")}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "test.txt"
    assert data["file_type"] == ".txt"
    assert data["status"] == "processed"
    assert data["char_count"] > 0


def test_list_documents(client):
    """Test listing documents."""
    # First upload a document
    file_content = b"Another test document content."
    client.post(
        f"{API_PREFIX}/documents/upload",
        files={"file": ("sample.txt", io.BytesIO(file_content), "text/plain")}
    )
    
    # Then get the list
    response = client.get(f"{API_PREFIX}/documents/")
    assert response.status_code == 200
    data = response.json()
    assert "documents" in data
    assert "count" in data
    assert data["count"] > 0
    assert len(data["documents"]) > 0


def test_get_document(client):
    """Test getting a specific document."""
    # First upload a document
    file_content = b"Content for retrieving specific document."
    upload_response = client.post(
        f"{API_PREFIX}/documents/upload",
        files={"file": ("retrieve.txt", io.BytesIO(file_content), "text/plain")}
    )
    document_id = upload_response.json()["id"]
    
    # Then get it by ID
    response = client.get(f"{API_PREFIX}/documents/{document_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == document_id
    assert data["filename"] == "retrieve.txt"


def test_delete_document(client):
    """Test deleting a document."""
    # First upload a document
    file_content = b"Content for document to be deleted."
    upload_response = client.post(
        f"{API_PREFIX}/documents/upload",
        files={"file": ("delete_me.txt", io.BytesIO(file_content), "text/plain")}
    )
    document_id = upload_response.json()["id"]
    
    # Then delete it
    response = client.delete(f"{API_PREFIX}/documents/{document_id}")
    assert response.status_code == 200
    assert "Document deleted successfully" in response.json()["message"]
    
    # Try to get it - should return 404
    response = client.get(f"{API_PREFIX}/documents/{document_id}")
    assert response.status_code == 404