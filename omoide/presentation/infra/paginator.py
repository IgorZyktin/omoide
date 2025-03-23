"""Paginator that works with page numbers."""

from collections.abc import Iterator
import math

from pydantic import BaseModel


class PageNum(BaseModel):
    """Single page representation."""

    number: int
    is_dummy: bool
    is_current: bool


class Paginator:
    """Paginator that works with page numbers."""

    def __init__(
        self,
        page: int,
        total_items: int,
        items_per_page: int,
        pages_in_block: int,
    ) -> None:
        """Initialize instance."""
        assert page >= 1
        assert items_per_page >= 1
        assert pages_in_block >= 1
        assert total_items >= 0
        self.page = page
        self.total_items = total_items
        self.items_per_page = items_per_page
        self.pages_in_block = pages_in_block

        self.total_pages = int(math.ceil(self.total_items / self.items_per_page))  # noqa: RUF046
        self.window = pages_in_block // 2

    def __repr__(self) -> str:
        """Return string representation."""
        _class = type(self).__name__
        return (
            f'{_class}('
            f'page={self.page}, '
            f'total_items={self.total_items}, '
            f'items_per_page={self.items_per_page}, '
            f'pages_in_block={self.pages_in_block}'
            ')'
        )

    def __iter__(self) -> Iterator[PageNum]:
        """Iterate over current page."""
        if self.is_fitting:
            # [1][2][3][4][5]  noqa: ERA001
            yield from self._iterate_short()
        else:
            # [1][...][55][56][57][...][70]  noqa: ERA001
            yield from self._iterate_long()

    def __len__(self) -> int:
        """Return total amount of items in the sequence."""
        return self.total_items

    @property
    def is_fitting(self) -> bool:
        """Return True if all pages can be displayed at once."""
        return self.total_pages <= self.pages_in_block

    @classmethod
    def empty(cls) -> 'Paginator':
        """Create empty paginator."""
        return cls(
            page=1,
            total_items=0,
            items_per_page=1,
            pages_in_block=1,
        )

    @property
    def has_previous(self) -> bool:
        """Return True if we can go back."""
        return self.page > self.first_page

    @property
    def has_next(self) -> bool:
        """Return True if we can go further."""
        return self.page < self.total_pages

    @property
    def previous_page(self) -> int | None:
        """Return previous page number."""
        if self.page > 1:
            return self.page - 1
        return None

    @property
    def next_page(self) -> int | None:
        """Return next page number."""
        if self.page < self.last_page:
            return self.page + 1
        return None

    @property
    def first_page(self) -> int:
        """Return first page number."""
        return 1

    @property
    def last_page(self) -> int:
        """Return last page number."""
        return max(1, self.total_pages)

    def _iterate_short(self) -> Iterator[PageNum]:
        """Iterate over all pages, no exclusions."""
        for number in range(1, self.total_pages + 1):
            yield PageNum(
                number=number,
                is_dummy=False,
                is_current=number == self.page,
            )

    def _iterate_long(self) -> Iterator[PageNum]:
        """Iterate over all pages, but show only some of them."""
        left_threshold = 1 + self.window - 1
        right_threshold = self.total_pages - self.window - 1

        if self.page < left_threshold:
            yield from self._left_leaning_design()
        elif self.page > right_threshold:
            yield from self._right_leaning_design()
        else:
            yield from self._centered_design()

    def _left_leaning_design(self) -> Iterator[PageNum]:
        """Render like [1][2][3][4][...][9]."""
        taken = 1
        for i in range(1, self.pages_in_block - taken):
            yield PageNum(
                number=i,
                is_dummy=False,
                is_current=i == self.page,
            )

        yield PageNum(
            number=-1,
            is_dummy=True,
            is_current=False,
        )

        yield PageNum(
            number=self.total_pages,
            is_dummy=False,
            is_current=self.total_pages == self.page,
        )

    def _centered_design(self) -> Iterator[PageNum]:
        """Render like [1][...][10][11][12][...][45]."""
        yield PageNum(
            number=self.first_page,
            is_dummy=False,
            is_current=self.first_page == self.page,
        )

        yield PageNum(
            number=-1,
            is_dummy=True,
            is_current=False,
        )

        left = self.page - self.window // 2
        right = self.page + self.window // 2 + 1

        for i in range(left, right + 1):
            yield PageNum(
                number=i,
                is_dummy=False,
                is_current=i == self.page,
            )

        yield PageNum(
            number=-1,
            is_dummy=True,
            is_current=False,
        )

        yield PageNum(
            number=self.total_pages,
            is_dummy=False,
            is_current=self.total_pages == self.page,
        )

    def _right_leaning_design(self) -> Iterator[PageNum]:
        """Render like [1][...][7][8][9]."""
        yield PageNum(
            number=self.first_page,
            is_dummy=False,
            is_current=self.first_page == self.page,
        )

        yield PageNum(
            number=-1,
            is_dummy=True,
            is_current=False,
        )

        taken = 3
        start = self.total_pages - self.pages_in_block + taken
        for i in range(start, self.total_pages + 1):
            yield PageNum(
                number=i,
                is_dummy=False,
                is_current=i == self.page,
            )
