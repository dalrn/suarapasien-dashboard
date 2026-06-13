"""
LLM-based structured extraction via Anthropic tool use.

Each chunk → one API call → list of aspect findings (dimension, polarity, sub_issue, quote).
Results are saved incrementally to outputs/absa_raw.jsonl so runs are resumable.
"""

from __future__ import annotations
import json
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import anthropic
from tqdm import tqdm

from .prompts import SYSTEM_PROMPT, EXTRACTION_TOOL

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

# Haiku is fast and cheap (~$2–3 for the full 8641-review run).
# Switch to "claude-sonnet-4-6" here if prototype quality needs a boost.
MODEL = "claude-haiku-4-5-20251001"
MAX_TOKENS = 1024

OUTPUTS = Path(__file__).resolve().parent.parent / "outputs"

Finding = dict[str, str]


# ---------------------------------------------------------------------------
# Single-chunk extraction
# ---------------------------------------------------------------------------

def classify_chunk(chunk_text: str, client: anthropic.Anthropic) -> list[Finding]:
    """
    Send one chunk to Claude and return a list of aspect findings.
    Returns [] if the chunk contains no service-quality content.
    Raises anthropic.APIError on unrecoverable errors (caller handles retries).
    """
    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT,
        tools=[EXTRACTION_TOOL],
        tool_choice={"type": "tool", "name": "extract_findings"},
        messages=[{"role": "user", "content": chunk_text}],
    )
    for block in response.content:
        if block.type == "tool_use":
            findings = block.input.get("findings", [])
            # Occasionally the SDK returns the list as a JSON string; parse it.
            if isinstance(findings, str):
                try:
                    findings = json.loads(findings)
                except json.JSONDecodeError:
                    return []   # malformed (unescaped quote in value); treat as empty
            return findings
    return []


# ---------------------------------------------------------------------------
# Batch extraction with resume support
# ---------------------------------------------------------------------------

def classify_batch(
    chunks: list[dict],
    client: anthropic.Anthropic,
    *,
    delay_seconds: float = 0.3,
    max_retries: int = 3,
    out_file: str = "absa_raw.jsonl",
) -> list[dict]:
    """
    Classify a list of chunk dicts (output of preprocess.prepare_chunks).
    Returns the same dicts with a 'findings' key added to each.

    Saves every result to outputs/<out_file> as it goes — safe to interrupt
    and resume; already-processed (review_id, chunk_index) pairs are skipped.
    """
    OUTPUTS.mkdir(exist_ok=True)
    out_path = OUTPUTS / out_file

    # Load already-processed keys so we can resume interrupted runs
    done_keys: set[tuple[str, int]] = set()
    if out_path.exists():
        with open(out_path, encoding="utf-8") as f:
            for line in f:
                try:
                    rec = json.loads(line)
                    done_keys.add((rec["review_id"], rec["chunk_index"]))
                except json.JSONDecodeError:
                    pass
        if done_keys:
            print(f"Resuming: {len(done_keys)} chunks already done, skipping.")

    results: list[dict] = []
    n_total = len(chunks)

    with open(out_path, "a", encoding="utf-8") as f:
        for i, chunk in enumerate(tqdm(chunks, total=n_total, desc="Classifying chunks")):
            key = (chunk["review_id"], chunk["chunk_index"])
            if key in done_keys:
                continue

            findings: list[Finding] = []
            for attempt in range(max_retries):
                try:
                    findings = classify_chunk(chunk["chunk_text"], client)
                    break
                except anthropic.RateLimitError:
                    wait = 10 * (2 ** attempt)
                    print(f"  [chunk {i+1}] Rate limit — waiting {wait}s...")
                    time.sleep(wait)
                except anthropic.APIError as e:
                    print(f"  [chunk {i+1}] API error (attempt {attempt+1}): {e}")
                    if attempt == max_retries - 1:
                        findings = []   # give up, record as empty

            record = {**chunk, "findings": findings}
            results.append(record)
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            f.flush()

            if (i + 1) % 25 == 0 or (i + 1) == n_total:
                n_with = sum(1 for r in results if r["findings"])
                print(f"  {i+1}/{n_total}  |  {n_with} chunks with findings so far")

            time.sleep(delay_seconds)

    return results


