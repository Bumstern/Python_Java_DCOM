import os
import sys
from enum import Enum
import logging

import psycopg2 as pg
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).parents[2]/'.env')
logger = logging.getLogger('main')


class PREFERENCE(Enum):
    TAGS = 'tags'
    CATEGORIES = 'categories'
    RESOLUTIONS = 'resolutions'


class DBManager:
    _SOURCE_DB = os.environ.get('DB_SOURCE')
    _DB_USER = os.environ.get('DB_USER')
    _DB_PASS = os.environ.get('DB_PASS')

    def __init__(self):
        # logger.debug(f'source: {self._SOURCE_DB}, user: {self._DB_USER}, pass: {self._DB_PASS}')
        self._conn = pg.connect(database=self._SOURCE_DB, user=self._DB_USER, password=self._DB_PASS)
        self.__create_tables()

    def __del__(self):
        if self._conn is not None:
            self._conn.close()

    def __create_tables(self):
        with open(Path(__file__).absolute().parent.parent/'sql/create_tables.sql', 'r') as f:
            sql_script = f.read()

        # sql_script = CREATE_TABLES_SCRIPT
        cursor = self._conn.cursor()
        cursor.execute(sql_script)
        self._conn.commit()
        cursor.close()

    def has_user(self, username: str) -> bool:
        cursor = self._conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        user = cursor.fetchone()
        res = user is not None
        cursor.close()
        return res

    def check_user_pass(self, username: str, password: str):
        cursor = self._conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = %s and password = %s',
                       (username, password,))
        user = cursor.fetchone()
        res = user is not None
        cursor.close()
        return res

    def add_user(self, username: str, password: str):
        cursor = self._conn.cursor()
        cursor.execute('INSERT INTO users (username, password) VALUES (%s, %s)',
                       (username, password,))
        self._conn.commit()
        cursor.close()

    def get_all_preferences(self, preference: PREFERENCE) -> tuple | None:
        cursor = self._conn.cursor()
        match preference:
            case PREFERENCE.TAGS:
                cursor.execute('SELECT name FROM tags')
            case PREFERENCE.RESOLUTIONS:
                cursor.execute('SELECT name FROM resolutions')
            case PREFERENCE.CATEGORIES:
                cursor.execute('SELECT name FROM categories')
            case _:
                raise ValueError(f"Нет такого PREFERENCE: {preference}")
        res = cursor.fetchall()
        cursor.close()
        return res

    def add_user_preference(self, username: str, preference: PREFERENCE, value: str) -> None:
        cursor = self._conn.cursor()
        match preference:
            case PREFERENCE.CATEGORIES:
                cursor.execute(
                    "INSERT INTO user_categories (user_login, category_id) VALUES (%s, (SELECT id FROM categories WHERE name = %s)) ON CONFLICT DO NOTHING",
                    (username, value,)
                )
            case PREFERENCE.TAGS:
                cursor.execute(
                    "INSERT INTO user_tags (user_login, tag_id) VALUES (%s, (SELECT id FROM tags WHERE name = %s)) ON CONFLICT DO NOTHING",
                    (username, value,)
                )
            case PREFERENCE.RESOLUTIONS:
                cursor.execute(
                    "INSERT INTO user_resolutions (user_login, resolution_id) VALUES (%s, (SELECT id FROM resolutions WHERE name = %s)) ON CONFLICT DO NOTHING",
                    (username, value,)
                )
            case _:
                raise ValueError(f"Нет такого PREFERENCE: {preference}")
        self._conn.commit()
        cursor.close()

    def remove_user_preference(self, username: str, preference: PREFERENCE, value: str) -> None:
        cursor = self._conn.cursor()
        match preference:
            case PREFERENCE.CATEGORIES:
                cursor.execute(
                    "DELETE FROM user_categories WHERE user_categories.category_id = "
                    "(select c.id from user_categories uc "
                    "join categories c on uc.category_id = c.id "
                    "where uc.user_login = %s and c.name = %s);",
                    (username, value,)
                )
            case PREFERENCE.TAGS:
                cursor.execute(
                    "DELETE FROM user_tags WHERE user_tags.tag_id = "
                    "(select t.id from user_tags ut "
                    "join tags t on ut.tag_id = t.id "
                    "where ut.user_login = %s and t.name = %s);",
                    (username, value,)
                )
            case PREFERENCE.RESOLUTIONS:
                cursor.execute(
                    "DELETE FROM user_resolutions WHERE user_resolutions.resolution_id = "
                    "(select r.id from user_resolutions ur "
                    "join resolutions r on ur.resolution_id = r.id "
                    "where ur.user_login = %s and r.name = %s);",
                    (username, value,)
                )
            case _:
                raise ValueError(f"Нет такого PREFERENCE: {preference}")
        self._conn.commit()
        cursor.close()

    def get_user_preferences(self, username: str, preference: PREFERENCE) -> tuple | None:
        cursor = self._conn.cursor()
        match preference:
            case PREFERENCE.TAGS:
                cursor.execute("select t.name from tags as t "
                               "join user_tags as ut on ut.tag_id = t.id "
                               "join users as u on u.username = ut.user_login "
                               "where u.username = %s;", (username,))
            case PREFERENCE.RESOLUTIONS:
                cursor.execute("select r.name from resolutions as r "
                               "join user_resolutions as ur on ur.resolution_id = r.id "
                               "join users as u on u.username = ur.user_login "
                               "where u.username = %s;", (username,))
            case PREFERENCE.CATEGORIES:
                cursor.execute("select c.name from categories as c "
                               "join user_categories as uc on uc.category_id = c.id "
                               "join users as u on u.username = uc.user_login "
                               "where u.username = %s;", (username,))
            case _:
                raise ValueError(f"Нет такого PREFERENCE: {preference}")
        res = cursor.fetchall()
        cursor.close()
        return res

    def SayHello(self, username: str):
        return f"Hi from db manager, {username}!"