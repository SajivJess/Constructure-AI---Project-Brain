import os
import hashlib
import json
from typing import List, Dict, Any
from pathlib import Path
import aiofiles
from pypdf import PdfReader
import chromadb
from chromadb.config import Settings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from fastapi import UploadFile

class DocumentProcessor:
    """Handles document ingestion, chunking, and indexing"""
    
    def __init__(self):
        self.upload_dir = Path(os.getenv("UPLOAD_DIR", "./uploads"))
        self.upload_dir.mkdir(exist_ok=True)
        
        # Initialize ChromaDB
        chroma_dir = os.getenv("CHROMA_DB_DIR", "./chroma_db")
        self.chroma_client = chromadb.PersistentClient(
            path=chroma_dir,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        self.collection = self.chroma_client.get_or_create_collection(
            name="construction_docs",
            metadata={"hnsw:space": "cosine"}
        )
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Text splitter configuration
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        # Metadata storage
        self.metadata_file = self.upload_dir / "documents_metadata.json"
        self.documents_metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict:
        """Load documents metadata from file"""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_metadata(self):
        """Save documents metadata to file"""
        with open(self.metadata_file, 'w') as f:
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
        text_chunks = self._extract_and_chunk_pdf(file_path, doc_id)
        
        # Create embeddings and store in ChromaDB
        self._index_chunks(text_chunks, doc_id, file.filename)
        
        # Save metadata
        self.documents_metadata[doc_id] = {
            "filename": file.filename,
            "path": str(file_path),
            "chunks_count": len(text_chunks),
            "uploaded_at": str(Path(file_path).stat().st_mtime)
        }
        self._save_metadata()
        
        return {
            "document_id": doc_id,
            "chunks_count": len(text_chunks)
        }
    
    def _extract_and_chunk_pdf(self, file_path: Path, doc_id: str) -> List[Dict[str, Any]]:
        """Extract text from PDF and split into chunks"""
        chunks = []
        
        try:
            reader = PdfReader(file_path)
            
            for page_num, page in enumerate(reader.pages, start=1):
                text = page.extract_text()
                
                if not text.strip():
                    continue
                
                # Split page text into chunks
                page_chunks = self.text_splitter.split_text(text)
                
                for chunk_idx, chunk_text in enumerate(page_chunks):
                    chunks.append({
                        "text": chunk_text,
                        "page": page_num,
                        "chunk_index": chunk_idx,
                        "document_id": doc_id
                    })
        
        except Exception as e:
            raise Exception(f"Error processing PDF: {str(e)}")
        
        return chunks
    
    def _index_chunks(self, chunks: List[Dict[str, Any]], doc_id: str, filename: str):
        """Index chunks in ChromaDB"""
        if not chunks:
            return
        
        # Prepare data for ChromaDB
        texts = [chunk["text"] for chunk in chunks]
        embeddings = self.embedding_model.encode(texts).tolist()
        
        ids = [f"{doc_id}_page{chunk['page']}_chunk{chunk['chunk_index']}" for chunk in chunks]
        metadatas = [
            {
                "document_id": doc_id,
                "filename": filename,
                "page": chunk["page"],
                "chunk_index": chunk["chunk_index"]
            }
            for chunk in chunks
        ]
        
        # Add to collection
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas
        )
    
    def search(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant chunks"""
        query_embedding = self.embedding_model.encode([query]).tolist()
        
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=n_results
        )
        
        # Format results
        formatted_results = []
        if results['documents']:
            for i in range(len(results['documents'][0])):
                formatted_results.append({
                    "text": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i],
                    "distance": results['distances'][0][i] if results.get('distances') else None
                })
        
        return formatted_results
    
    def list_documents(self) -> List[Dict[str, Any]]:
        """List all processed documents"""
        return [
            {"document_id": doc_id, **metadata}
            for doc_id, metadata in self.documents_metadata.items()
        ]
    
    def is_initialized(self) -> bool:
        """Check if vector store is initialized"""
        try:
            return self.collection.count() > 0
        except:
            return False
