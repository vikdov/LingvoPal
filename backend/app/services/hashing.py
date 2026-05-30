"""Content fingerprinting for item deduplication."""

import hashlib
import re
import unicodedata


def _normalize(s: str) -> str:
    s = unicodedata.normalize("NFKC", s)  # ﬁ→fi, full-width chars→ASCII, etc.
    s = s.casefold()  # Unicode-aware lowercasing (ß→ss)
    s = re.sub(r"\s+", " ", s).strip()  # collapse whitespace
    return s


def compute_item_content_hash(
    language_id: int,
    term: str,
    context: str | None,
) -> str:
    """SHA-256 hex fingerprint of (language_id, term, context).

    Covers the homograph problem: "bank" (financial) and "bank" (river) differ
    in context → different hashes → separate items.

    MVP trade-off: casefold() means "Apple" and "apple" are identical. Known
    failure mode: acronyms without context ("IT" pronoun vs "IT" tech) in the
    same language will falsely deduplicate. Revisit if users report issues.
    """
    payload = f"{language_id}|{_normalize(term)}|{_normalize(context or '')}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
