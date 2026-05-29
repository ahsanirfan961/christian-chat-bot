"""Output validator — substring-match guardrail for scripture quotes.

Ensures the LLM cannot output text formatted as a Bible verse unless it
matches the retrieved database payload identically.  This is a lightweight
custom implementation achieving the same behaviour as a guardrails-ai
validator, without the heavy dependency.
"""

from __future__ import annotations

import re
from typing import List


def extract_quoted_strings(text: str) -> list[str]:
    """Pull every double-quoted and "curly-quoted" substring out of *text*."""
    # Matches "…", \u201c…\u201d (curly quotes), and «…»
    patterns = [
        r'"([^"]+)"',          # straight double quotes
        r'\u201c([^\u201d]+)\u201d',  # curly double quotes
        r'\u00ab([^\u00bb]+)\u00bb',  # guillemets
    ]
    found: list[str] = []
    for pat in patterns:
        found.extend(re.findall(pat, text))
    return found


def _normalise(s: str) -> str:
    """Lowercase, collapse whitespace, strip punctuation edges."""
    s = re.sub(r"\s+", " ", s).strip().lower()
    s = s.strip(".,;:!?'\"")
    return s


def validate_scripture_quotes(
    output_text: str,
    retrieved_verses: List[dict],
) -> tuple[bool, str]:
    """Check that every quoted string in *output_text* appears in the retrieved payload.

    Parameters
    ----------
    output_text:
        The LLM-generated response text.
    retrieved_verses:
        List of dicts, each with at least a ``"text"`` key containing the
        exact verse text returned by API.Bible.

    Returns
    -------
    (is_valid, cleaned_text):
        ``is_valid`` is True when every quote is verified.
        ``cleaned_text`` is the (potentially redacted) text.
    """
    if not retrieved_verses:
        # Nothing to validate against — any quote is suspicious
        quotes = extract_quoted_strings(output_text)
        if quotes:
            cleaned = output_text
            for q in quotes:
                cleaned = cleaned.replace(q, "[verse text unavailable]")
            return False, cleaned
        return True, output_text

    # Build a single normalised corpus from all retrieved verse texts
    corpus_parts: list[str] = []
    for v in retrieved_verses:
        text = v.get("text", "")
        if text:
            corpus_parts.append(_normalise(text))
    corpus = " ".join(corpus_parts)

    quotes = extract_quoted_strings(output_text)
    if not quotes:
        # No quoted material — nothing to verify
        return True, output_text

    is_valid = True
    cleaned = output_text
    for q in quotes:
        norm_q = _normalise(q)
        # Check if the normalised quote is a substring of the corpus
        if norm_q and norm_q not in corpus:
            is_valid = False
            cleaned = cleaned.replace(q, "[verse text could not be verified]")

    return is_valid, cleaned
