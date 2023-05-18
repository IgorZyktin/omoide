# -*- coding: utf-8 -*-
"""Repository that performs all search queries.
"""
import abc

import omoide.domain.models
from omoide.application import app_models
from omoide.domain import dtos
from omoide.domain import models
from omoide.domain.interfaces.in_storage import in_rp_base


class AbsSearchRepository(
    in_rp_base.AbsBaseRepository,
):
    """Repository that performs all search queries."""

    @abc.abstractmethod
    async def count_matching_items(
            self,
            user: omoide.domain.models.User,
            aim: app_models.Aim,
    ) -> int:
        """Count matching items for search query."""

    @abc.abstractmethod
    async def get_matching_items(
            self,
            user: omoide.domain.models.User,
            aim: app_models.Aim,
            obligation: dtos.Obligation,
    ) -> list[models.Item]:
        """Return matching items for search query."""

    @abc.abstractmethod
    async def guess_tag_known(
            self,
            user: omoide.domain.models.User,
            guess: dtos.GuessTag,
            obligation: dtos.Obligation,
    ) -> list[dtos.GuessResult]:
        """Guess tag for known user."""

    @abc.abstractmethod
    async def guess_tag_anon(
            self,
            user: omoide.domain.models.User,
            guess: dtos.GuessTag,
            obligation: dtos.Obligation,
    ) -> list[dtos.GuessResult]:
        """Guess tag for anon user."""

    @abc.abstractmethod
    async def count_all_tags(
            self,
            user: models.User,
    ) -> list[tuple[str, int]]:
        """Return statistics for known tags."""
