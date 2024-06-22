# -*- coding: utf-8 -*-
"""Repository that performs write operations on items.
"""
import abc
import datetime
from typing import Collection
from uuid import UUID

from omoide import domain
from omoide.domain.interfaces.in_storage \
    .in_repositories.in_rp_items import AbsItemsRepository


class AbsItemsWriteRepository(AbsItemsRepository):
    """Repository that performs write operations on items."""
