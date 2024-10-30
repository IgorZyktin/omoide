"""Tests."""

from omoide.presentation import infra


def _str(paginator: infra.Paginator) -> str:
    """Convert paginator into readable string."""
    numbers = []
    for page in paginator:
        if page.is_dummy:
            numbers.append('...')
        elif page.is_current:
            numbers.append(f'[{page.number:02d}]')
        else:
            numbers.append(f'{page.number:02d}')
    return ' '.join(numbers)


def test_paginator_str():
    paginator = infra.Paginator(
        page=3,
        items_per_page=5,
        total_items=25,
        pages_in_block=5,
    )

    assert str(paginator) == (
        'Paginator(page=3, total_items=25, ' 'items_per_page=5, pages_in_block=5)'
    )


def test_paginator_neighbours():
    paginator = infra.Paginator(
        page=3,
        items_per_page=5,
        total_items=25,
        pages_in_block=5,
    )

    assert paginator.page == 3
    assert paginator.previous_page == 2
    assert paginator.next_page == 4


def test_paginator_tiny():
    paginator = infra.Paginator(
        page=1,
        items_per_page=1,
        total_items=1,
        pages_in_block=1,
    )

    assert paginator.page == 1
    assert paginator.first_page == 1
    assert paginator.last_page == 1
    assert paginator.next_page is None
    assert paginator.previous_page is None
    assert not paginator.has_next
    assert not paginator.has_previous


def test_paginator_short_first():
    paginator = infra.Paginator(
        page=1,
        items_per_page=5,
        total_items=25,
        pages_in_block=5,
    )

    assert paginator.first_page == 1
    assert paginator.last_page == 5
    assert not paginator.has_previous
    assert paginator.has_next
    assert _str(paginator) == '[01] 02 03 04 05'


def test_paginator_short_middle():
    paginator = infra.Paginator(
        page=3,
        items_per_page=5,
        total_items=25,
        pages_in_block=5,
    )

    assert paginator.first_page == 1
    assert paginator.last_page == 5
    assert paginator.has_previous
    assert paginator.has_next
    assert _str(paginator) == '01 02 [03] 04 05'


def test_paginator_short_last():
    paginator = infra.Paginator(
        page=5,
        items_per_page=5,
        total_items=25,
        pages_in_block=5,
    )

    assert paginator.first_page == 1
    assert paginator.last_page == 5
    assert paginator.has_previous
    assert not paginator.has_next
    assert _str(paginator) == '01 02 03 04 [05]'


def test_paginator_long_first():
    paginator = infra.Paginator(
        page=1,
        items_per_page=5,
        total_items=100,
        pages_in_block=10,
    )

    assert paginator.first_page == 1
    assert paginator.last_page == 20
    assert _str(paginator) == '[01] 02 03 04 05 06 07 08 ... 20'


def test_paginator_long_third():
    paginator = infra.Paginator(
        page=3,
        items_per_page=5,
        total_items=100,
        pages_in_block=10,
    )

    assert paginator.first_page == 1
    assert paginator.last_page == 20
    assert _str(paginator) == '01 02 [03] 04 05 06 07 08 ... 20'


def test_paginator_long_middle():
    paginator = infra.Paginator(
        page=5,
        items_per_page=5,
        total_items=100,
        pages_in_block=10,
    )

    assert paginator.first_page == 1
    assert paginator.last_page == 20
    assert _str(paginator) == '01 ... 03 04 [05] 06 07 08 ... 20'


def test_paginator_long_last():
    paginator = infra.Paginator(
        page=20,
        items_per_page=5,
        total_items=100,
        pages_in_block=10,
    )

    assert paginator.first_page == 1
    assert paginator.last_page == 20
    assert _str(paginator) == '01 ... 13 14 15 16 17 18 19 [20]'


def test_paginator_long_almost_last():
    paginator = infra.Paginator(
        page=17,
        items_per_page=5,
        total_items=100,
        pages_in_block=10,
    )

    assert paginator.first_page == 1
    assert paginator.last_page == 20
    assert _str(paginator) == '01 ... 13 14 15 16 [17] 18 19 20'


def test_paginator_transitions():
    paginator = infra.Paginator(
        page=1,
        items_per_page=5,
        total_items=100,
        pages_in_block=10,
    )

    def _ch(pag: infra.Paginator):
        """Stringify and increment page."""
        result = _str(pag)
        pag.page += 1
        return result

    assert _ch(paginator) == '[01] 02 03 04 05 06 07 08 ... 20'
    assert _ch(paginator) == '01 [02] 03 04 05 06 07 08 ... 20'
    assert _ch(paginator) == '01 02 [03] 04 05 06 07 08 ... 20'
    assert _ch(paginator) == '01 02 03 [04] 05 06 07 08 ... 20'
    assert _ch(paginator) == '01 ... 03 04 [05] 06 07 08 ... 20'
    assert _ch(paginator) == '01 ... 04 05 [06] 07 08 09 ... 20'
    assert _ch(paginator) == '01 ... 05 06 [07] 08 09 10 ... 20'
    assert _ch(paginator) == '01 ... 06 07 [08] 09 10 11 ... 20'
    assert _ch(paginator) == '01 ... 07 08 [09] 10 11 12 ... 20'
    assert _ch(paginator) == '01 ... 08 09 [10] 11 12 13 ... 20'
    assert _ch(paginator) == '01 ... 09 10 [11] 12 13 14 ... 20'
    assert _ch(paginator) == '01 ... 10 11 [12] 13 14 15 ... 20'
    assert _ch(paginator) == '01 ... 11 12 [13] 14 15 16 ... 20'
    assert _ch(paginator) == '01 ... 12 13 [14] 15 16 17 ... 20'
    assert _ch(paginator) == '01 ... 13 14 [15] 16 17 18 19 20'
    assert _ch(paginator) == '01 ... 13 14 15 [16] 17 18 19 20'
    assert _ch(paginator) == '01 ... 13 14 15 16 [17] 18 19 20'
    assert _ch(paginator) == '01 ... 13 14 15 16 17 [18] 19 20'
    assert _ch(paginator) == '01 ... 13 14 15 16 17 18 [19] 20'
    assert _ch(paginator) == '01 ... 13 14 15 16 17 18 19 [20]'
