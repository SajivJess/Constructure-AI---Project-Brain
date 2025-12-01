from typing import Dict, Any, List, Optional
import uuid
from openai import OpenAI
import os
from document_processor import DocumentProcessor

class RAGPipeline:
    """Retrieval-Augmented Generation pipeline for Q&A"""
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.doc_processor = DocumentProcessor()
        self.conversations = {}  # Simple in-memory conversation storage
        self.model = "gpt-4o-mini"  # Cost-effective model
    
    async def process_query(self, query: str, conversation_id: Optional[str] = None) -> Dict[str, Any]:
        """Process a user query with RAG"""
        
        # Create or get conversation
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
            self.conversations[conversation_id] = []
        
        # Check for structured extraction requests
        if self._is_extraction_request(query):
            return await self._handle_extraction_request(query, conversation_id)
        
        # Retrieve relevant documents
        retrieved_docs = self.doc_processor.search(query, n_results=5)
        
        if not retrieved_docs:
            return {
                "answer": "I couldn't find any relevant information in the documents. Please make sure documents have been uploaded.",
                "sources": [],
                "conversation_id": conversation_id
            }
        
        # Build context from retrieved documents
        context = self._build_context(retrieved_docs)
        
        # Get conversation history
        history = self.conversations.get(conversation_id, [])
        
        # Generate answer using OpenAI
        answer = self._generate_answer(query, context, history)
        
        # Extract and format sources
        sources = self._format_sources(retrieved_docs)
        
        # Update conversation history
        self.conversations[conversation_id].append({
            "role": "user",
            "content": query
        })
        self.conversations[conversation_id].append({
            "role": "assistant",
            "content": answer
        })
        
        return {
            "answer": answer,
            "sources": sources,
            "conversation_id": conversation_id
        }
    
    def _is_extraction_request(self, query: str) -> bool:
        """Check if query is requesting structured extraction"""
        extraction_keywords = [
            "door schedule", "generate a door schedule",
            "room summary", "list all rooms",
            "equipment list", "mep equipment"
        ]
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in extraction_keywords)
    
    async def _handle_extraction_request(self, query: str, conversation_id: str) -> Dict[str, Any]:
        """Handle extraction requests through chat"""
        from structured_extractor import StructuredExtractor
        extractor = StructuredExtractor()
        
        # Determine extraction type
        query_lower = query.lower()
        if "door" in query_lower:
            extraction_type = "door_schedule"
        elif "room" in query_lower:
            extraction_type = "room_summary"
        else:
            extraction_type = "equipment_list"
        
        # Perform extraction
        result = await extractor.extract(extraction_type)
        
        # Format as chat response
        answer = self._format_extraction_as_text(result["data"], extraction_type)
        
        return {
            "answer": answer,
            "sources": result["sources"],
            "conversation_id": conversation_id,
            "structured_data": result["data"]  # Include structured data
        }
    
    def _format_extraction_as_text(self, data: List[Dict], extraction_type: str) -> str:
        """Format structured data as readable text"""
        if not data:
            return f"No {extraction_type.replace('_', ' ')} data found in the documents."
        
        if extraction_type == "door_schedule":
            text = f"I found {len(data)} doors in the documents:\n\n"
            for door in data:
                text += f"• {door.get('mark', 'N/A')}: "
                text += f"{door.get('width_mm', 'N/A')}mm × {door.get('height_mm', 'N/A')}mm, "
                text += f"Fire Rating: {door.get('fire_rating', 'N/A')}, "
                text += f"Material: {door.get('material', 'N/A')}\n"
        elif extraction_type == "room_summary":
            text = f"I found {len(data)} rooms in the documents:\n\n"
            for room in data:
                text += f"• {room.get('name', 'N/A')}: "
                text += f"Area: {room.get('area_sqm', 'N/A')}m², "
                text += f"Finish: {room.get('floor_finish', 'N/A')}\n"
        else:
            text = f"I found {len(data)} equipment items:\n\n"
            for item in data:
                text += f"• {item.get('type', 'N/A')}: {item.get('description', 'N/A')}\n"
        
        return text
    
    def _build_context(self, retrieved_docs: List[Dict[str, Any]]) -> str:
        """Build context string from retrieved documents"""
        context_parts = []
        for doc in retrieved_docs:
            filename = doc['metadata']['filename']
            page = doc['metadata']['page']
            text = doc['text']
            context_parts.append(f"[{filename}, Page {page}]\n{text}")
        
        return "\n\n".join(context_parts)
    
    def _generate_answer(self, query: str, context: str, history: List[Dict]) -> str:
        """Generate answer using OpenAI"""
        
        system_prompt = """You are an expert AI assistant for construction project management. 
Your role is to answer questions about construction documents accurately and concisely.

Guidelines:
- Base your answers ONLY on the provided context from the documents
- If information is not in the context, say so clearly
- Cite specific sources when making claims
- Be precise about technical specifications (materials, dimensions, ratings)
- If asked about conflicting information, highlight the discrepancies
- Keep answers concise but complete"""

        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history (last 5 exchanges)
        messages.extend(history[-10:])
        
        # Add current query with context
        user_message = f"""Context from project documents:

{context}

Question: {query}

Please answer based on the context above."""
        
        messages.append({"role": "user", "content": user_message})
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
                max_tokens=800
            )
            
            return response.choices[0].message.content
        except Exception as e:
            return f"Error generating answer: {str(e)}"
    
    def _format_sources(self, retrieved_docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format sources for response"""
        sources = []
        seen = set()
        
        for doc in retrieved_docs:
            filename = doc['metadata']['filename']
            page = doc['metadata']['page']
            source_key = f"{filename}_{page}"
            
            if source_key not in seen:
                sources.append({
                    "filename": filename,
                    "page": page,
                    "text_preview": doc['text'][:200] + "..." if len(doc['text']) > 200 else doc['text']
                })
                seen.add(source_key)
        
        return sources
