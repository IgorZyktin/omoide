"""Web level API models."""

from pydantic import BaseModel

from omoide.omoide_api.common import common_api_models


class AutocompleteOutput(BaseModel):
    """Autocompletion variants."""

    variants: list[str]

    model_config = {
        'json_schema_extra': {'examples': [{'variants': ['abridge', 'apple', 'authorise']}]}
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
