"""Web level API models."""
from pydantic import BaseModel

from omoide.omoide_api.common import common_api_models

MAXIMUM_AUTOCOMPLETE_SIZE = 256
MINIMAL_AUTOCOMPLETE_SIZE = 2
AUTOCOMPLETE_VARIANTS = 10

ITEMS_IN_RESPONSE = 25
ITEMS_IN_RECENT_UPDATES_RESPONSE = ITEMS_IN_RESPONSE


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


class RecentUpdatesOutput(BaseModel):
    """Recently updated items with their parent names."""
    items: list[common_api_models.ItemOutput]

    model_config = {
        'json_schema_extra': {
            'examples': [
                {
                    'items': [
                        common_api_models.DEFAULT_ITEM_EXAMPLE,
                    ],

                },
            ],
        },
    }
