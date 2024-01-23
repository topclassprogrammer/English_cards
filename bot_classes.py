"""Модуль классов для бота"""
from telebot.handler_backends import State, StatesGroup


class Command:
    """Класс кнопок-действий"""
    ADD_WORD = 'Добавить слово ➕'
    DELETE_WORD = 'Удалить слово🔙'
    NEXT = 'Дальше ⏭'


class BotStates(StatesGroup):
    """Класс состояний бота"""
    target_word = State()
    translate = State()
    check_eng_word_to_add = State()
    check_rus_word_to_add = State()
    input_rus_word_to_add = State()
    check_eng_word_to_delete = State()
    new_row = State()
