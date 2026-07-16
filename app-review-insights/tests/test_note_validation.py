"""Note validation gates — word counter, quote checker, theme ranking."""

import pandas as pd

from src.generate_note import (_normalize_for_match, build_quote_pool,
                               count_words, extract_quotes, top_themes,
                               verify_quotes)


def test_word_count_strips_markdown_tokens():
    assert count_words("# Title\n**bold** and _italic_ words") == 5


def test_word_count_limit_detection():
    long_note = "word " * 251
    assert count_words(long_note) > 250
    short_note = "word " * 250
    assert count_words(short_note) == 250


def test_extract_quotes_ignores_short_fragments():
    note = 'He said "ok" but also "this app never works for me at all"'
    assert extract_quotes(note) == ["this app never works for me at all"]


def test_verify_quotes_accepts_real_and_rejects_paraphrase():
    source = pd.Series(["The KYC process failed three times this week for me"])
    good = 'note: "KYC process failed three times this week" end'
    bad = 'note: "the KYC flow broke thrice in seven days" end'
    assert verify_quotes(good, source) == []
    assert len(verify_quotes(bad, source)) == 1


def test_verify_quotes_survives_smart_quotes_and_whitespace():
    source = pd.Series(["it's   simply the best payment app I have used"])
    note = "x \u201cit\u2019s simply the best payment app I have used\u201d y"
    assert verify_quotes(note, source) == []


def test_normalize_for_match():
    assert _normalize_for_match("A  B\u2019s   c") == "a b's c"


def test_top_themes_skips_sentiment_bucket_and_tiebreaks():
    stats = {
        "totals": {
            "General Praise & Sentiment": 1000,
            "Payments": 50,
            "KYC": 50,
            "Performance": 80,
            "Statements": 10,
        },
        "avg_rating": {
            "General Praise & Sentiment": 4.5,
            "Payments": 2.0,
            "KYC": 3.0,
            "Performance": 2.5,
            "Statements": 1.0,
        },
    }
    top = top_themes(stats)
    assert "General Praise & Sentiment" not in top
    assert top[0] == "Performance"
    assert top[1:] == ["Payments", "KYC"]  # tie on 50 -> lower rating first


def test_quote_pool_filters_length_and_redactions():
    df = pd.DataFrame(
        {
            "theme": ["Payments"] * 4,
            "rating": [1, 5, 1, 1],
            "text": [
                "short",
                "a reasonable length review complaining about payment failures",
                "contains [REDACTED] so must be excluded from the quote pool",
                "x" * 500,
            ],
        }
    )
    pool = build_quote_pool(df, ["Payments"])
    texts = [q["text"] for q in pool]
    assert len(pool) == 1
    assert "payment failures" in texts[0]
