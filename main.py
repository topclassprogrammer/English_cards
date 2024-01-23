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
