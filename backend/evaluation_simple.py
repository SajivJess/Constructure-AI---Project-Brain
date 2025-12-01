from typing import List, Dict, Any
import asyncio

class EvaluationSystem:
    """Evaluation system for testing RAG quality with predefined test cases"""
    
    def __init__(self):
        # Test queries with expected answers and keywords to verify
        self.test_cases = [
            {
                "query": "What is the fire rating for corridor partitions?",
                "expected_keywords": ["1 hour", "partition", "corridor"],
                "category": "specification_lookup"
            },
            {
                "query": "What flooring material is specified for corridors?",
                "expected_keywords": ["vinyl", "tile", "flooring"],
                "category": "material_spec"
            },
            {
                "query": "What is the main entrance door specification?",
                "expected_keywords": ["door", "entrance", "900", "2100"],
                "category": "door_spec"
            },
            {
                "query": "Generate a door schedule",
                "expected_keywords": ["door", "schedule", "mark"],
                "category": "structured_extraction"
            },
            {
                "query": "What are the accessibility requirements for doors?",
                "expected_keywords": ["accessibility", "door", "requirement"],
                "category": "code_compliance"
            },
            {
                "query": "List all doors with 1 hour fire rating",
                "expected_keywords": ["fire", "rating", "1 hour", "door"],
                "category": "filtered_query"
            },
            {
                "query": "What is the ceiling height in corridors?",
                "expected_keywords": ["ceiling", "height", "corridor", "2700"],
                "category": "measurement_lookup"
            },
            {
                "query": "What materials are used for corridor walls?",
                "expected_keywords": ["wall", "corridor", "paint", "finish"],
                "category": "finish_spec"
            }
        ]
    
    async def run_evaluation(self, rag_pipeline) -> Dict[str, Any]:
        """Run evaluation tests through the RAG pipeline"""
        results = []
        
        for test_case in self.test_cases:
            try:
                # Run query through RAG pipeline
                response = await rag_pipeline.process_query(test_case["query"])
                
                # Evaluate answer
                answer = response.get("answer", "").lower()
                sources = response.get("sources", [])
                
                # Check for expected keywords
                keywords_found = sum(
                    1 for kw in test_case["expected_keywords"] 
                    if kw.lower() in answer
                )
                
                keyword_score = keywords_found / len(test_case["expected_keywords"]) if test_case["expected_keywords"] else 0
                
                # Evaluate quality
                has_sources = len(sources) > 0
                has_answer = len(answer) > 50
                
                if keyword_score >= 0.6 and has_sources and has_answer:
                    verdict = "correct"
                elif keyword_score >= 0.4 or has_sources:
                    verdict = "partially_correct"
                else:
                    verdict = "incorrect"
                
                results.append({
                    "query": test_case["query"],
                    "category": test_case["category"],
                    "answer": answer[:200] + "..." if len(answer) > 200 else answer,
                    "sources_count": len(sources),
                    "keyword_score": round(keyword_score, 2),
                    "correctness": verdict,
                    "confidence": response.get("confidence", "unknown")
                })
                
            except Exception as e:
                results.append({
                    "query": test_case["query"],
                    "category": test_case["category"],
                    "correctness": "error",
                    "answer": f"Error: {str(e)}",
                    "sources_count": 0,
                    "keyword_score": 0
                })
        
        # Calculate summary statistics
        correctness_values = [r.get("correctness") for r in results]
        summary = {
            "correct": correctness_values.count("correct"),
            "partially_correct": correctness_values.count("partially_correct"),
            "incorrect": correctness_values.count("incorrect"),
            "errors": correctness_values.count("error")
        }
        
        success_rate = (summary["correct"] + summary["partially_correct"] * 0.5) / len(results) if results else 0
        
        return {
            "total_queries": len(results),
            "results": results,
            "summary": summary,
            "success_rate": round(success_rate, 2),
            "evaluation_complete": True
        }
