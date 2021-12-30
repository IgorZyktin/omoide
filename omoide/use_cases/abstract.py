# -*- coding: utf-8 -*-
"""All possible use cases in one place.
"""


# user-related use cases ------------------------------------------------------

class AbsUpdateUserUseCase:
    """Change user data (language, visibility, etc.).
    """


# group-related use cases -----------------------------------------------------


class AbsCreateGroupUseCase:
    """Create new group.
    """


class AbsUpdateGroupUseCase:
    """Change group data (name, members, etc.).
    """


class AbsDeleteGroupUseCase:
    """Delete existing group.
    """


# visibility-related use cases ------------------------------------------------


class AbsCreateVisibilityUseCase:
    """Create new visibility template.
    """


class AbsUpdateVisibilityUseCase:
    """Change visibility template data (which items are visible).
    """


class AbsDeleteVisibilityUseCase:
    """Delete existing visibility template.
    """


# item-related use cases ------------------------------------------------------


class AbsCreateItemUseCase:
    """Create new item.
    """


class AbsUpdateItemUseCase:
    """Change item data (name, tags, permissions, etc.).
    """


class AbsDeleteItemUseCase:
    """Delete existing item.
    """


class AbsUploadItemUseCase:
    """Upload content specifically for this item.
    """


class AbsUploadChildItemsUseCase:
    """Create many new items and make them children of the current one.
    """


# search-related use cases ----------------------------------------------------


class AbsSearchRandomItemsUseCase:
    """Search for random images when registered user is asking.
    """


class AbsSearchSpecificItemsUseCase:
    """Search for specific images when registered user is asking.
    """


class AbsAnonSearchRandomItemsUseCase:
    """Search for random images when anonymous user is asking.
    """


class AbsAnonSearchSpecificItemsUseCase:
    """Search for specific images when anonymous user is asking.
    """
