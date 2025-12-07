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
        'ru': 'Вложенные',
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
    'Create': {
        'ru': 'Создать',
    },
    'Upload': {
        'ru': 'Загрузить',
    },
    'Edit': {
        'ru': 'Редактировать',
    },
    'Delete': {
        'ru': 'Удалить',
    },
    'Copy ID': {
        'ru': 'Скопировать ID',
    },
    'Copy link': {
        'ru': 'Скопировать ссылку',
    },
    'Download all': {
        'ru': 'Скачать все',
    },
    'Whats new?': {
        'ru': 'Что нового?',
    },
    'Show all tags': {
        'ru': 'Просмотр тегов',
    },
    'Show used space': {
        'ru': 'Просмотр занятого места',
    },
    'Current user': {
        'ru': 'Текущий пользователь',
    },
    'Show duplicated items': {
        'ru': 'Показать дубликаты',
    },
    'Log out': {
        'ru': 'Выйти',
    },
    'Jump to bottom': {
        'ru': 'Промотать вниз',
    },
    'Jump to top': {
        'ru': 'Промотать вверх',
    },
    'Process media': {
        'ru': 'Начать обработку',
    },
    'You have successfully logged out': {
        'ru': 'Вы успешно вышли с сайта',
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
