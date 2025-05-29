import os
from typing import List, Optional
from pathlib import Path
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.config import ALLOWED_EXTENSIONS, MAX_FILE_SIZE
from app.models.document import DocumentCreate, DocumentList, DocumentResponse, DocumentDB
from app.services.document_processor import DocumentProcessor
from app.utils.file_utils import get_file_path, save_uploaded_file
from app.database import get_db

router = APIRouter(
    prefix="/documents",
    tags=["documents"],
    responses={404: {"description": "Not found"}},
)


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload a document file (PDF, DOCX, TXT, etc.) to the system.
    The file will be saved and processed for text extraction.
    """
    # Validate file size
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File size exceeds the maximum allowed size ({MAX_FILE_SIZE/(1024*1024)}MB)"
        )
    
    # Validate file extension using DocumentProcessor method
    if not DocumentProcessor.is_valid_file(file.filename):
        allowed = ", ".join(ALLOWED_EXTENSIONS)
        raise HTTPException(
            status_code=400,
            detail=f"File type not supported. Allowed types: {allowed}"
        )
    
    try:
        # Save file and get file ID
        file_id, file_path = save_uploaded_file(file)
        
        # Process document to extract text
        text, char_count = DocumentProcessor.process_document(file_path)
        
        # Create DB entry
        document = DocumentDB(
            id=file_id,
            filename=file.filename,
            file_path=str(file_path),
            file_type=os.path.splitext(file.filename)[1].lower(),
            processed_path=str(file_path.parent.parent / "processed" / f"{file_id}.txt"),
            status="processed",
            char_count=char_count
        )
        
        db.add(document)
        db.commit()
        db.refresh(document)
        
        return document
    
    except Exception as e:
        # Clean up file if something went wrong
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while processing the document: {str(e)}"
        )


@router.get("/", response_model=DocumentList)
async def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    List all uploaded documents with pagination, sorted by latest.
    """
    try:
        documents = db.query(DocumentDB).order_by(DocumentDB.created_at.desc()).offset(skip).limit(limit).all()
        total_count = db.query(DocumentDB).count()
        
        return DocumentList(documents=documents, count=total_count)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str, db: Session = Depends(get_db)):
    """
    Get a specific document by ID.
    """
    document = db.query(DocumentDB).filter(DocumentDB.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return document


@router.delete("/{document_id}", response_model=dict)
async def delete_document(document_id: str, db: Session = Depends(get_db)):
    """
    Delete a document by ID.
    """
    document = db.query(DocumentDB).filter(DocumentDB.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    try:
        # Delete file from storage
        if os.path.exists(document.file_path):
            os.remove(document.file_path)
        
        # Delete processed file if exists
        if document.processed_path and os.path.exists(document.processed_path):
            os.remove(document.processed_path)
        
        # Delete from database
        db.delete(document)
        db.commit()
        
        return {"message": "Document deleted successfully"}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while deleting the document: {str(e)}"
        )