"""Основной модуль логики работы боты"""
import random
from string import ascii_letters, whitespace
import sys

from telebot import TeleBot, types, custom_filters
from telebot.storage import StateMemoryStorage
from telebot.apihelper import ApiTelegramException

from bot_classes import Command, BotStates
from db import env, get_rus_words, get_eng_words, count_user_words, \
    get_common_eng_words, get_user_eng_words, get_target_word, \
    add_new_row_in_words, add_new_row_in_users_words, delete_word, \
    check_if_user_in_db


TOKEN = env('TOKEN')
ENG_WORD_CHARS = ascii_letters + whitespace + '-'
RUS_LOWER_CHARS = 'йцукенгшщзхъфывапролджэячсмитьбю'
RUS_WORD_CHARS = RUS_LOWER_CHARS + RUS_LOWER_CHARS.upper() + whitespace + '-'


# Создаем объект класса TeleBot
try:
    TOKEN = env('TOKEN')
except ApiTelegramException as err:
    print(f'Invalid token {TOKEN}', err)
    sys.exit()
else:
    state_storage = StateMemoryStorage()
    bot = TeleBot(TOKEN, state_storage=state_storage)


@bot.message_handler(commands=['start'])
def start(message):
    """Вывод приветственного сообщения по команде /start"""
    msg = (
        "Привет 👋 Давай попрактикуемся в английском языке.\n"
        "Тренировки можешь проходить в удобном для себя темпе. "
        "У тебя есть возможность использовать тренажёр, как конструктор, "
        "и собирать свою собственную базу для обучения.\n"
        "Чтобы начать тренировку воспользуйтесь командой /cards")
    bot.send_message(message.chat.id, msg)
    if check_if_user_in_db(message):
        msg = "Hello, stranger, let's study English..."
    else:
        msg = "Welcome back!"
    bot.send_message(message.chat.id, msg)


