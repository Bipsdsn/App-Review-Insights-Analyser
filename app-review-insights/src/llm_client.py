"""Provider-agnostic LLM wrapper — all LLM calls go through complete().

No direct SDK usage in stage modules (conventions.md section 4.2).
Groq settings: 2s inter-call sleep (~30 req/min free tier), exponential
backoff 2/4/8s on 429/5xx (max 3 retries), JSON-fix reprompt (max 2).
"""

import json
import logging
import os
import time

from src.errors import PipelineError

log = logging.getLogger(__name__)

BATCH_SIZE = 25  # reviews per classification call (decisions.md D-008)
SLEEP_BETWEEN_CALLS = 2.0
BACKOFF_SCHEDULE = [2, 4, 8]

_client = None
_last_call = 0.0


def _get_client():
    global _client
    if _client is None:
        from groq import Groq

        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise PipelineError("llm: GROQ_API_KEY not set — copy .env.example to .env")
        _client = Groq(api_key=api_key)
    return _client


def _throttle() -> None:
    global _last_call
    wait = SLEEP_BETWEEN_CALLS - (time.monotonic() - _last_call)
    if wait > 0:
        time.sleep(wait)
    _last_call = time.monotonic()


def complete(
    prompt: str,
    config: dict,
    json_mode: bool = True,
    temperature: float = 0.2,
    fast: bool = False,
) -> str:
    """Send one completion request with throttling and backoff; return text.

    fast=True routes to the high-volume model (separate Groq daily quota).
    """
    client = _get_client()
    model = config["llm"]["model_fast"] if fast else config["llm"]["model"]
    kwargs = {"response_format": {"type": "json_object"}} if json_mode else {}

    last_exc: Exception | None = None
    for attempt, backoff in enumerate([0] + BACKOFF_SCHEDULE):
        if backoff:
            log.warning("llm: retrying in %ds (attempt %d)", backoff, attempt)
            time.sleep(backoff)
        _throttle()
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                **kwargs,
            )
            return resp.choices[0].message.content or ""
        except Exception as exc:  # groq exposes status via exception classes
            last_exc = exc
            status = getattr(exc, "status_code", None)
            # Daily token quota exhausted on the primary model: backoff won't
            # help (rolling 24h window) — fall back to the fast model.
            if status == 429 and not fast and "tokens per day" in str(exc).lower():
                log.warning(
                    "llm: %s daily quota exhausted — falling back to %s",
                    model,
                    config["llm"]["model_fast"],
                )
                return complete(
                    prompt,
                    config,
                    json_mode=json_mode,
                    temperature=temperature,
                    fast=True,
                )
            if status is not None and status not in (429, 500, 502, 503, 504):
                raise PipelineError(f"llm: non-retryable error: {exc}") from exc
    raise PipelineError(f"llm: exhausted retries: {last_exc}") from last_exc


def complete_json(
    prompt: str,
    config: dict,
    temperature: float = 0.2,
    fast: bool = False,
) -> dict:
    """complete() + JSON parse with a 'fix format' reprompt (max 2)."""
    text = complete(prompt, config, json_mode=True, temperature=temperature, fast=fast)
    for attempt in range(3):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            if attempt == 2:
                raise PipelineError(
                    f"llm: unparseable JSON after retries: {text[:200]}"
                )
            log.warning("llm: malformed JSON, reprompting (attempt %d)", attempt + 1)
            text = complete(
                "Return ONLY valid JSON, no prose, fixing this output:\n" + text,
                config,
                json_mode=True,
                temperature=0.0,
                fast=fast,
            )
    raise PipelineError("llm: unreachable")
