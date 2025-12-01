"""
Tests for structured extraction service
"""
import pytest
from app.services.extraction_service import ExtractionService

@pytest.fixture
def extraction_service():
    """Create extraction service instance"""
    return ExtractionService()

def test_door_schedule_extraction(extraction_service):
    """Test door schedule extraction"""
    context_chunks = [
        {
            "content": """
            Door Schedule:
            D-101: Level 1 Corridor, 900mm x 2100mm, 1 HR Fire Rating, Hollow Metal
            D-102: Level 1 Office, 800mm x 2100mm, 20 min, Wood
            """,
            "file_name": "door_schedule.pdf",
            "page_number": 5
        }
    ]
    
    result = extraction_service.extract_door_schedule(context_chunks)
    
    assert isinstance(result, dict)
    assert "data" in result
    assert "sources" in result
    assert len(result["data"]) > 0
    
    # Check first door entry
    door = result["data"][0]
    assert "mark" in door
    assert "location" in door
    assert "width_mm" in door
    assert "height_mm" in door

def test_room_schedule_extraction(extraction_service):
    """Test room schedule extraction"""
    context_chunks = [
        {
            "content": """
            Room Schedule:
            101: Lobby, 50.5 sqm, Ceramic Tile, Level 1
            102: Office, 15.2 sqm, Carpet, Level 1
            """,
            "file_name": "room_schedule.pdf",
            "page_number": 3
        }
    ]
    
    result = extraction_service.extract_room_schedule(context_chunks)
    
    assert isinstance(result, dict)
    assert "data" in result
    assert len(result["data"]) > 0
    
    room = result["data"][0]
    assert "number" in room
    assert "name" in room
    assert "area" in room
    assert "finish" in room

def test_equipment_list_extraction(extraction_service):
    """Test equipment list extraction"""
    context_chunks = [
        {
            "content": """
            Equipment List:
            - HVAC-01: Rooftop Unit, 10 tons, Carrier, Mechanical Room
            - HVAC-02: Split System, 3 tons, Trane, Office Area
            """,
            "file_name": "mep_specs.pdf",
            "page_number": 12
        }
    ]
    
    result = extraction_service.extract_equipment_list(context_chunks)
    
    assert isinstance(result, dict)
    assert "data" in result
    assert len(result["data"]) > 0
    
    equipment = result["data"][0]
    assert "tag" in equipment
    assert "type" in equipment
    assert "location" in equipment

def test_extract_structured_data_router(extraction_service):
    """Test the main router that determines extraction type"""
    query = "Generate a door schedule"
    
    # Should detect door schedule extraction
    result = extraction_service.extract_structured_data(query, [])
    
    assert isinstance(result, dict)
    assert "data" in result
    assert "sources" in result
    assert "extraction_type" in result

def test_invalid_extraction_type(extraction_service):
    """Test handling of unsupported extraction types"""
    query = "Extract something weird"
    
    result = extraction_service.extract_structured_data(query, [])
    
    # Should handle gracefully
    assert isinstance(result, dict)

def test_empty_context_handling(extraction_service):
    """Test extraction with no context chunks"""
    result = extraction_service.extract_door_schedule([])
    
    assert isinstance(result, dict)
    assert "data" in result
    # Should return empty or indicate no data found
    assert len(result["data"]) == 0 or "error" in result

def test_source_citation_in_extraction(extraction_service):
    """Test that extractions include proper source citations"""
    context_chunks = [
        {
            "content": "D-101: Door info here",
            "file_name": "test.pdf",
            "page_number": 5
        }
    ]
    
    result = extraction_service.extract_door_schedule(context_chunks)
    
    assert "sources" in result
    assert len(result["sources"]) > 0
    assert result["sources"][0]["file_name"] == "test.pdf"
    assert result["sources"][0]["page_number"] == 5

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
