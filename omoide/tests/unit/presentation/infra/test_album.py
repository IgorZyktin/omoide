# -*- coding: utf-8 -*-
"""Tests.
"""
from omoide.presentation import infra


def _str(album: infra.Album) -> str:
    """Convert album into readable string."""
    values = []
    for page in album:
        if page.is_dummy:
            values.append('...')
        elif page.is_current:
            values.append(f'[{page.value}]')
        else:
            values.append(f'{page.value}')
    return ' '.join(values)


def test_album_str():
    album = infra.Album(
        sequence='abc',
        position='b',
        items_on_page=5,
    )

    assert str(album) == "Album(sequence='abc', position='b', items_on_page=5)"


def test_album_neighbours():
    album = infra.Album(
        sequence='abc',
        position='b',
        items_on_page=5,
    )

    assert album.position == 'b'
    assert album.previous_item == 'a'
    assert album.next_item == 'c'


def test_album_tiny():
    album = infra.Album(
        sequence='a',
        position='a',
        items_on_page=5,
    )

    assert album.position == 'a'
    assert album.first_item == 'a'
    assert album.last_item == 'a'
    assert album.previous_item is None
    assert album.next_item is None
    assert not album.has_next
    assert not album.has_previous


def test_album_not_included():
    album = infra.Album(
        sequence='abcde',
        position='z',
        items_on_page=5,
    )

    assert album.first_item == 'a'
    assert album.last_item == 'e'
    assert not album.has_previous
    assert not album.has_next
    assert _str(album) == 'a b c d e'


def test_album_short_first():
    album = infra.Album(
        sequence='abcde',
        position='a',
        items_on_page=5,
    )

    assert album.first_item == 'a'
    assert album.last_item == 'e'
    assert not album.has_previous
    assert album.has_next
    assert _str(album) == '[a] b c d e'


def test_album_short_middle():
    album = infra.Album(
        sequence='abcde',
        position='c',
        items_on_page=5,
    )

    assert album.first_item == 'a'
    assert album.last_item == 'e'
    assert album.has_previous
    assert album.has_next
    assert _str(album) == 'a b [c] d e'


def test_album_short_last():
    album = infra.Album(
        sequence='abcde',
        position='e',
        items_on_page=5,
    )

    assert album.first_item == 'a'
    assert album.last_item == 'e'
    assert album.has_previous
    assert not album.has_next
    assert _str(album) == 'a b c d [e]'


def test_album_long_first():
    album = infra.Album(
        sequence='abcdefghijklmnopqrstuvwxyz',
        position='a',
        items_on_page=10,
    )

    assert _str(album) == '[a] b c d e f g h ... z'


def test_album_long_third():
    album = infra.Album(
        sequence='abcdefghijklmnopqrstuvwxyz',
        position='c',
        items_on_page=10,
    )

    assert _str(album) == 'a b [c] d e f g h ... z'


def test_album_long_middle():
    album = infra.Album(
        sequence='abcdefghijklmnopqrstuvwxyz',
        position='n',
        items_on_page=10,
    )

    assert _str(album) == 'a ... l m [n] o p q ... z'


def test_album_long_last():
    album = infra.Album(
        sequence='abcdefghijklmnopqrstuvwxyz',
        position='z',
        items_on_page=10,
    )

    assert _str(album) == 'a ... s t u v w x y [z]'


def test_album_long_almost_last():
    album = infra.Album(
        sequence='abcdefghijklmnopqrstuvwxyz',
        position='x',
        items_on_page=10,
    )

    assert _str(album) == 'a ... s t u v w [x] y z'


def test_album_transitions():
    album = infra.Album(
        sequence='abcdefghijklmnopqrstuvwxyz',
        position='a',
        items_on_page=10,
    )

    def _ch(alb: infra.Album):
        """Stringify and increment page."""
        nonlocal album
        result = _str(alb)
        try:
            album = infra.Album(
                sequence=album.sequence,
                position=alb.sequence[alb.sequence.index(alb.position) + 1],
                items_on_page=10,
            )
        except IndexError:
            pass
        return result

    assert _ch(album) == '[a] b c d e f g h ... z'
    assert _ch(album) == 'a [b] c d e f g h ... z'
    assert _ch(album) == 'a b [c] d e f g h ... z'
    assert _ch(album) == 'a b c [d] e f g h ... z'
    assert _ch(album) == 'a b c d [e] f g h ... z'
    assert _ch(album) == 'a ... d e [f] g h i ... z'
    assert _ch(album) == 'a ... e f [g] h i j ... z'
    assert _ch(album) == 'a ... f g [h] i j k ... z'
    assert _ch(album) == 'a ... g h [i] j k l ... z'
    assert _ch(album) == 'a ... h i [j] k l m ... z'
    assert _ch(album) == 'a ... i j [k] l m n ... z'
    assert _ch(album) == 'a ... j k [l] m n o ... z'
    assert _ch(album) == 'a ... k l [m] n o p ... z'
    assert _ch(album) == 'a ... l m [n] o p q ... z'
    assert _ch(album) == 'a ... m n [o] p q r ... z'
    assert _ch(album) == 'a ... n o [p] q r s ... z'
    assert _ch(album) == 'a ... o p [q] r s t ... z'
    assert _ch(album) == 'a ... p q [r] s t u ... z'
    assert _ch(album) == 'a ... q r [s] t u v ... z'
    assert _ch(album) == 'a ... r s [t] u v w ... z'
    assert _ch(album) == 'a ... s t [u] v w x ... z'
    assert _ch(album) == 'a ... s t u [v] w x y z'
    assert _ch(album) == 'a ... s t u v [w] x y z'
    assert _ch(album) == 'a ... s t u v w [x] y z'
    assert _ch(album) == 'a ... s t u v w x [y] z'
    assert _ch(album) == 'a ... s t u v w x y [z]'
