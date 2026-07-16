"""PII scrubbing — the non-negotiable constraint (conventions.md section 3.3)."""

import pandas as pd
import pytest

from src.pii_scrub import (REDACTED, contains_pii, hash_id, scrub_frame,
                           scrub_text)

MUST_REDACT = [
    "contact me at ramesh.k@gmail.com please",
    "mail: a+b@x.co.in",
    "call +91 98765 43210 now",
    "call 09876543210",
    "my number 9876543210",
    "9876-543210 is my number",
    "order id 12345678901 not refunded",
    "PAN ABCDE1234F rejected",
    "aadhaar 1234 5678 9012 not accepted",
    "tweet @phonepe_support did nothing",
    "see https://example.com/track?token=abc123",
]

MUST_KEEP = [
    "refund of 500 rupees pending",  # short number
    "waited 3 days for support",  # small number
    "version 2.4.1 broke everything",  # version string
    "got 50000 cashback",  # 5 digits
    "rated 5 stars last year",
    "great app no problems at all",
]


@pytest.mark.parametrize("text", MUST_REDACT)
def test_pii_is_redacted(text):
    assert REDACTED in scrub_text(text), f"not redacted: {text}"


@pytest.mark.parametrize("text", MUST_KEEP)
def test_clean_text_untouched(text):
    assert scrub_text(text) == text, f"over-redacted: {text}"


@pytest.mark.parametrize("text", MUST_REDACT)
def test_contains_pii_detects(text):
    assert contains_pii(text)


def test_scrubbed_output_is_pii_free():
    for text in MUST_REDACT:
        assert not contains_pii(scrub_text(text))


def test_hash_id_stable_and_short():
    assert hash_id("abc") == hash_id("abc")
    assert hash_id("abc") != hash_id("abd")
    assert len(hash_id("abc")) == 10


def test_scrub_frame_drops_pii_columns_and_hashes_ids():
    df = pd.DataFrame(
        {
            "platform_id": ["raw-id-1"],
            "userName": ["Ramesh Kumar"],
            "author": ["someone"],
            "text": ["email me at x@y.com"],
            "rating": [1],
        }
    )
    out = scrub_frame(df)
    assert "userName" not in out.columns
    assert "author" not in out.columns
    assert "platform_id" not in out.columns
    assert out["review_id"].iloc[0] == hash_id("raw-id-1")
    assert REDACTED in out["text"].iloc[0]
