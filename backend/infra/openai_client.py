"""
Shared OpenAI wrapper — retry on 429, exponential backoff, usage logging.
All agents go through chat() and embed(). No raw openai imports elsewhere.
"""

import json
import time
import logging
import threading
from datetime import datetime, timezone

import httpx as _httpx
from openai import OpenAI

from infra.db import OPENAI_API_KEY

logger = logging.getLogger(__name__)

client = OpenAI(
    api_key=OPENAI_API_KEY,
    timeout=_httpx.Timeout(90, connect=10),
    max_retries=0,
)

USAGE_LOG_FILE = "usage.jsonl"
_log_lock = threading.Lock()


def _log_usage(agent: str, model: str, prompt_tokens: int, completion_tokens: int):
    entry = {
        "agent": agent,
        "model": model,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    try:
        with _log_lock:
            with open(USAGE_LOG_FILE, "a") as f:
                f.write(json.dumps(entry) + "\n")
    except OSError:
        pass


def chat(
    agent: str,
    model: str,
    messages: list,
    json_mode: bool = False,
    stream: bool = False,
) -> str:
    """Call OpenAI chat completions with retry on 429."""
    kwargs = {"model": model, "messages": messages}
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    if stream:
        kwargs["stream"] = True

    for attempt in range(3):
        try:
            logger.info(f"[{agent}] {model} attempt {attempt + 1}...")
            resp = client.chat.completions.create(**kwargs)

            if stream:
                return resp  # caller iterates the stream

            usage = resp.usage
            _log_usage(agent, model, usage.prompt_tokens, usage.completion_tokens)
            logger.info(f"[{agent}] done — {usage.prompt_tokens}+{usage.completion_tokens} tok")
            return resp.choices[0].message.content

        except Exception as e:
            if "429" in str(e) and attempt < 2:
                wait = 2 ** (attempt + 1)
                logger.warning(f"[{agent}] 429 — retrying in {wait}s")
                time.sleep(wait)
            else:
                raise


def embed(texts: list[str]) -> list[list[float]]:
    """Batch-embed with text-embedding-3-large (100 per request, retry on 429)."""
    all_embeddings: list[list[float]] = []

    for i in range(0, len(texts), 100):
        batch = texts[i : i + 100]
        for attempt in range(3):
            try:
                resp = client.embeddings.create(
                    model="text-embedding-3-large",
                    input=batch,
                )
                all_embeddings.extend([item.embedding for item in resp.data])
                break
            except Exception as e:
                if "429" in str(e) and attempt < 2:
                    wait = 2 ** (attempt + 1)
                    logger.warning(f"Embed 429 — retrying in {wait}s")
                    time.sleep(wait)
                else:
                    raise

    return all_embeddings
