import json
import os
import random
import sys

from environs import Env
from sqlalchemy import create_engine, exc, func, insert
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists, create_database

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


def create_db():
    """Создаем БД"""
    try:
        DSN = f"{PROTOCOL}://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB_NAME}"
        engine = create_engine(DSN)
        if not database_exists(engine.url):
            create_database(engine.url)
        create_tables(engine)
    except (exc.OperationalError,
            exc.ArgumentError) as err:
        print('Incorrect DSN string', err)
        sys.exit()
    else:
        return engine


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
        with Session() as session:
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
            session.commit()
    except KeyError as err:
        print(f'Incorrect key {err} while trying to get it in '
              f'FOR loop')
        sys.exit()


def check_if_user_in_db(message):
    """Проверяем есть ли ID текущего пользователя в БД"""
    with Session() as session:
        if (message.from_user.id,) not in get_users_ids():
            session.add(Users(telegram_id=message.from_user.id))
            session.commit()
            return True


def get_user_id_subq(message):
    """Получаем подзапрос ID текущего пользователя"""
    with Session() as session:
        return session.query(Users).filter(
            Users.telegram_id == message.from_user.id).subquery()


def get_user_id(message):
    """Получаем ID текущего пользователя"""
    with Session() as session:
        return session.query(Users.user_id). \
            filter(Users.telegram_id == message.from_user.id).one()[0]


def get_users_ids():
    """Получаем список ID всех пользователей"""
    with Session() as session:
        return session.query(Users.telegram_id).all()


def count_common_words():
    """Получаем кол-во слов в общем словаре"""
    with Session() as session:
        return session.query(func.count(Words.word_id)).filter(
            Words.common_word).one()[0]


def count_user_words(message):
    """Получаем кол-во слов в личном словаре пользователя"""
    with Session() as session:
        return session.query(func.count(Users_words.user_id)).filter(
            Users_words.user_id == get_user_id_subq(message).c.user_id). \
            one()[0]


def get_common_eng_words():
    """Получаем список английских слов в общем словаре"""
    with Session() as session:
        common_eng_words = session.query(Words.eng_word).filter(
            Words.common_word).all()
        res = [word[0] for word in common_eng_words]
    return res


def get_user_eng_words(message):
    """Получаем список английских слов в словаре пользователя"""
    with Session() as session:
        user_eng_words = session.query(Words.eng_word).join(Users_words). \
            filter(get_user_id_subq(message).c.user_id
                   == Users_words.user_id).all()
        res = [word[0] for word in user_eng_words]
    return res


def get_eng_words(message):
    """Получаем список всех английских слов, имеющихся в общем словаре
     и словаре пользователя"""
    res = get_common_eng_words() + get_user_eng_words(message)
    random.shuffle(res)
    return res


def get_common_rus_words():
    """Получаем список русских слов в общем словаре"""
    with Session() as session:
        common_rus_words = session.query(Words.rus_word).filter(
            Words.common_word).all()
        res = [word[0] for word in common_rus_words]
    return res


def get_user_rus_words(message):
    """Получаем список русских слов в словаре пользователя"""
    with Session() as session:
        user_rus_words = session.query(Words.rus_word).join(Users_words). \
            filter(get_user_id_subq(message).c.user_id ==
                   Users_words.user_id).all()
        res = [word[0] for word in user_rus_words]
    return res


def get_rus_words(message):
    """Получаем список всех русских слов, имеющихся в общем словаре
     и словаре пользователя"""
    res = get_common_rus_words() + get_user_rus_words(message)
    random.shuffle(res)
    return res


def add_new_row_in_words(new_eng_word, new_rus_word):
    """Добавить новую запись в таблицу words"""
    with Session() as session:
        new_row_in_words = session.execute(
            insert(Words).returning(Words.word_id), [{'eng_word': new_eng_word,
                                                      'rus_word': new_rus_word,
                                                      'common_word': False}])
        session.commit()
        return new_row_in_words.fetchone()[0]


def add_new_row_in_users_words(message, new_eng_word_id):
    """Добавить новую запись в таблицу users_words"""
    with Session() as session:
        users_words_row = Users_words(user_id=get_user_id(message),
                                      word_id=new_eng_word_id)
        session.add(users_words_row)
        session.commit()


def get_target_word(translate_word):
    """Получаем слово, которое должен отгадать пользователь"""
    with Session() as session:
        return session.query(Words.eng_word). \
            filter(Words.rus_word == translate_word).one()[0]


def delete_word(message, prepared_word):
    """Удалить запись из словаря пользователя"""
    with Session() as session:
        subq = session.query(Words.word_id).join(Users_words).filter(
            Users_words.user_id == get_user_id_subq(message).c.user_id). \
            subquery()
        session.query(Words).filter(Words.word_id == subq.c.word_id,
                                    Words.eng_word == prepared_word).delete()
        session.commit()


engine = create_db()
Session = sessionmaker(bind=engine)
read_json()
make_rows()
