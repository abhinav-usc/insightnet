"""
Parser — extracts structured sections from README and code files.

parse_readme(text) → List[Section dict]
parse_code(filename, text) → List[CodeBlock dict]
"""

import ast
import os
import re
import logging

logger = logging.getLogger(__name__)

SKIP_PATTERNS = ("LICENSE", "CHANGELOG", ".lock")


# ── Markdown helpers ─────────────────────────────────────────────────

def _strip_markdown(text: str) -> str:
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)   # links
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)           # bold
    text = re.sub(r"\*(.+?)\*", r"\1", text)               # italic
    text = re.sub(r"_(.+?)_", r"\1", text)                 # italic
    text = re.sub(r"`([^`]+)`", r"\1", text)               # inline code
    return text


# ── README parser ────────────────────────────────────────────────────

def parse_readme(text: str) -> list[dict]:
    """Split README into sections at ## headers. Returns [{section_label, content}]."""
    sections = []
    parts = re.split(r"(?=^## )", text, flags=re.MULTILINE)

    for part in parts:
        lines = part.strip().split("\n", 1)
        if not lines:
            continue

        header = lines[0].strip()
        label = header[3:].strip() if header.startswith("## ") else "Introduction"
        content = lines[1] if len(lines) > 1 else ""
        content = _strip_markdown(content).strip()

        if len(content) < 50:
            continue

        sections.append({"section_label": label, "content": content})

    return sections


# ── Code parsers ─────────────────────────────────────────────────────

def parse_code(filename: str, text: str) -> list[dict]:
    """Extract functions/classes from source code. Returns [{function_name, content, source_file, language}]."""
    basename = os.path.basename(filename)
    if any(basename.startswith(p) for p in SKIP_PATTERNS):
        return []
    if basename == "__init__.py" and not text.strip():
        return []

    ext = os.path.splitext(filename)[1].lower()
    if ext == ".py":
        return _parse_python(filename, text)
    if ext == ".r":
        return _parse_r(filename, text)
    if ext in (".js", ".ts"):
        return _parse_js_ts(filename, text)
    return []


def _parse_python(filename: str, text: str) -> list[dict]:
    blocks = []
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return blocks
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            source = ast.get_source_segment(text, node) or ""
            blocks.append({
                "function_name": node.name,
                "content": source,
                "source_file": filename,
                "language": "python",
            })
    return blocks


def _parse_r(filename: str, text: str) -> list[dict]:
    blocks = []
    for match in re.finditer(r"(\w+)\s*<-\s*function\s*\(", text):
        start = match.start()
        end = text.find("\n\n", start)
        if end == -1:
            end = min(start + 2000, len(text))
        blocks.append({
            "function_name": match.group(1),
            "content": text[start:end],
            "source_file": filename,
            "language": "R",
        })
    return blocks


def _parse_js_ts(filename: str, text: str) -> list[dict]:
    blocks = []
    patterns = [
        r"(?:export\s+)?(?:async\s+)?function\s+(\w+)",
        r"(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\(",
        r"(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?(?:\([^)]*\)|\w+)\s*=>",
    ]
    seen = set()
    for pat in patterns:
        for match in re.finditer(pat, text):
            name = match.group(1)
            if name in seen:
                continue
            seen.add(name)
            start = match.start()
            end = text.find("\n\n", start)
            if end == -1:
                end = min(start + 2000, len(text))
            ext = os.path.splitext(filename)[1]
            blocks.append({
                "function_name": name,
                "content": text[start:end],
                "source_file": filename,
                "language": "typescript" if ext == ".ts" else "javascript",
            })
    return blocks
