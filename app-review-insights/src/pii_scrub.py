"""Stage 1.5: Deterministic PII removal at the ingestion boundary.

Nothing downstream of this module may contain usernames, emails, phone
numbers, or platform IDs. All patterns live in PATTERNS — add new ones
here only (conventions.md section 3.3).

Order matters: email runs before @handle so "a@b.com" is not half-matched;
currency/amount protection is handled by requiring 8+ bare digits for the
ID rule (EC-PII-04/05).
"""

import hashlib
import logging
import re

import pandas as pd

log = logging.getLogger(__name__)

REDACTED = "[REDACTED]"

# Columns that must never survive ingestion (EC-PII-12: only mapped columns
# are imported, but manual CSVs may carry these — drop defensively).
PII_COLUMNS = frozenset(
    {
        "username",
        "user_name",
        "author",
        "name",
        "email",
        "user",
        "reviewer",
        "userimage",
        "user_image",
        "replycontent",
        "reply_content",
    }
)

# Ordered: earlier patterns run first.
PATTERNS: list[tuple[str, re.Pattern]] = [
    # Emails, incl. subaddressing and multi-part TLDs (EC-PII-01)
    ("email", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")),
    # URLs with query strings / tokens — whole URL goes (EC-PII-07)
    ("token_url", re.compile(r"https?://\S+\?\S+")),
    # Indian phone numbers: optional +91/0 prefix, 10 digits starting 6-9,
    # single space/hyphen separators allowed anywhere (EC-PII-02)
    (
        "phone_in",
        re.compile(r"(?<![\d-])(?:\+91[\s-]?|0)?[6-9](?:[\s-]?\d){9}(?![\d-])"),
    ),
    # PAN card pattern: ABCDE1234F (EC-PII-11)
    ("pan", re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b")),
    # Aadhaar-like: 4-4-4 digit groups (EC-PII-11)
    ("aadhaar", re.compile(r"\b\d{4}\s\d{4}\s\d{4}\b")),
    # Long bare digit runs (8+): order/ticket/account numbers (EC-PII-04).
    # Negative lookbehind for currency/comma keeps amounts intact (EC-PII-05).
    ("long_id", re.compile(r"(?<![\d,.\u20b9])\d{8,}(?![\d,.])")),
    # @handles — after email so only standalone handles remain (EC-PII-06)
    ("handle", re.compile(r"(?<!\w)@\w{2,}")),
]


def scrub_text(s: str) -> str:
    """Redact all PII patterns in a single string."""
    if not isinstance(s, str) or not s:
        return "" if not isinstance(s, str) else s
    for _name, pattern in PATTERNS:
        s = pattern.sub(REDACTED, s)
    return s


def hash_id(platform_id: str) -> str:
    """Non-reversible stable key: sha256, first 10 hex chars (D-013)."""
    return hashlib.sha256(str(platform_id).encode("utf-8")).hexdigest()[:10]


def scrub_frame(df: pd.DataFrame, id_column: str = "platform_id") -> pd.DataFrame:
    """Scrub a review dataframe in place of the PII boundary.

    - Drops any known PII columns (username/author/email/...)
    - Hashes `id_column` into `review_id` and removes the raw value
    - Redacts PII patterns inside `title` and `text`
    """
    df = df.copy()

    drop_cols = [c for c in df.columns if c.lower().replace(" ", "") in PII_COLUMNS]
    if drop_cols:
        df = df.drop(columns=drop_cols)
        log.info("pii: dropped columns %s", drop_cols)

    if id_column in df.columns:
        df["review_id"] = df[id_column].map(hash_id)
        df = df.drop(columns=[id_column])

    for col in ("title", "text"):
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str).map(scrub_text)

    return df


def contains_pii(s: str) -> bool:
    """Re-scan helper for downstream artifacts (defense in depth)."""
    return any(p.search(s) for _n, p in PATTERNS)
