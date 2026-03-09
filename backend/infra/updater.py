"""
Repo Update Detector — commit SHA polling + re-ingestion.

check_for_updates(): one-shot check all repos
reingest_repo():     re-scrape → delete stale Chroma entries → re-ingest
start_scheduler():   daily cron at 02:00
"""

import time
import logging
from concurrent.futures import ThreadPoolExecutor, TimeoutError

import httpx
import schedule

from infra.db import supabase, GITHUB_TOKEN, col_profiles, col_readme, col_code
from infra.scraper import load_repo_list, scrape_repo, save_repo
from ingestion.parser import parse_readme, parse_code
from ingestion.summarizer import summarize_repo, chunk_and_embed

logger = logging.getLogger(__name__)

_gh = httpx.Client(
    timeout=httpx.Timeout(30, connect=10),
    headers={"Authorization": f"Bearer {GITHUB_TOKEN}"} if GITHUB_TOKEN else {},
)


def _get_latest_sha(repo_name: str) -> str | None:
    try:
        resp = _gh.get(f"https://api.github.com/repos/{repo_name}/commits?per_page=1")
        if resp.status_code == 200:
            data = resp.json()
            if data:
                return data[0]["sha"]
    except Exception as e:
        logger.error(f"Failed to get SHA for {repo_name}: {e}")
    return None


def _get_stored_sha(repo_name: str) -> str | None:
    result = supabase.table("repos").select("commit_sha").eq("repo_name", repo_name).limit(1).execute()
    if result.data:
        return result.data[0].get("commit_sha")
    return None


def _log_ingestion(repo_name: str, trigger: str, status: str, commit_sha: str = ""):
    try:
        supabase.table("ingestion_log").insert({
            "repo_name": repo_name,
            "trigger": trigger,
            "status": status,
            "commit_sha": commit_sha,
        }).execute()
    except Exception as e:
        logger.error(f"Failed to log ingestion for {repo_name}: {e}")


def _delete_chroma_entries(repo_name: str):
    """Delete stale ChromaDB entries for a repo across all collections."""
    for col in (col_profiles, col_readme, col_code):
        try:
            existing = col.get(where={"repo_name": repo_name})
            if existing["ids"]:
                col.delete(ids=existing["ids"])
        except Exception:
            pass


def reingest_repo(repo_name: str):
    """Full re-ingestion: scrape → delete old Chroma → summarize → chunk → embed."""
    logger.info(f"Re-ingesting {repo_name}...")
    record = scrape_repo(f"https://github.com/{repo_name}")
    if record is None:
        logger.warning(f"Re-ingest failed for {repo_name}: scrape returned None")
        _log_ingestion(repo_name, "update", "failed")
        return

    _delete_chroma_entries(repo_name)
    save_repo(record)

    sections = parse_readme(record.readme_text)
    code_blocks = []
    for fn, content in record.file_contents.items():
        code_blocks.extend(parse_code(fn, content))

    summarize_repo(record.repo_name, record.readme_text, list(record.file_contents.keys()))
    chunk_and_embed(record.repo_name, sections, code_blocks)

    _log_ingestion(record.repo_name, "update", "success", record.commit_sha)
    logger.info(f"Re-ingested {repo_name}")


def check_for_updates(repo_list: list[str]):
    """One-shot: compare commit SHA for each repo, re-ingest if changed."""
    for url in repo_list:
        parts = url.rstrip("/").split("/")
        repo_name = f"{parts[-2]}/{parts[-1]}"

        latest = _get_latest_sha(repo_name)
        stored = _get_stored_sha(repo_name)

        if latest and latest != stored:
            logger.info(f"Update detected: {repo_name}")
            reingest_repo(repo_name)
        else:
            logger.info(f"No update: {repo_name}")
            _log_ingestion(repo_name, "scheduled_check", "skipped")

        time.sleep(0.5)


def start_scheduler():
    """Run daily update check at 02:00."""
    repos = load_repo_list("repos.txt")
    schedule.every().day.at("02:00").do(check_for_updates, repos)
    logger.info("Scheduler started — daily checks at 02:00")
    while True:
        schedule.run_pending()
        time.sleep(60)
