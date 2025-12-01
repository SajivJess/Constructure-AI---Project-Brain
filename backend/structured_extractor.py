from typing import Dict, Any, List
import json
from openai import OpenAI
import os
from document_processor import DocumentProcessor

class StructuredExtractor:
    """Extracts structured data from construction documents"""
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.doc_processor = DocumentProcessor()
        self.model = "gpt-4o-mini"
    
    async def extract(self, extraction_type: str) -> Dict[str, Any]:
        """Extract structured data based on type"""
        
        extraction_map = {
            "door_schedule": self._extract_door_schedule,
            "room_summary": self._extract_room_summary,
            "equipment_list": self._extract_equipment_list
        }
        
        if extraction_type not in extraction_map:
            raise ValueError(f"Unsupported extraction type: {extraction_type}")
        
        return await extraction_map[extraction_type]()
    
    async def _extract_door_schedule(self) -> Dict[str, Any]:
        """Extract door schedule from documents"""
        
        # Search for door-related content
        queries = [
            "door schedule specifications",
            "door types fire rating dimensions",
            "door hardware requirements"
        ]
        
        all_docs = []
        for query in queries:
            docs = self.doc_processor.search(query, n_results=10)
            all_docs.extend(docs)
        
        # Remove duplicates
        unique_docs = {doc['text']: doc for doc in all_docs}.values()
        context = self._build_extraction_context(list(unique_docs))
        
        prompt = """Extract ALL doors from the following construction documents and return a JSON array.

For each door, extract:
- mark: Door identifier/mark (e.g., "D-101", "101", etc.)
- location: Where the door is located
- width_mm: Width in millimeters (convert if needed)
- height_mm: Height in millimeters (convert if needed)
- fire_rating: Fire rating (e.g., "1 HR", "90 MIN", "NONE")
- material: Door material (e.g., "Hollow Metal", "Wood", "Aluminum")

Context:
{context}

Return ONLY a JSON array with this exact structure:
[
  {{
    "mark": "string",
    "location": "string",
    "width_mm": number,
    "height_mm": number,
    "fire_rating": "string",
    "material": "string"
  }}
]

If no doors are found, return an empty array [].
"""
        
        data = self._extract_with_gpt(prompt.format(context=context))
        sources = self._extract_sources(list(unique_docs))
        
        return {
            "data": data,
            "sources": sources
        }
    
    async def _extract_room_summary(self) -> Dict[str, Any]:
        """Extract room summary from documents"""
        
        queries = [
            "room schedule area floor finish",
            "room types specifications ceiling",
            "space planning room dimensions"
        ]
        
        all_docs = []
        for query in queries:
            docs = self.doc_processor.search(query, n_results=10)
            all_docs.extend(docs)
        
        unique_docs = {doc['text']: doc for doc in all_docs}.values()
        context = self._build_extraction_context(list(unique_docs))
        
        prompt = """Extract ALL rooms from the following construction documents and return a JSON array.

For each room, extract:
- name: Room name or number
- area_sqm: Floor area in square meters (convert if needed)
- floor_finish: Floor finish material
- ceiling_height_m: Ceiling height in meters (if available)
- occupancy_type: Type of occupancy (if available)

Context:
{context}

Return ONLY a JSON array with this exact structure:
[
  {{
    "name": "string",
    "area_sqm": number,
    "floor_finish": "string",
    "ceiling_height_m": number or null,
    "occupancy_type": "string or null"
  }}
]

If no rooms are found, return an empty array [].
"""
        
        data = self._extract_with_gpt(prompt.format(context=context))
        sources = self._extract_sources(list(unique_docs))
        
        return {
            "data": data,
            "sources": sources
        }
    
    async def _extract_equipment_list(self) -> Dict[str, Any]:
        """Extract MEP equipment list from documents"""
        
        queries = [
            "mechanical equipment HVAC specifications",
            "electrical equipment MEP systems",
            "plumbing fixtures equipment schedule"
        ]
        
        all_docs = []
        for query in queries:
            docs = self.doc_processor.search(query, n_results=10)
            all_docs.extend(docs)
        
        unique_docs = {doc['text']: doc for doc in all_docs}.values()
        context = self._build_extraction_context(list(unique_docs))
        
        prompt = """Extract ALL MEP equipment from the following construction documents and return a JSON array.

For each equipment item, extract:
- type: Equipment type (e.g., "HVAC", "Electrical", "Plumbing")
- description: Equipment description
- model: Model number (if available)
- location: Installation location
- specifications: Key specifications

Context:
{context}

Return ONLY a JSON array with this exact structure:
[
  {{
    "type": "string",
    "description": "string",
    "model": "string or null",
    "location": "string",
    "specifications": "string"
  }}
]

If no equipment is found, return an empty array [].
"""
        
        data = self._extract_with_gpt(prompt.format(context=context))
        sources = self._extract_sources(list(unique_docs))
        
        return {
            "data": data,
            "sources": sources
        }
    
    def _build_extraction_context(self, docs: List[Dict[str, Any]]) -> str:
        """Build context for extraction"""
        context_parts = []
        for doc in docs[:15]:  # Limit to avoid token limits
            filename = doc['metadata']['filename']
            page = doc['metadata']['page']
            text = doc['text']
            context_parts.append(f"[{filename}, Page {page}]\n{text}")
        
        return "\n\n".join(context_parts)
    
    def _extract_with_gpt(self, prompt: str) -> List[Dict[str, Any]]:
        """Use GPT to extract structured data"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a precise data extraction assistant. Extract information exactly as specified and return valid JSON only."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            result_text = response.choices[0].message.content
            
            # Parse JSON response
            try:
                # Try to parse as direct array
                data = json.loads(result_text)
                if isinstance(data, list):
                    return data
                # If it's an object, try to extract array from common keys
                for key in ['data', 'items', 'results', 'doors', 'rooms', 'equipment']:
                    if key in data and isinstance(data[key], list):
                        return data[key]
                return []
            except json.JSONDecodeError:
                # Try to extract JSON array from text
                import re
                json_match = re.search(r'\[.*\]', result_text, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                return []
                
        except Exception as e:
            print(f"Extraction error: {str(e)}")
            return []
    
    def _extract_sources(self, docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract source information"""
        sources = []
        seen = set()
        
        for doc in docs:
            filename = doc['metadata']['filename']
            page = doc['metadata']['page']
            source_key = f"{filename}_{page}"
            
            if source_key not in seen:
                sources.append({
                    "filename": filename,
                    "page": page
                })
                seen.add(source_key)
        
        return sources[:10]  # Limit sources
