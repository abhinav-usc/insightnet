"""
Agent 4 — Recommendation + Synthesis.

Fetches full README for top-5, context-stuffs gpt-5.4, streams response.
run_query_pipeline(query) wraps Agent 1 → 2 → 3 → 4.
"""

import logging

from infra import openai_client
from infra.scraper import get_readme
from retrieval.query_understanding import understand_query
from retrieval.retrieval import embed_query, retrieve
from retrieval.reranker import rerank

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert in public health epidemic modeling tools.
Based on the tools provided, format your response as:

1. **BEST PICK**: [tool name] — one sentence explaining why it's the best fit.

2. **RANKED LIST** (1–5):
   For each tool include:
   - Tool name and one-line summary
   - Why it fits the query
   - A relevant code snippet (if applicable)
   - Citation: [source: owner/repo]

3. If the user's intent is "compare_tools", add a **markdown comparison table** at the end.

Be concise and cite your sources."""


def synthesize(query: str, top_results: list, intent: str):
    """Context-stuff gpt-5.4 with full READMEs and stream the response."""
    context_parts = []
    for i, result in enumerate(top_results[:5]):
        readme = get_readme(result.repo_name)
        context_parts.append(
            f"[Tool {i+1}: {result.repo_name}]\n"
            f"Relevance reason: {result.reason}\n\n"
            f"{readme[:3000]}"
        )

    context = "\n\n---\n\n".join(context_parts)
    user_msg = f"Query: {query}\nIntent: {intent}\n\n{context}"

    return openai_client.chat(
        agent="agent4",
        model="gpt-5.4",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        stream=True,
    )


def run_query_pipeline(query: str):
    """Full pipeline: Agent 1 → 2 → 3 → 4. Returns a streaming response."""
    logger.info(f"Query pipeline start: {query!r}")

    # Agent 1: Query Understanding
    plan = understand_query(query)
    logger.info(f"Intent={plan.intent}, collections={plan.preferred_collections}")

    # Agent 2: Retrieval + RRF
    embedding = embed_query(query)
    top20 = retrieve(plan, embedding)
    logger.info(f"Retrieved {len(top20)} candidates")

    # Agent 3: Re-ranking (cosine + o3 judge)
    top5 = rerank(query, embedding, top20)
    logger.info(f"Top 5: {[r.repo_name for r in top5]}")

    # Agent 4: Synthesis (streamed)
    return synthesize(query, top5, plan.intent)
