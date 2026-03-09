"""
Chunker -- split parsed sections into token-bounded chunks.

chunk_readme:  512-token windows, 64-token overlap, one Chunk per window.
chunk_code:    one Chunk per function/class, truncate at 1024 tokens.
"""

import logging
import tiktoken
from models import Chunk

logger = logging.getLogger(__name__)

_enc = tiktoken.get_encoding("cl100k_base")

WINDOW = 512
OVERLAP = 64


def chunk_readme(sections: list[dict], repo_name: str) -> list[Chunk]:
    chunks: list[Chunk] = []

    for si, section in enumerate(sections):
        text = section["content"]
        if not text.strip():
            continue

        tokens = _enc.encode(text)

        if len(tokens) <= WINDOW:
            chunks.append(Chunk(
                id=f"{repo_name}::README.md::{si}_0",
                repo_name=repo_name,
                file_path="README.md",
                chunk_type="readme",
                section_header=section["section_label"],
                content=text,
                token_count=len(tokens),
            ))
        else:
            start = 0
            ci = 0
            while start < len(tokens):
                end = min(start + WINDOW, len(tokens))
                window = tokens[start:end]
                chunks.append(Chunk(
                    id=f"{repo_name}::README.md::{si}_{ci}",
                    repo_name=repo_name,
                    file_path="README.md",
                    chunk_type="readme",
                    section_header=section["section_label"],
                    content=_enc.decode(window),
                    token_count=len(window),
                ))
                ci += 1

                # Reached the end -- stop
                if end == len(tokens):
                    break

                # Advance with overlap, but always move forward by at least 1
                next_start = end - OVERLAP
                if next_start <= start:
                    break
                start = next_start

    if chunks:
        avg = sum(c.token_count for c in chunks) // len(chunks)
        logger.info(f"{repo_name}: {len(chunks)} README chunks (avg {avg} tok)")
    return chunks


def chunk_code(code_blocks: list[dict], repo_name: str) -> list[Chunk]:
    chunks: list[Chunk] = []

    for block in code_blocks:
        content = block["content"]
        if not content.strip():
            continue

        tokens = _enc.encode(content)
        if len(tokens) > 1024:
            logger.warning(f"{block['function_name']} in {block['source_file']}: {len(tokens)} tok, truncating to 1024")
            tokens = tokens[:1024]
            content = _enc.decode(tokens)

        chunks.append(Chunk(
            id=f"{repo_name}::{block['source_file']}::{block['function_name']}",
            repo_name=repo_name,
            file_path=block["source_file"],
            chunk_type="code",
            function_name=block["function_name"],
            content=content,
            token_count=len(tokens),
        ))

    if chunks:
        logger.info(f"{repo_name}: {len(chunks)} code chunks")
    return chunks
