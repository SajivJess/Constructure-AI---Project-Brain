from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
import os
import logging
from dotenv import load_dotenv
import uvicorn
from datetime import datetime
from collections import defaultdict
import pandas as pd
from io import BytesIO
from fastapi.responses import StreamingResponse
import hashlib
import json

from auth import verify_token, create_access_token, authenticate_user
from document_processor_vector import DocumentProcessor
from rag_pipeline_simple import RAGPipeline
from structured_extractor_simple import StructuredExtractor
from evaluation_simple import EvaluationSystem

load_dotenv()

# Query history storage
query_history = []
document_usage = defaultdict(int)

# In-memory cache for queries and responses
query_cache = {}  # {query_hash: {"answer": ..., "sources": ..., "timestamp": ...}}
retrieval_cache = {}  # {query_hash: [chunks...]}
CACHE_TTL_SECONDS = 3600  # 1 hour cache

def get_query_hash(query: str, filters: Dict = None) -> str:
    """Generate hash for query caching"""
    cache_key = query.lower().strip()
    if filters:
        cache_key += json.dumps(filters, sort_keys=True)
    return hashlib.md5(cache_key.encode()).hexdigest()

def is_cache_valid(timestamp: str) -> bool:
    """Check if cache entry is still valid"""
    try:
        cached_time = datetime.fromisoformat(timestamp)
        age = (datetime.now() - cached_time).total_seconds()
        return age < CACHE_TTL_SECONDS
    except:
        return False

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Constructure AI - Project Brain", version="1.0.0")

@app.on_event("startup")
async def startup_event():
    logger.info("=== CONSTRUCTURE AI API STARTING ===")
    logger.info(f"RAG Pipeline initialized: {rag_pipeline is not None}")
    logger.info(f"RAG Pipeline using Gemini: {getattr(rag_pipeline, 'use_gemini', False)}")
    logger.info(f"RAG Pipeline API key valid: {getattr(rag_pipeline, 'api_key_valid', False)}")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Initialize components
doc_processor = DocumentProcessor()
rag_pipeline = RAGPipeline(doc_processor=doc_processor)
structured_extractor = StructuredExtractor()
evaluation_system = EvaluationSystem()

# Pydantic models
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None  # Document, page range, confidence filters

class ChatResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    conversation_id: Optional[str] = None
    confidence: Optional[str] = None

class ExtractionRequest(BaseModel):
    extraction_type: str  # "door_schedule", "room_summary", "equipment_list"

class EvaluationResponse(BaseModel):
    total_queries: int
    results: List[Dict[str, Any]]
    summary: Dict[str, int]

# Routes
@app.get("/")
async def root():
    return {
        "message": "Constructure AI - Project Brain API",
        "version": "1.0.0",
        "status": "operational"
    }

@app.post("/auth/login")
async def login(request: LoginRequest):
    """Authenticate user and return JWT token"""
    user = authenticate_user(request.email, request.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": user["email"]})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {"email": user["email"]}
    }

