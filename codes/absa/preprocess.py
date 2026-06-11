"""
Text normalization and chunking for ABSA extraction.

Chunking strategy:
  - Reviews <= CHUNK_THRESHOLD chars: sent as a single unit (covers ~90% of data).
  - Reviews > CHUNK_THRESHOLD chars: split first on paragraph breaks (\n), then
    on sentence boundaries if a paragraph is still too long.
  - This keeps each chunk self-contained so the LLM has full context per call.
"""

from __future__ import annotations
import re
import pandas as pd
from pathlib import Path

import tqdm

CHUNK_THRESHOLD = 1000   # chars; below this the whole review is one chunk
MAX_CHUNK_CHARS = 700    # target max chars per chunk when splitting is needed


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------

def normalize(text: str) -> str:
    """Minimal cleanup: collapse excess whitespace, strip. Preserve original casing and punctuation."""
    text = re.sub(r'\n{3,}', '\n\n', text)   # 3+ newlines → 2
    text = re.sub(r'[ \t]+', ' ', text)       # multiple spaces/tabs → one space
    return text.strip()


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------

def _split_on_sentences(text: str) -> list[str]:
    """Fallback: split on sentence-ending punctuation when no paragraph breaks exist."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks: list[str] = []
    current = ""
    for sent in sentences:
        if len(current) + len(sent) + 1 <= MAX_CHUNK_CHARS:
            current = (current + " " + sent).strip() if current else sent
        else:
            if current:
                chunks.append(current)
            current = sent
    if current:
        chunks.append(current)
    return chunks or [text]


def split_into_chunks(text: str) -> list[str]:
    """
    Split text into LLM-ready chunks.
    Short reviews (<= CHUNK_THRESHOLD) are returned as-is.
    Long reviews are split on paragraph breaks first, sentence breaks as fallback.
    """
    if len(text) <= CHUNK_THRESHOLD:
        return [text]

    paragraphs = [p.strip() for p in re.split(r'\n+', text) if p.strip()]
    if not paragraphs:
        return _split_on_sentences(text)

    chunks: list[str] = []
    current = ""
    for para in paragraphs:
        if not current:
            current = para
        elif len(current) + len(para) + 1 <= MAX_CHUNK_CHARS:
            current += "\n" + para
        else:
            chunks.append(current)
            current = para
    if current:
        chunks.append(current)

    # If any chunk is still over MAX_CHUNK_CHARS (e.g. a single huge paragraph),
    # fall back to sentence splitting for that chunk.
    final: list[str] = []
    for chunk in chunks:
        if len(chunk) > MAX_CHUNK_CHARS:
            final.extend(_split_on_sentences(chunk))
        else:
            final.append(chunk)

    return final or [text]


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def prepare_chunks(df: pd.DataFrame) -> list[dict]:
    """
    Convert the reviews DataFrame into a flat list of chunk dicts.
    Each dict carries all metadata needed to reconstruct puskesmas profiles later.

    Schema:
        chunk_text    : str   — the text to send to the LLM
        review_id     : str
        puskesmas_id  : str
        puskesmas_name: str
        wilayah       : str
        rating        : int
        chunk_index   : int   — 0-based index within the review
        n_chunks      : int   — total chunks this review was split into
    """
    records: list[dict] = []
    for _, row in df.iterrows():
        text = normalize(str(row['review_text']))
        chunks = split_into_chunks(text)
        n = len(chunks)
        for i, chunk in enumerate(chunks):
            records.append({
                'chunk_text':     chunk,
                'review_id':      str(row['review_id']),
                'puskesmas_id':   str(row['puskesmas_id']),
                'puskesmas_name': str(row['puskesmas_name']),
                'wilayah':        str(row['wilayah']),
                'rating':         int(row['rating']),
                'chunk_index':    i,
                'n_chunks':       n,
            })
    return records


# ---------------------------------------------------------------------------
# Quick smoke-test
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    DATA = Path(__file__).resolve().parent.parent.parent / 'data' / 'reviews_cleaned_rating_1_2.csv'
    df = pd.read_csv(DATA)
    chunks = prepare_chunks(df)

    n_reviews       = len(df)
    n_chunks        = len(chunks)
    n_unsplit       = sum(1 for c in chunks if c['n_chunks'] == 1 and c['chunk_index'] == 0)
    split_review_ids = {c['review_id'] for c in chunks if c['n_chunks'] > 1}

    print(f"Reviews        : {n_reviews}")
    print(f"Total chunks   : {n_chunks}  (extra from splits: {n_chunks - n_reviews})")
    print(f"Not split      : {n_unsplit} ({n_unsplit / n_reviews * 100:.1f}%)")
    print(f"Split reviews  : {len(split_review_ids)}")

    # Show a sample of a split review so we can eyeball the chunking
    if split_review_ids:
        ex_id = next(iter(split_review_ids))
        ex_chunks = [c for c in chunks if c['review_id'] == ex_id]
        print(f"\nExample split review ({ex_id}) — {ex_chunks[0]['n_chunks']} chunks:")
        for c in ex_chunks:
            print(f"  [{c['chunk_index']}] ({len(c['chunk_text'])} chars) {c['chunk_text'][:120]}...")
