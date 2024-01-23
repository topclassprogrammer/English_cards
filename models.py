"""Модуль ORM-моделей для бота"""
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Users(Base):
    """Таблица ID пользователей"""
    __tablename__ = 'users'
    user_id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    words = relationship('Users_words', back_populates='users')


class Words(Base):
    """Таблица английских слов, их переводов на русский язык и
    наличия флага принадлежности к общему словарю пользователей"""
    __tablename__ = 'words'
    word_id = Column(Integer, primary_key=True)
    eng_word = Column(String(40), nullable=False)
    rus_word = Column(String(40), nullable=False)
    common_word = Column(Boolean, nullable=False)
    users = relationship('Users_words', back_populates='words')


