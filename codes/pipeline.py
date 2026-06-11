"""
Main pipeline: reviews CSV → ABSA extraction → puskesmas profiles.

Steps:
  1. preprocess  — normalize + chunk reviews
  2. classify    — LLM extraction per chunk (Step 3)
  3. aggregate   — roll up to per-puskesmas profiles (Step 6)

Usage:
  python pipeline.py
"""

from pathlib import Path
import pandas as pd

DATA    = Path(__file__).parent.parent / 'data' / 'reviews_cleaned_rating_1_2.csv'
OUTPUTS = Path(__file__).parent / 'outputs'


def run():
    from absa.preprocess import prepare_chunks
    # from absa.classifier import classify_batch   # uncomment in Step 3
    # from absa.aggregator import aggregate        # uncomment in Step 6

    print("Loading data...")
    df = pd.read_csv(DATA)
    print(f"  {len(df)} reviews, {df['puskesmas_id'].nunique()} puskesmas")

    print("Preprocessing...")
    chunks = prepare_chunks(df)
    print(f"  {len(chunks)} chunks ready")

    # Step 3: classify
    # client  = ...   # initialise Anthropic client
    # results = classify_batch(chunks, client)

    # Step 6: aggregate
    # profiles = aggregate(results)
    # import json
    # (OUTPUTS / 'puskesmas_profiles.json').write_text(json.dumps(profiles, ensure_ascii=False, indent=2))
    # print(f"  Profiles written to outputs/puskesmas_profiles.json")


if __name__ == '__main__':
    run()
