import sys
sys.path.insert(0, "F:/Projects/constructure ai/backend")
from document_processor_vector import DocumentProcessor

# Test FAISS search
doc_processor = DocumentProcessor()
print(f" DocumentProcessor loaded")
print(f"  Total vectors in FAISS: {doc_processor.index.ntotal}")
print(f"  Total chunks: {len(doc_processor.chunks)}")
print(f"  Total documents: {len(doc_processor.documents)}")

# Test search
query = "fire rating corridor partition"
print(f"\n Searching for: '{query}'")
results = doc_processor.search_documents(query, top_k=3)
print(f"  Results found: {len(results)}")

for i, result in enumerate(results, 1):
    print(f"\n  Result {i}:")
    print(f"    File: {result['filename']}")
    print(f"    Page: {result['page_number']}")
    print(f"    Score: {result['relevance_score']:.4f}")
    print(f"    Preview: {result['content'][:150]}...")
