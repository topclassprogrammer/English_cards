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
