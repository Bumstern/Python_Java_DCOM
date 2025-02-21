import hashlib
from pathlib import Path
from typing import Callable
import os
import time
import sys

import jwt
from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).parents[2]/'.env')

from .db_manager import DBManager


class AccountManager:
    __SECRET_KEY = os.environ.get('SECRET_KEY')  # Секретный ключ для JWT

    def __init__(self):
        self._db_manager = DBManager()

    def _hash_password(self, password: str) -> str:
        """Хеширует пароль с использованием SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()

    def _check_password_hash(self, username: str, password: str) -> bool:
        hashed_password = self._hash_password(password)
        return self._db_manager.check_user_pass(username, hashed_password)

    @classmethod
    def _create_jwt_token(cls, username: str) -> str:
        """Создает JWT-токен для пользователя."""
        payload = {
            "sub": username,  # Идентификатор пользователя
            "iat": time.time(),  # Время выпуска токена
            "exp": time.time() + 3600,  # Срок действия токена (1 час)
        }
        return jwt.encode(payload, cls.__SECRET_KEY, algorithm="HS256")

    @classmethod
    def _decode_jwt_token(cls, token: str) -> str | None:
        """Декодирует JWT-токен и возвращает имя пользователя."""
        try:
            payload = jwt.decode(token, cls.__SECRET_KEY, algorithms=["HS256"])
            return payload["sub"]
        except jwt.ExpiredSignatureError:
            print("Ошибка: время сессии истекло. Перезайдите.")
        except jwt.InvalidTokenError:
            print("Ошибка: токен недействителен.")
        return None

    def register_user(self, username: str, password: str) -> str:
        username = username.strip()
        password = password.strip()

        # Проверка на существование пользователя
        if self._db_manager.has_user(username) or username == '':
            raise ValueError('Пользователь с таким именем уже существует!')
            # return None

        hashed_password = self._hash_password(password)
        self._db_manager.add_user(username, hashed_password)

        token = self._create_jwt_token(username)
        # print(f"Пользователь {username} успешно зарегистрирован!")
        return token

    def login_user(self, username: str, password: str) -> str | None:
        username = username.strip()
        password = password.strip()

        # Поиск пользователя в базе данных
        if not self._db_manager.has_user(username):
            print('Пользователь с таким именем не найден!')
            return None

        # Проверка пароля
        if self._check_password_hash(username, password):
            print('Авторизация успешна!')
        else:
            print('Неверный пароль!')
            return None

        # Генерация JWT-токена
        token = self._create_jwt_token(username)
        return token

    @classmethod
    def user_data_wrapper(cls, func: Callable):
        """
        Декоратор, который извлекает имя пользователя из токена
        и передает имя пользователя в целевой метод класса.
        Токен должен быть первым аргументом метода класса (не считая self).
        """

        def wrapper(*args, **kwargs):
            token = args[1]
            assert isinstance(token, str)

            # Расшифровываем токен
            username = cls._decode_jwt_token(token)
            if username is None:
                # Если не удалось расшифровать токен - выходим из функции
                return None

            # Передаем данные пользователя в целевую функцию
            if len(args) > 2:
                new_args = [args[0], username, *args[2:]]
                return func(*new_args, **kwargs)
            else:
                new_args = [args[0], username]
                return func(*new_args, **kwargs)

        return wrapper

    def SayHello(self, username: str):
        return f"Hi from account, {username}!"
