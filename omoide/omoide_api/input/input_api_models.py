"""Web level API models."""
from pydantic import BaseModel


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
