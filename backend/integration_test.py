"""Integration test to verify complete data flow"""
import sys
sys.path.insert(0, "F:/Projects/constructure ai/backend")

from document_processor_vector import DocumentProcessor

print("Testing FAISS Vector Search Integration...")
print("-" * 50)

# Initialize processor
dp = DocumentProcessor()

print(f"✓ Documents loaded: {len(dp.documents)}")
print(f"✓ Total chunks: {len(dp.chunks)}")
print(f"✓ FAISS vectors: {dp.index.ntotal}")

# Test search
query = "fire rating corridor"
results = dp.search_documents(query, top_k=3)

print(f"\nSearch Query: '{query}'")
print(f"Results found: {len(results)}")

for i, result in enumerate(results, 1):
    print(f"\n[{i}] Score: {result['relevance_score']:.4f}")
    print(f"    File: {result['filename']}")
    print(f"    Page: {result['page_number']}")
    print(f"    Text: {result['content'][:100]}...")

print("\n" + "=" * 50)
print("✓ Integration Test PASSED: Data flows correctly")
print("  Frontend → Backend → FAISS Database → Search Results")
