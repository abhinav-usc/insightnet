"""
Agent 1 — Query Understanding.

understand_query(query) → QueryPlan via gpt-4.1-mini (json_object format).
"""

import json
import logging

from infra import openai_client
from models import QueryPlan

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You analyze search queries for a public health epidemic modeling tools database.
Return a JSON object with these fields:
- intent: "find_tool" | "compare_tools" | "explain_tool"
- domain: the public health domain (e.g. "influenza", "COVID-19", "respiratory illness")
- keywords: list of search keywords
- preferred_collections: list from ["tool_profiles", "readme_chunks", "code_chunks"]
- filters: optional dict of filters (e.g. {"difficulty": "low"})"""


def understand_query(query: str) -> QueryPlan:
    try:
        raw = openai_client.chat(
            agent="agent1",
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": query},
            ],
            json_mode=True,
        )
        data = json.loads(raw)
        return QueryPlan(
            intent=data.get("intent", "find_tool"),
            domain=data.get("domain", ""),
            keywords=data.get("keywords", []),
            preferred_collections=data.get("preferred_collections", ["tool_profiles", "readme_chunks", "code_chunks"]),
            filters=data.get("filters", {}),
        )
    except Exception as e:
        logger.error(f"Query understanding failed: {e}")
        return QueryPlan(intent="find_tool", keywords=query.split()[:5])
