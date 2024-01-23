"""Модуль классов для бота"""
from telebot.handler_backends import State, StatesGroup


class Command:
    """Класс кнопок-действий"""
    ADD_WORD = 'Добавить слово ➕'
    DELETE_WORD = 'Удалить слово🔙'
    NEXT = 'Дальше ⏭'