# ---------------------------------------------------------------------------
# Concurrent batch extraction (for the full ~9k-chunk run)
# ---------------------------------------------------------------------------

class _ChunkFailed(Exception):
    """Raised when a chunk could not be classified after all retries.

    The chunk is NOT written to disk so that a resume run retries it — this is
    what keeps a transient API failure from being silently recorded as an empty
    (no-findings) result, which would otherwise corrupt the dataset.
    """


def classify_batch_concurrent(
    chunks: list[dict],
    client: anthropic.Anthropic,
    *,
    max_workers: int = 5,
    max_retries: int = 5,
    out_file: str = "absa_raw.jsonl",
) -> list[dict]:
    """
    Concurrent version of classify_batch for large runs (full dataset).
    Resumable, per-chunk retry with backoff, incremental flush.

    IMPORTANT — failure handling: a chunk that still errors after `max_retries`
    is NOT written to disk; it is counted as failed and left for the next resume
    run to retry. Only genuine model results (including a real empty findings
    list) are persisted. This prevents the silent-empty corruption where a
    rate-limited/failed call was saved as "no findings".
    """
    OUTPUTS.mkdir(exist_ok=True)
    out_path = OUTPUTS / out_file

    # Resume: skip already-processed (review_id, chunk_index) pairs
    done_keys: set[tuple[str, int]] = set()
    if out_path.exists():
        with open(out_path, encoding="utf-8") as f:
            for line in f:
                try:
                    rec = json.loads(line)
                    done_keys.add((rec["review_id"], rec["chunk_index"]))
                except json.JSONDecodeError:
                    pass
        if done_keys:
            print(f"Resuming: {len(done_keys)} chunks already done, skipping.")

    todo = [c for c in chunks if (c["review_id"], c["chunk_index"]) not in done_keys]
    if not todo:
        print("Nothing to do — all chunks already processed.")
        return []

    write_lock = threading.Lock()
    results: list[dict] = []
    n_failed = 0

    def work(chunk: dict) -> dict:
        last_err: Exception | None = None
        for attempt in range(max_retries):
            try:
                findings = classify_chunk(chunk["chunk_text"], client)
                return {**chunk, "findings": findings}
            except anthropic.RateLimitError as e:
                last_err = e
                # honour Retry-After if present, else exponential backoff
                wait = 15 * (2 ** attempt)
                retry_after = getattr(getattr(e, "response", None), "headers", {})
                try:
                    wait = max(wait, float(retry_after.get("retry-after", 0)))
                except (ValueError, AttributeError):
                    pass
                time.sleep(wait)
            except anthropic.APIError as e:
                last_err = e
                time.sleep(5 * (2 ** attempt))
        # exhausted retries — do NOT fabricate an empty result
        raise _ChunkFailed(str(last_err))

    with open(out_path, "a", encoding="utf-8") as f:
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = {pool.submit(work, c): c for c in todo}
            for fut in tqdm(as_completed(futures), total=len(todo), desc="Classifying (concurrent)"):
                try:
                    record = fut.result()
                except _ChunkFailed:
                    n_failed += 1
                    continue   # leave unprocessed; resume will retry
                with write_lock:
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")
                    f.flush()
                    results.append(record)

    n_with = sum(1 for r in results if r["findings"])
    print(f"Selesai: {len(results)} chunk baru diproses, {n_with} berisi temuan.")
    if n_failed:
        print(f"⚠ {n_failed} chunk GAGAL (tidak ditulis) — jalankan ulang sel ini "
              f"untuk mencoba lagi chunk yang gagal.")
    return results
