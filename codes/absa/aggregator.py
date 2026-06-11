"""
Aggregate chunk-level findings → per-puskesmas SERVQUAL profiles.
Implemented in Step 6.
"""

from __future__ import annotations
import pandas as pd


def aggregate(results: list[dict]) -> dict[str, dict]:
    """
    Input:  list of chunk dicts with 'findings' key (from classifier.classify_batch).
    Output: dict keyed by puskesmas_id, each value is a profile dict:
        {
          "puskesmas_id":   str,
          "puskesmas_name": str,
          "wilayah":        str,
          "n_reviews":      int,
          "dimensions": {
            "<DimName>": {
              "score":        float,   # 1–5, Bayesian-smoothed polarity ratio
              "confidence":   str,     # "Cukup banyak data" / "Datanya sedang" / "Belum cukup"
              "n_mentions":   int,
              "sub_issues":   [{"label": str, "count": int, "polarity": str}],
              "quotes":       [str],
            },
            ...
          }
        }
    """
    raise NotImplementedError("Implement in Step 6")


def _polarity_to_score(n_pos: int, n_neg: int, prior_pos: float = 0.3, prior_n: int = 5) -> float:
    """
    Bayesian-smoothed polarity ratio mapped to 1–5.
    prior_pos: dataset-level positive rate for this dimension (update after first full run).
    prior_n:   strength of the prior in pseudo-counts.
    """
    smoothed = (n_pos + prior_pos * prior_n) / (n_pos + n_neg + prior_n)
    return round(1 + smoothed * 4, 2)   # maps [0, 1] → [1, 5]


def _confidence_label(n_mentions: int) -> str:
    if n_mentions >= 20:
        return "Cukup banyak data"
    if n_mentions >= 8:
        return "Datanya sedang"
    return "Belum cukup"
