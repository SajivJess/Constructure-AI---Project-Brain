import os
import hashlib
import json
from typing import List, Dict, Any
from pathlib import Path
import aiofiles
from pypdf import PdfReader
from fastapi import UploadFile

class DocumentProcessor:
    """Handles document ingestion, chunking, and indexing (simplified version)"""
    
    def __init__(self):
        self.upload_dir = Path(os.getenv("UPLOAD_DIR", "./data/uploads"))
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory storage for documents and chunks
        self.documents = {}
        self.chunks = []
        
        # Metadata storage
        self.metadata_file = self.upload_dir / "documents_metadata.json"
        self.documents_metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict:
        """Load documents metadata from file"""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _save_metadata(self):
        """Save documents metadata to file"""
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.documents_metadata, f, indent=2)
    
    async def process_document(self, file: UploadFile) -> Dict[str, Any]:
        """Process and index a document"""
        # Save uploaded file
        file_path = self.upload_dir / file.filename
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # Generate document ID
        doc_id = hashlib.md5(file.filename.encode()).hexdigest()
        
        # Extract text from PDF
        text_chunks = self._extract_and_chunk_pdf(file_path, doc_id, file.filename)
        
        # Store in memory
        self.documents[doc_id] = {
            "filename": file.filename,
            "path": str(file_path),
            "chunks": text_chunks
        }
        self.chunks.extend(text_chunks)
        
        # Save metadata
        self.documents_metadata[doc_id] = {
            "filename": file.filename,
            "path": str(file_path),
            "chunks_count": len(text_chunks),
        }
        self._save_metadata()
        
        return {
            "document_id": doc_id,
            "filename": file.filename,
            "chunks_count": len(text_chunks)
        }
    
    def _extract_and_chunk_pdf(self, file_path: Path, doc_id: str, filename: str) -> List[Dict[str, Any]]:
        """Extract text from PDF and split into chunks"""
        chunks = []
        
        try:
            reader = PdfReader(file_path)
            
            for page_num, page in enumerate(reader.pages, start=1):
                text = page.extract_text()
                
                if text.strip():
                    # Simple chunking by splitting on double newlines and size
                    page_chunks = self._chunk_text(text, chunk_size=1000, overlap=200)
                    
                    for chunk_idx, chunk_text in enumerate(page_chunks):
                        chunk_id = f"{doc_id}_page{page_num}_chunk{chunk_idx}"
                        chunks.append({
                            "id": chunk_id,
                            "document_id": doc_id,
                            "filename": filename,
                            "page_number": page_num,
                            "chunk_index": chunk_idx,
                            "content": chunk_text
                        })
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            
        return chunks
    
    def _chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Split text into overlapping chunks"""
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk.strip())
            start += (chunk_size - overlap)
        
        return chunks
    
    def search_documents(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Simple keyword-based search through all chunks"""
        query_lower = query.lower()
        results = []
        
        for chunk in self.chunks:
            content_lower = chunk["content"].lower()
            # Calculate relevance score based on keyword matches
            score = 0
            for word in query_lower.split():
                if word in content_lower:
                    score += content_lower.count(word)
            
            if score > 0:
                results.append({
                    **chunk,
                    "relevance_score": score
                })
        
        # Sort by relevance and return top_k
        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        return results[:top_k]
    
    def get_all_documents(self) -> List[Dict[str, Any]]:
        """Get list of all documents"""
        return [
            {
                "document_id": doc_id,
                **metadata
            }
            for doc_id, metadata in self.documents_metadata.items()
        ]
