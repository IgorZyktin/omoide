"""Models that go to user.
"""
import pydantic


class OutAutocomplete(pydantic.BaseModel):
    """Autocompletion variants."""
    variants: list[str]
