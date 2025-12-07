"""Poor-man's localization module."""

from omoide import models

VOCABULARY = {
    'Home': {
        'ru': 'Домой',
    },
    'Search': {
        'ru': 'Искать',
    },
    'Random': {
        'ru': 'Случайные',
    },
    'Ordered': {
        'ru': 'По порядку',
    },
    'Collections': {
        'ru': 'Коллекции',
    },
    'All items': {
        'ru': 'Картинки',
    },
    'Direct': {
        'ru': 'Ближайшие',
    },
    'Related': {
        'ru': 'Дочерние',
    },
    'Paged load': {
        'ru': 'Постранично',
    },
    'Dynamic load': {
        'ru': 'Лента',
    },
    'Login': {
        'ru': 'Вход',
    },
}


def gettext(text: str, user: models.User) -> str:
    """Convert to different language."""
    if user.is_anon:
        return text

    # TODO - use proper localization technics, not this garbage
    try:
        return VOCABULARY[text]['ru']
    except (KeyError, ValueError, IndexError):
        return text
