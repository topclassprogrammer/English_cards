"""Основной модуль логики работы боты"""
import json
import os
import random
from string import ascii_letters, whitespace
import sys

from environs import Env
from sqlalchemy import create_engine, func, insert, exc
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists, create_database
from telebot import TeleBot, types, custom_filters
from telebot.storage import StateMemoryStorage
from telebot.apihelper import ApiTelegramException

from bot_classes import Command, BotStates
from models import Words, Users, Users_words, create_tables


DB_DATA = 'db_data.json'

env = Env()
env.read_env()
PROTOCOL = env('PROTOCOL')
USER = env('USER')
PASSWORD = env.int('PASSWORD')
HOST = env('HOST')
PORT = env.int('PORT')
DB_NAME = env('DB_NAME')
TOKEN = env('TOKEN')

ENG_WORD_CHARS = ascii_letters + whitespace + '-'
RUS_LOWER_CHARS = 'йцукенгшщзхъфывапролджэячсмитьбю'
RUS_WORD_CHARS = RUS_LOWER_CHARS + RUS_LOWER_CHARS.upper() + whitespace + '-'


def create_db():
    """Создаем БД"""
    try:
        DSN = f"{PROTOCOL}://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB_NAME}"
        engine = create_engine(DSN)
        if not database_exists(engine.url):
            create_database(engine.url)
        Session = sessionmaker(bind=engine)
        global session
        session = Session()
        create_tables(engine)
    except (exc.OperationalError,
            exc.ArgumentError) as err:
        print('Incorrect DSN string', err)
        sys.exit()


def read_json():
    """Считываем JSON файл"""
    if DB_DATA not in os.listdir():
        print(f'DB data file name {DB_DATA} '
              f'not found in the project folder {os.getcwd()}')
        sys.exit()
    with open(DB_DATA, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except json.decoder.JSONDecodeError as err:
            print(f'Incorrect JSON data in {DB_DATA}', err)
            sys.exit()
    return data


def make_rows():
    """Заполняем БД записями из JSON-файла"""
    try:
        for el in read_json():
            if 'Words' == el['model']:
                session.add(Words(eng_word=el['fields']['eng_word'],
                                  rus_word=el['fields']['rus_word'],
                                  common_word=el['fields']['common_word']))
            elif 'Users' == el['model']:
                session.add(Users(telegram_id=el['fields']['telegram_id']))
            elif 'Users_words' == el['model']:
                session.add(Users_words(user_id=el['fields']['user_id'],
                                        word_id=el['fields']['word_id']))
    except KeyError as err:
        print(f'Incorrect key {err} while trying to get it in '
              f'FOR loop')
        sys.exit()
    session.commit()


# Создаем объект класса TeleBot
try:
    TOKEN = env('TOKEN')
except ApiTelegramException as err:
    print(f'Invalid token {TOKEN}', err)
    sys.exit()
else:
    state_storage = StateMemoryStorage()
    bot = TeleBot(TOKEN, state_storage=state_storage)


def get_user_id(message):
    """Получаем ID пользователя"""
    return session.query(Users).filter(
        Users.telegram_id == message.from_user.id).subquery()


def count_common_words():
    """Получаем кол-во слов в общем словаре"""
    return session.query(func.count(Words.word_id)).filter(
        Words.common_word == True).one()[0]


def count_user_words(message):
    """Получаем кол-во слов в личном словаре пользователя"""
    return session.query(func.count(Users_words.user_id)).filter(
        Users_words.user_id == get_user_id(message).c.user_id).one()[0]


def get_common_eng_words():
    """Получаем список английских слов в общем словаре"""
    res = []
    common_eng_words = session.query(Words.eng_word).filter(
        Words.common_word == True).all()
    [res.append(word[0]) for word in common_eng_words]
    return res


def get_user_eng_words(message):
    """Получаем список английских слов в словаре пользователя"""
    res = []
    user_eng_words = session.query(Words.eng_word).join(Users_words).filter(
        get_user_id(message).c.user_id == Users_words.user_id).all()
    [res.append(word[0]) for word in user_eng_words]
    return res


def get_eng_words(message):
    """Получаем список всех английских слов, имеющихся в общем словаре
     и словаре пользователя"""
    res = []
    res += get_common_eng_words() + get_user_eng_words(message)
    random.shuffle(res)
    return res


def get_common_rus_words():
    """Получаем список русских слов в общем словаре"""
    res = []
    common_rus_words = session.query(Words.rus_word).filter(
        Words.common_word == True).all()
    [res.append(word[0]) for word in common_rus_words]
    return res


def get_user_rus_words(message):
    """Получаем список русских слов в словаре пользователя"""
    res = []
    user_rus_words = session.query(Words.rus_word).join(Users_words).filter(
        get_user_id(message).c.user_id == Users_words.user_id).all()
    [res.append(word[0]) for word in user_rus_words]
    return res


def get_rus_words(message):
    """Получаем список всех русских слов, имеющихся в общем словаре
     и словаре пользователя"""
    res = []
    res += get_common_rus_words() + get_user_rus_words(message)
    random.shuffle(res)
    return res


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
    users = session.query(Users.telegram_id).all()
    if (message.from_user.id,) not in users:
        session.add(Users(telegram_id=message.from_user.id))
        session.commit()
        msg = "Hello, stranger, let's study English..."
        bot.send_message(message.chat.id, msg)


@bot.message_handler(commands=['cards'])
def create_cards(message):
    """Создает карточку из семи кнопок: 4 кнопки это
    возможные варианты ответов, а 3 - это кнопки-действия"""
    translate_word = get_rus_words(message)[0]
    target_word = session.query(Words.eng_word).filter(
        Words.rus_word == translate_word).one()[0]
    random_eng_words = []
    for word in get_eng_words(message):
        if len(random_eng_words) < 3 and word != target_word:
            random_eng_words.append(word)
    buttons_text = []
    buttons_text += [target_word] + random_eng_words
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
    user_id = session.query(Users.user_id).filter(
        Users.telegram_id == message.from_user.id).one()[0]
    words_row = session.execute(insert(Words).returning(Words.word_id),
                                [{'eng_word': new_eng_word,
                                  'rus_word': new_rus_word,
                                  'common_word': False}])
    new_eng_word_id = words_row.fetchone()[0]
    users_words_row = Users_words(user_id=user_id, word_id=new_eng_word_id)
    session.add(users_words_row)
    session.commit()
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
