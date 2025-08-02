# Embedder API Specification

## Critical Requirements Documentation

This document defines the mandatory API specifications for the `core.embedding.Embedder` class to ensure system compatibility.

## ⚠️ CRITICAL: Query Method Return Format

**REQUIREMENT**: The `Embedder.query()` method MUST return a 4-tuple format for proper system operation.

### Required Format

```python
(chunk_text, file_path, chunk_id, score)
Format Details
Position	Element	Type	Description
0	chunk_text	str	The actual text content of the chunk
1	file_path	str	Relative path to the source file
2	chunk_id	int	Unique identifier for the chunk
3	score	float	FAISS distance/similarity score
Example Return Value
[
    ("Modern Web Application Architecture 1. Frontend...", "web_architecture.txt", 3, 1.968598484992981),
    ("Database design patterns include...", "database_guide.txt", 15, 2.123456789),
    ("API versioning strategies...", "api_design.txt", 7, 2.456789012)
]
Why This Format is Required
1. UI Citation Display
The Streamlit UI (app.py) expects exactly this format to display search results with proper citations:

chunk_text: Displayed as the main content
file_path: Used for citation links
chunk_id: Internal tracking
score: Relevance ranking
2. Test Suite Compatibility
The comprehensive test suite (test_complete_system.py) validates this format:
query_works = len(results) > 0 and len(results[0]) == 4  # 4-tuple format
3. System Integration
Other components that depend on this format:

watch.py (EmbeddingAdapter)
ask.py (answer generation)
Any future search integrations
Implementation Reference
Current Correct Implementation in embedding.py:

def query(self, query: str, k: int = 5):
    # ... [FAISS search logic] ...
    
    # Return results in 4-tuple format: (chunk_text, file_path, chunk_id, score)
    results = []
    for i, target_id in enumerate(target_ids):
        if target_id in id_to_row:
            file_path, chunk_text = id_to_row[target_id]
            score = float(distances[0][i])  # Get the distance/score from FAISS
            results.append((chunk_text, file_path, target_id, score))
        else:
            results.append((None, None, target_id, float('inf')))
    
    return results

Troubleshooting
Common Issues
Test Failure: "Query failed or wrong format"

Symptom: Test suite shows failing search functionality
Cause: Query method returning wrong tuple format (e.g., 2-tuple instead of 4-tuple)
Solution: Verify query() method returns 4-tuple format as specified above
UI Citation Display Issues

Symptom: Search results show without proper file citations
Cause: Missing file_path or incorrect tuple order
Solution: Ensure tuple order matches specification
Validation Script
Use this script to verify the format:

from core.embedding import Embedder

# Test the format
em = Embedder()
results = em.query('test query', k=1)

if results:
    result = results[0]
    assert len(result) == 4, f"Expected 4-tuple, got {len(result)}-tuple"
    chunk_text, file_path, chunk_id, score = result
    print("✅ Format validation passed")
    print(f"Format: ({type(chunk_text).__name__}, {type(file_path).__name__}, {type(chunk_id).__name__}, {type(score).__name__})")
else:
    print("❌ No results returned")

Version History
v1.0 (2025-08-02): Initial specification established
v1.1 (2025-08-02): Added troubleshooting and validation sections
Related Files
embedding.py - Main implementation
test_complete_system.py - Format validation tests
app.py - UI consumer of this format
watch.py - Real-time search integration
⚠️ WARNING: Changing this format will break UI functionality and test suite. Any modifications require updating all dependent components.
```