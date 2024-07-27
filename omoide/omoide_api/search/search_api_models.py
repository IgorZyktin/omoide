"""Web level API models."""
from pydantic import BaseModel

from omoide.omoide_api.common import common_api_models

LAST_SEEN_DEFAULT = -1

AUTOCOMPLETE_DEFAULT = ''
AUTOCOMPLETE_MIN_LENGTH = 2
AUTOCOMPLETE_MAX_LENGTH = 256
AUTOCOMPLETE_MIN_LIMIT = 1
AUTOCOMPLETE_MAX_LIMIT = 25
AUTOCOMPLETE_DEFAULT_LIMIT = 10

RECENT_UPDATES_MIN_LIMIT = 1
RECENT_UPDATES_MAX_LIMIT = 50
RECENT_UPDATES_DEFAULT_LIMIT = 25

SEARCH_QUERY_DEFAULT = ''
SEARCH_QUERY_MIN_LENGTH = 2
SEARCH_QUERY_MAX_LENGTH = 512
SEARCH_QUERY_MIN_LIMIT = 1
SEARCH_QUERY_MAX_LIMIT = 200
SEARCH_QUERY_DEFAULT_LIMIT = 25


class AutocompleteOutput(BaseModel):
    """Autocompletion variants."""
    variants: list[str]

    model_config = {
        'json_schema_extra': {
            'examples': [
                {'variants': ['abridge', 'apple', 'authorise']}
            ]
        }
    }


class RecentUpdatesOutput(BaseModel):
    """Recently updated items with their parent names."""
    items: list[common_api_models.ItemOutput]

    model_config = {
        'json_schema_extra': {
            'examples': [
                {'items': [common_api_models.DEFAULT_ITEM_EXAMPLE]},
            ],
        },
    }


class SearchTotalOutput(BaseModel):
    """Search statistics."""
    total: int
    duration: float

    model_config = {
        'json_schema_extra': {
            'examples': [
                {
                    'total': 1,
                    'duration': 0.025,
                }
            ],
        }
    }
