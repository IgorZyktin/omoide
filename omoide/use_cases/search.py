# -*- coding: utf-8 -*-
"""Search use cases.
"""
from omoide import domain


class AnonSearchRandomItemsUseCase:
    """Search for random images when anonymous user is asking.
    """

    async def execute(self) -> domain.SearchResult:
        """Search for random."""
        return domain.SearchResult(
            is_random=True,
            page=1,
            total_pages=1,
            total_items=1,
            items=[
                domain.SimpleItem(owner_uuid='u99', uuid='u1', name='name1',
                                  ext=None, is_collection=False),
                domain.SimpleItem(owner_uuid='u99', uuid='u2', name='name2',
                                  ext=None, is_collection=False),
                domain.SimpleItem(owner_uuid='u99', uuid='u3', name='name3',
                                  ext=None, is_collection=True),
            ],
        )


class AnonSearchSpecificItemsUseCase:
    """Search for specific images when anonymous user is asking.
    """

    async def execute(self) -> domain.SearchResult:
        """Search for specific."""
        return domain.SearchResult(
            is_random=False,
            page=1,
            total_pages=1,
            total_items=1,
            items=[
                domain.SimpleItem(owner_uuid='u99', uuid='u4', name='name4',
                                  ext=None, is_collection=False),
                domain.SimpleItem(owner_uuid='u99', uuid='u5', name='name5',
                                  ext=None, is_collection=True),
                domain.SimpleItem(owner_uuid='u99', uuid='u6', name='name6',
                                  ext=None, is_collection=False),
            ],
        )
