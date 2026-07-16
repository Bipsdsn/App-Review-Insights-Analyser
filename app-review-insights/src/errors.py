"""Single custom exception for the pipeline (conventions.md section 2.3).

Raise with a stage-prefixed message, e.g.:
    raise PipelineError("group: LLM returned unknown theme 'Billing'")
"""


class PipelineError(Exception):
    """Raised for any recoverable-by-rerun pipeline failure."""
