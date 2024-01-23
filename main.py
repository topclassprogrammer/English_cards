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
