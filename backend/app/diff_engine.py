"""
Compares a submitted document's text against the stored original, sentence
by sentence, and reports exactly what changed.

Uses difflib (Python standard library) — no ML needed for this, since we're
not detecting similarity to unknown sources (like the plagiarism project),
we're comparing against ONE known, specific original. A deterministic diff
is more precise and more defensible than a similarity score here.
"""

import re
import difflib


def split_sentences(text: str):
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in sentences if s.strip()]


def compare_documents(original_text: str, submitted_text: str):
    """
    Returns:
        match_percentage: float 0-100
        differences: list of dicts describing each change
        verdict: "MATCH" or "DISCREPANCY_FOUND"
    """
    original_sentences = split_sentences(original_text)
    submitted_sentences = split_sentences(submitted_text)

    matcher = difflib.SequenceMatcher(None, original_sentences, submitted_sentences)
    differences = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue  # unchanged content, nothing to flag

        original_chunk = " ".join(original_sentences[i1:i2])
        submitted_chunk = " ".join(submitted_sentences[j1:j2])

        if tag == "replace":
            differences.append({
                "type": "MODIFIED",
                "original": original_chunk,
                "submitted": submitted_chunk,
            })
        elif tag == "delete":
            differences.append({
                "type": "REMOVED_FROM_ORIGINAL",
                "original": original_chunk,
                "submitted": "",
            })
        elif tag == "insert":
            differences.append({
                "type": "ADDED_IN_SUBMITTED",
                "original": "",
                "submitted": submitted_chunk,
            })

    match_percentage = round(matcher.ratio() * 100, 1)
    verdict = "MATCH" if match_percentage >= 98.0 and not differences else "DISCREPANCY_FOUND"

    return match_percentage, differences, verdict