@app.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Upload and process a construction document"""
    verify_token(credentials.credentials)
    
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    try:
        result = await doc_processor.process_document(file)
        return {
            "message": "Document processed successfully",
            "filename": file.filename,
            "chunks_created": result["chunks_count"],
            "document_id": result["document_id"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")

@app.get("/documents/list")
async def list_documents(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """List all uploaded documents"""
    verify_token(credentials.credentials)
    documents = doc_processor.list_documents()
    return {"documents": documents}

@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Handle chat queries with RAG"""
    verify_token(credentials.credentials)
    
    try:
        logger.info(f"Processing chat query: {request.message[:50]}...")
        
        # Check cache first
        query_hash = get_query_hash(request.message, request.filters)
        if query_hash in query_cache and is_cache_valid(query_cache[query_hash].get("timestamp", "")):
            logger.info(f"Cache hit for query: {request.message[:50]}...")
            cached_result = query_cache[query_hash]
            result_dict = {
                "answer": cached_result["answer"],
                "sources": cached_result["sources"],
                "confidence": cached_result.get("confidence", "medium"),
                "structured_data": cached_result.get("structured_data"),
                "cached": True
            }
            return ChatResponse(**result_dict)
        
        # Track query in history
        query_entry = {
            "timestamp": datetime.now().isoformat(),
            "query": request.message,
            "filters": request.filters
        }
        
        result = await rag_pipeline.process_query(
            query=request.message,
            conversation_id=request.conversation_id,
            filters=request.filters
        )
        
        # Update query history and document usage
        query_entry["sources_count"] = len(result.get("sources", []))
        query_entry["confidence"] = result.get("confidence")
        query_history.append(query_entry)
        
        for source in result.get("sources", []):
            document_usage[source.get("filename", "unknown")] += 1
        
        # Cache the result
        query_cache[query_hash] = {
            "answer": result.get("answer"),
            "sources": result.get("sources"),
            "confidence": result.get("confidence"),
            "structured_data": result.get("structured_data"),
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Chat query completed successfully (cached for future use)")
        return ChatResponse(**result)
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@app.post("/extract")
async def extract_structured_data(
    request: ExtractionRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Extract structured data (door schedules, room summaries, etc.)"""
    verify_token(credentials.credentials)
    
    try:
        result = await structured_extractor.extract(request.extraction_type)
        return {
            "extraction_type": request.extraction_type,
            "data": result["data"],
            "sources": result["sources"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting data: {str(e)}")

@app.get("/evaluate", response_model=EvaluationResponse)
async def run_evaluation(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Run evaluation tests on the RAG system"""
    verify_token(credentials.credentials)
    
    try:
        results = await evaluation_system.run_evaluation(rag_pipeline)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running evaluation: {str(e)}")

@app.get("/analytics")
async def get_analytics(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get query history and analytics"""
    verify_token(credentials.credentials)
    
    recent_queries = query_history[-50:] if len(query_history) > 50 else query_history
    total_queries = len(query_history)
    
    query_texts = [q["query"] for q in query_history]
    unique_queries = list(set(query_texts))
    query_counts = {q: query_texts.count(q) for q in unique_queries}
    popular_queries = sorted(query_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    
    return {
        "total_queries": total_queries,
        "recent_queries": recent_queries,
        "popular_queries": [{"query": q, "count": c} for q, c in popular_queries],
        "document_usage": [{"document": doc, "count": count} for doc, count in sorted(document_usage.items(), key=lambda x: x[1], reverse=True)],
        "avg_sources_per_query": sum(q.get("sources_count", 0) for q in query_history) / total_queries if total_queries > 0 else 0
    }

@app.get("/export/door_schedule")
async def export_door_schedule(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Export door schedule as Excel file"""
    verify_token(credentials.credentials)
    
    try:
        result = await structured_extractor.extract("door_schedule")
        
        if not result.get("data"):
            raise HTTPException(status_code=404, detail="No door schedule data found")
        
        df = pd.DataFrame(result["data"])
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Door Schedule', index=False)
            if result.get("sources"):
                pd.DataFrame(result["sources"]).to_excel(writer, sheet_name='Sources', index=False)
        
        output.seek(0)
        
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=door_schedule.xlsx"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting: {str(e)}")

@app.get("/export/room_schedule")
async def export_room_schedule(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Export room schedule as Excel file"""
    verify_token(credentials.credentials)
    
    try:
        result = await structured_extractor.extract("room_schedule")
        
        if not result.get("data"):
            raise HTTPException(status_code=404, detail="No room schedule data found")
        
        df = pd.DataFrame(result["data"])
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Room Schedule', index=False)
            if result.get("sources"):
                pd.DataFrame(result["sources"]).to_excel(writer, sheet_name='Sources', index=False)
        
        output.seek(0)
        
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=room_schedule.xlsx"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting: {str(e)}")

@app.get("/detect-conflicts")
async def detect_conflicts(
    query: str = "Are there any conflicting specifications?",
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Red-flag detection: Find conflicting specs or inconsistencies"""
    verify_token(credentials.credentials)
    
    try:
        # Search for common conflict areas
        conflict_queries = [
            "door fire ratings",
            "wall fire ratings",
            "floor finishes",
            "accessibility requirements",
            "dimensions and measurements"
        ]
        
        conflicts = []
        
        for topic in conflict_queries:
            # Search for relevant chunks
            results = doc_processor.search_documents(f"{topic} specifications", top_k=10)
            
            if len(results) < 2:
                continue
            
            # Extract text from top results
            texts = [r["content"] for r in results[:5]]
            
            # Ask LLM to detect conflicts
            texts_joined = "\n\n---\n\n".join(texts[:3])
            conflict_prompt = f"""Analyze these specifications about {topic} and identify any conflicts or inconsistencies:

{texts_joined}

List any conflicting requirements, differing specifications, or inconsistencies. 
If there are no conflicts, respond with "No conflicts detected".
Be specific about what conflicts and reference document sections."""
            
            conflict_result = await rag_pipeline.process_query(
                query=conflict_prompt,
                conversation_id=None,
                filters=None
            )
            
            answer = conflict_result.get("answer", "")
            if "no conflict" not in answer.lower() and len(answer) > 50:
                conflicts.append({
                    "topic": topic,
                    "potential_conflict": answer,
                    "sources": conflict_result.get("sources", [])[:3],
                    "confidence": conflict_result.get("confidence", "medium")
                })
        
        return {
            "conflicts_found": len(conflicts),
            "conflicts": conflicts,
            "analysis": "Analyzed common specification areas for inconsistencies" if conflicts else "No conflicts detected in analyzed areas"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Conflict detection error: {str(e)}")

@app.get("/cache/stats")
async def cache_stats(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get cache statistics"""
    verify_token(credentials.credentials)
    
    valid_cache_count = sum(1 for entry in query_cache.values() if is_cache_valid(entry.get("timestamp", "")))
    
    return {
        "total_cached_queries": len(query_cache),
        "valid_cache_entries": valid_cache_count,
        "cache_ttl_seconds": CACHE_TTL_SECONDS,
        "retrieval_cache_size": len(retrieval_cache)
    }

@app.post("/cache/clear")
async def clear_cache(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Clear all caches"""
    verify_token(credentials.credentials)
    
    query_cache.clear()
    retrieval_cache.clear()
    
    return {
        "status": "success",
        "message": "All caches cleared"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "vector_store": doc_processor.is_initialized(),
        "documents_count": len(doc_processor.list_documents()),
        "bm25_enabled": doc_processor.bm25 is not None,
        "total_queries": len(query_history),
        "cache_size": len(query_cache),
        "cache_hits_available": sum(1 for e in query_cache.values() if is_cache_valid(e.get("timestamp", "")))
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