@bot.message_handler(commands=['cards'])
def create_cards(message):
    """Создает карточку из семи кнопок: 4 кнопки это
    возможные варианты ответов, а 3 - это кнопки-действия"""
    translate_word = get_rus_words(message)[0]
    target_word = get_target_word(translate_word)
    random_eng_words = []
    for word in get_eng_words(message):
        if len(random_eng_words) < 3 and word != target_word:
            random_eng_words.append(word)
    buttons_text = [target_word] + random_eng_words
    random.shuffle(buttons_text)
    buttons_text += [Command.NEXT, Command.ADD_WORD, Command.DELETE_WORD]
    global buttons
    buttons = [types.KeyboardButton(text=button) for button in buttons_text]
    cards = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    cards.add(*buttons)
    msg = f"Как переводится слово '{translate_word}'?"
    bot.send_message(message.chat.id, msg, reply_markup=cards)
    bot.set_state(message.from_user.id, BotStates.target_word, message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['target_word'] = target_word
        data['translate_word'] = translate_word


@bot.message_handler(func=lambda message: message.text == Command.NEXT)
def next_cards(message):
    """Создает новую карточку слов"""
    create_cards(message)


@bot.message_handler(func=lambda message: message.text == Command.ADD_WORD)
def input_eng_word_to_add(message):
    """Ввод нового английского слова для добавления в словарь пользователя"""
    msg = "Введите новое английское слово"
    bot.send_message(message.chat.id, msg)
    bot.set_state(message.from_user.id, BotStates.check_eng_word_to_add,
                  message.chat.id)


@bot.message_handler(state=BotStates.check_eng_word_to_add)
def check_eng_word_to_add(message):
    """Проверка перед добавлением нового английского слова на
    корректность символов и присутствие в словаре пользователя"""
    prepared_word = message.text.lower().capitalize().strip()
    if not set(message.text) < set(ascii_letters + whitespace + '-'):
        msg = ("Вы некорректно ввели английское слово. В слове должны "
               "присутствовать только буквы английского алфавита.\n"
               "Попробуйте еще раз.")
        bot.send_message(message.chat.id, msg)
        return
    elif prepared_word in get_eng_words(message):
        msg = ("Данное слово '{prepared_word}' уже есть в словаре.\n"
               "Вы должны ввести слово, которого нет в словаре.")
        bot.send_message(message.chat.id, msg)
        return
    bot.set_state(message.from_user.id, BotStates.input_rus_word_to_add,
                  message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['new_eng_word'] = prepared_word
    input_rus_word_to_add(message)


@bot.message_handler(state=BotStates.input_rus_word_to_add)
def input_rus_word_to_add(message):
    """Ввод русского перевода для введенного английского слова для добавления
    в словарь пользователя"""
    msg = "Введите русский перевод для введенного английского слова"
    bot.send_message(message.chat.id, msg)
    bot.set_state(message.from_user.id, BotStates.check_rus_word_to_add,
                  message.chat.id)


@bot.message_handler(state=BotStates.check_rus_word_to_add)
def check_rus_word_to_add(message):
    """Проверка перед добавлением русского перевода на
    корректность символов и присутствие в словаре пользователя"""
    prepared_word = message.text.lower().capitalize().strip()
    if not set(message.text) < set(RUS_WORD_CHARS):
        msg = ("Вы некорректно ввели русское слово. В слове должны "
               "присутствовать только буквы русского алфавита.\n"
               "Попробуйте еще раз.")
        bot.send_message(message.chat.id, msg)
        return
    elif prepared_word in get_eng_words(message):
        msg = (f"Данное слово '{prepared_word}' уже есть в словаре.\n"
               "Вы должны ввести слово, которого нет в словаре.")
        bot.send_message(message.chat.id, msg)
        return
    bot.set_state(message.from_user.id, BotStates.new_row, message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['new_rus_word'] = prepared_word
    add_new_row(message)


@bot.message_handler(state=BotStates.new_row)
def add_new_row(message):
    """Запись пары слов в БД"""
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        new_eng_word = data['new_eng_word']
        new_rus_word = data['new_rus_word']
    new_eng_word_id = add_new_row_in_words(new_eng_word, new_rus_word)
    add_new_row_in_users_words(message, new_eng_word_id)
    msg = ("Слова успешно добавлены!\nКол-во слов в вашем личном словаре: "
           f"{count_user_words(message)}")
    bot.send_message(message.chat.id, msg)
    bot.delete_state(message.from_user.id, message.chat.id)


@bot.message_handler(func=lambda message: message.text == Command.DELETE_WORD)
def input_eng_word_to_delete(message):
    """Ввод английского слова для удаления из словаря пользователя"""
    msg = ("Введите английское слово, которое вы хотите "
           "удалить из своего словаря")
    bot.send_message(message.chat.id, msg)
    bot.set_state(message.from_user.id, BotStates.check_eng_word_to_delete,
                  message.chat.id)


@bot.message_handler(state=BotStates.check_eng_word_to_delete)
def check_eng_word_to_delete(message):
    """Проверка перед удалением английского слова на
    корректность символов и присутствие в словаре пользователя"""
    prepared_word = message.text.lower().capitalize().strip()
    if not set(message.text) < set(ENG_WORD_CHARS):
        msg = ("Вы некорректно ввели английское слово. В слове должны "
               "присутствовать только буквы английского алфавита.\n"
               "Попробуйте еще раз.")
        bot.send_message(message.chat.id, msg)
    elif prepared_word in get_common_eng_words():
        msg = ("Вы не можете удалить английское слово из общего словаря\n"
               "Вы должны ввести английское слово из своего словаря.\n"
               "Попробуйте еще раз.")
        bot.send_message(message.chat.id, msg)
    elif prepared_word in get_user_eng_words(message):
        delete_word(message, prepared_word)
        msg = (f"Запись со словом {prepared_word} успешно удалена из "
               "словаря пользователя")
        bot.send_message(message.chat.id, msg)
        bot.delete_state(message.from_user.id, message.chat.id)
    else:
        msg = (f"Слово {prepared_word} не обнаружено в словаре.\n"
               "Попробуйте еще раз.")
        bot.send_message(message.chat.id, msg)
    return


@bot.message_handler(state=BotStates.target_word)
def check_target_word(message):
    """Проверка корректно выбранного слова из карточки"""
    prepared_word = message.text.lower().capitalize().strip()
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        target_word = data['target_word']
        translate_word = data['translate_word']
    cards = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    if prepared_word == target_word or '✅' in prepared_word:
        for button in buttons[:4]:
            if button.text == prepared_word and '✅' not in button.text:
                button.text = prepared_word + '✅'
                cards.add(*buttons)
                break
        msg = (f"Поздравляем!🎉 Это правильный ответ✅\n{target_word} => "
               f"{translate_word}\nЧтобы продолжить нажмите {Command.NEXT}")
        bot.send_message(message.chat.id, msg, reply_markup=cards)
    else:
        for button in buttons[:4]:
            if button.text == prepared_word and '❌' not in button.text and \
                    '✅' not in button.text:
                button.text = prepared_word + '❌'
                cards.add(*buttons)
                break
        msg = "Неправильный ответ❌ Попробуйте еще раз."
        bot.send_message(message.chat.id, msg, reply_markup=cards)


if __name__ == '__main__':
    bot.add_custom_filter(custom_filters.StateFilter(bot))
    bot.infinity_polling()
