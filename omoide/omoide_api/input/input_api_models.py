"""Web level API models."""
from pydantic import BaseModel

MAXIMUM_AUTOCOMPLETE_SIZE = 256
MINIMAL_AUTOCOMPLETE_SIZE = 2
AUTOCOMPLETE_VARIANTS = 10


class AutocompleteOutput(BaseModel):
    """Autocompletion variants."""
    variants: list[str]

    model_config = {
        'json_schema_extra': {
            'examples': [
                {
                    'variants': [
                        'abridge',
                        'apple',
                        'authorise',
                    ],
                }
            ]
        }
    }
