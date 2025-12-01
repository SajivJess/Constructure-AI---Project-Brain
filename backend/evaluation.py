from typing import Dict, Any, List
from rag_pipeline import RAGPipeline

class EvaluationSystem:
    """Simple evaluation system for RAG pipeline"""
    
    def __init__(self):
        self.rag_pipeline = RAGPipeline()
        
        # Test queries with expected answer patterns
        self.test_queries = [
            {
                "query": "What is the fire rating for corridor partitions?",
                "expected_keywords": ["fire", "rating", "corridor", "partition", "hour", "hr"],
                "category": "specifications"
            },
            {
                "query": "What flooring material is specified for the lobby?",
                "expected_keywords": ["floor", "lobby", "material", "finish"],
                "category": "materials"
            },
            {
                "query": "Are there any accessibility requirements for doors?",
                "expected_keywords": ["accessibility", "door", "ada", "requirement", "clearance"],
                "category": "compliance"
            },
            {
                "query": "What are the door dimensions?",
                "expected_keywords": ["door", "dimension", "width", "height", "mm", "size"],
                "category": "dimensions"
            },
            {
                "query": "What types of HVAC systems are specified?",
                "expected_keywords": ["hvac", "system", "mechanical", "air", "conditioning"],
                "category": "mep"
            },
            {
                "query": "What is the ceiling height in the main corridor?",
                "expected_keywords": ["ceiling", "height", "corridor", "meter", "mm"],
                "category": "dimensions"
            },
            {
                "query": "What is the wall construction specification?",
                "expected_keywords": ["wall", "construction", "partition", "specification"],
                "category": "specifications"
            },
            {
                "query": "Are there fire safety systems specified?",
                "expected_keywords": ["fire", "safety", "system", "alarm", "sprinkler", "suppression"],
                "category": "safety"
            }
        ]
    
    async def run_evaluation(self) -> Dict[str, Any]:
        """Run evaluation tests"""
        results = []
        
        for test_case in self.test_queries:
            result = await self._evaluate_query(test_case)
            results.append(result)
        
        # Calculate summary
        summary = self._calculate_summary(results)
        
        return {
            "total_queries": len(results),
            "results": results,
            "summary": summary
        }
    
    async def _evaluate_query(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate a single query"""
        query = test_case["query"]
        expected_keywords = test_case["expected_keywords"]
        
        try:
            # Run query through RAG pipeline
            response = await self.rag_pipeline.process_query(query)
            answer = response["answer"].lower()
            sources = response["sources"]
            
            # Check if answer contains expected keywords
            keyword_matches = sum(1 for keyword in expected_keywords if keyword in answer)
            keyword_score = keyword_matches / len(expected_keywords)
            
            # Check if sources are provided
            has_sources = len(sources) > 0
            
            # Check if answer is not empty or error
            has_answer = len(answer) > 20 and "error" not in answer.lower()
            
            # Determine correctness
            if keyword_score >= 0.3 and has_sources and has_answer:
                correctness = "correct"
            elif keyword_score >= 0.2 and has_answer:
                correctness = "partially_correct"
            else:
                correctness = "incorrect"
            
            return {
                "query": query,
                "category": test_case["category"],
                "answer": response["answer"][:200] + "..." if len(response["answer"]) > 200 else response["answer"],
                "sources_count": len(sources),
                "keyword_score": round(keyword_score, 2),
                "correctness": correctness,
                "has_sources": has_sources
            }
            
        except Exception as e:
            return {
                "query": query,
                "category": test_case["category"],
                "answer": f"Error: {str(e)}",
                "sources_count": 0,
                "keyword_score": 0.0,
                "correctness": "error",
                "has_sources": False
            }
    
    def _calculate_summary(self, results: List[Dict[str, Any]]) -> Dict[str, int]:
        """Calculate summary statistics"""
        summary = {
            "correct": 0,
            "partially_correct": 0,
            "incorrect": 0,
            "error": 0,
            "total_with_sources": 0
        }
        
        for result in results:
            correctness = result["correctness"]
            if correctness in summary:
                summary[correctness] += 1
            
            if result["has_sources"]:
                summary["total_with_sources"] += 1
        
        return summary
