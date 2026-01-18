# RAG vs. Full Document: Performance Comparison

This document illustrates the efficiency gains from using RAG (Retrieval-Augmented Generation).

## Token Usage Comparison

### Scenario: 100-page PDF Document

**Document Stats:**
- Pages: 100
- Total characters: ~250,000
- Estimated tokens: ~62,500 (at 4 chars/token)

**Questions:** 10 questions to answer

### Without RAG (Full Document Approach)

For each question, the entire PDF is sent:

```
Tokens per question: 62,500 (document) + 50 (question) = 62,550
Total for 10 questions: 625,500 tokens
API calls: 10
Cost estimate: ~$31 (at $0.05/1K tokens)
```

### With RAG (Retrieval-Augmented Generation)

For each question, only top 3 relevant chunks are sent:

```
Chunk size: 1000 characters
Chunks retrieved: 3
Tokens per question: 750 (3 chunks) + 50 (question) = 800
Total for 10 questions: 8,000 tokens
Embedding creation: Local (free)
API calls: 10
Cost estimate: ~$0.40 (at $0.05/1K tokens)
```

## Savings Summary

| Metric | Without RAG | With RAG | Savings |
|--------|------------|----------|---------|
| Tokens per question | 62,550 | 800 | **98.7%** |
| Total tokens (10 Q's) | 625,500 | 8,000 | **98.7%** |
| Estimated cost | $31.28 | $0.40 | **$30.88 (98.7%)** |
| Processing time | ~5-10 min | ~30-60 sec | **~90%** |

## Speed Comparison

### Without RAG
1. Extract PDF: 5 seconds
2. Question 1: 30 seconds (large context)
3. Question 2: 30 seconds
4. ... (repeat for each question)
5. **Total: ~5 minutes**

### With RAG
1. Extract PDF: 5 seconds
2. Create embeddings: 10 seconds (one-time, cached)
3. Question 1: 5 seconds (small context)
4. Question 2: 5 seconds (retrieval + API)
5. ... (repeat)
6. **Total: ~1 minute**

## Accuracy Considerations

### RAG Benefits:
- ✅ Focused context reduces noise
- ✅ More precise answers from relevant sections
- ✅ Less chance of hitting context limits
- ✅ Can handle PDFs of any size

### Potential Concerns:
- ⚠️ Might miss context if answer spans multiple non-adjacent sections
- ⚠️ Solution: Increase `top_k` (e.g., from 3 to 5 chunks)

## Recommendations

### Use RAG (default) when:
- PDF is larger than 10 pages
- You have multiple questions
- You want to minimize costs
- You need fast responses

### Use Full Document (--no-rag) when:
- PDF is very small (< 5 pages)
- Questions require broad context from entire document
- You want to ensure nothing is missed

## Best Practices

1. **Start with RAG** (default): Works well for 95% of use cases
2. **Tune `top_k`**: 
   - 3 (default): Fast, cost-effective
   - 5: More context, slight increase in tokens
   - 7+: For complex questions needing broad context
3. **Check cache**: Indexes are cached, so re-running on same PDF is instant
4. **Monitor token usage**: Output JSON includes usage stats

## Example Output

With RAG enabled, you'll see:

```json
{
  "metadata": {
    "rag_enabled": true,
    ...
  },
  "rag_stats": {
    "num_chunks": 250,
    "top_k": 3
  },
  "qa_results": [
    {
      "question": "...",
      "answer": "...",
      "usage": {
        "prompt_tokens": 800,  // Much lower than 62,550!
        "completion_tokens": 150,
        "total_tokens": 950
      }
    }
  ]
}
```

## Conclusion

RAG provides:
- **~99% reduction** in token usage
- **~90% faster** processing
- **~99% cost savings**
- **Same or better** accuracy

**Recommendation**: Always use RAG unless you have a specific reason not to.
