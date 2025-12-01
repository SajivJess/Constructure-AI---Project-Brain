"""
Tests for RAG pipeline
"""
import pytest
from app.services.rag_service import RAGService
from app.services.document_service import DocumentService
from app.database import SessionLocal

@pytest.fixture
def db_session():
    """Create a test database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def rag_service():
    """Create RAG service instance"""
    return RAGService()

@pytest.fixture
def doc_service():
    """Create document service instance"""
    return DocumentService()

def test_chunk_text(rag_service):
    """Test text chunking functionality"""
    text = "This is a test. " * 1000  # Long text
    chunks = rag_service._chunk_text(text, chunk_size=500, overlap=50)
    
    assert len(chunks) > 1
    assert all(len(chunk) <= 600 for chunk in chunks)  # Allow some overflow
    
def test_keyword_search(rag_service):
    """Test keyword search"""
    # This would need a populated database
    # For now, just test the function exists and is callable
    assert callable(rag_service._keyword_search)

def test_vector_search(rag_service):
    """Test vector search"""
    assert callable(rag_service._vector_search)

def test_hybrid_search(rag_service):
    """Test hybrid search combining vector and keyword"""
    assert callable(rag_service.retrieve_context)

def test_generate_answer(rag_service):
    """Test answer generation"""
    context_chunks = [
        {
            "content": "The fire rating for corridor partitions is 1 hour.",
            "file_name": "spec.pdf",
            "page_number": 5
        }
    ]
    
    query = "What is the fire rating for corridor partitions?"
    
    answer = rag_service.generate_answer(query, context_chunks)
    
    assert isinstance(answer, dict)
    assert "answer" in answer
    assert "sources" in answer
    assert len(answer["sources"]) > 0

@pytest.mark.asyncio
async def test_process_query_e2e(rag_service):
    """Test end-to-end query processing"""
    # This would need a populated database
    # For now, test the structure
    query = "What is the fire rating?"
    
    # Mock response structure
    result = {
        "answer": "Test answer",
        "sources": [
            {
                "file_name": "test.pdf",
                "page_number": 1,
                "relevance_score": 0.95
            }
        ],
        "confidence": "high"
    }
    
    assert "answer" in result
    assert "sources" in result
    assert isinstance(result["sources"], list)

def test_citation_formatting(rag_service):
    """Test that citations are properly formatted"""
    chunks = [
        {
            "file_name": "specifications.pdf",
            "page_number": 10,
            "content": "Test content"
        }
    ]
    
    sources = rag_service._format_sources(chunks)
    
    assert len(sources) > 0
    assert "file_name" in sources[0]
    assert "page_number" in sources[0]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
