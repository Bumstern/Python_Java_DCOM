import json
import os
import pathlib
import sched
import shutil
import threading
import time
import tkinter
from tkinter.filedialog import askdirectory

import requests
import win32com.client as client

from matplotlib import pyplot as plt
from PIL import Image

# from server import WallpaperDCOMServer


def select_folder():
    """
    Prompt the user to select a folder for saving files.
    :return: The selected folder path as a string, or None if no folder was selected.
    """
    tkinter.Tk().withdraw()  # Hide the root window of Tkinter
    folder_path = askdirectory(title="Выберите папку для сохранения обоев")
    if folder_path:
        print(f"Выбранная папка: {folder_path}")
        return folder_path
    else:
        print("Папка не была выбрана. Оставляем по умолчанию")
        return None


def download_images_to_folder(links: list[str], folder_path: str):
    # if os.path.exists(folder_path):
    #     shutil.rmtree(folder_path)
    # os.makedirs(folder_path)

    # Download and save each image
    for i, link in enumerate(links, start=1):
        try:
            response = requests.get(link, stream=True)
            if response.status_code == 200:
                file_extension = os.path.splitext(link)[-1]  # Extract file extension from URL
                if file_extension.lower() not in ('.jpg', '.jpeg', '.png', '.webp'):
                    file_extension = '.jpg'  # Default to .jpg if the extension is invalid or missing

                file_path = os.path.join(folder_path, f"{i}{file_extension}")
                with open(file_path, 'wb') as file:
                    for chunk in response.iter_content(1024):
                        file.write(chunk)
                print(f"Downloaded: {file_path}")
            else:
                print(f"Failed to download {link}: HTTP {response.status_code}")
        except Exception as e:
            print(f"Error downloading {link}: {e}")


def clear_console():
    # os.system('cls' if os.name == 'nt' else 'clear')
    print('\n' * 10)


class GuestMenu:
    def __init__(self, server_obj):
        self._server = server_obj

    def register_menu(self) -> str | None:
        token = None
        while True:
            clear_console()
            print("__Главное меню__")
            print("1) Войти в систему")
            print("2) Зарегистрироваться")
            print("3) Выйти")
            choice = input("Выберите действие: ")

            match choice:
                case "1":
                    username = str(input("Введите имя пользователя: "))
                    password = str(input("Введите пароль: "))
                    token = self._server.login(username, password)
                    if token is None:
                        print("Неверное имя пользователя или пароль")
                        input("Нажмите любую клавишу, чтобы продолжить")
                case "2":
                    username = str(input("Введите имя пользователя: "))
                    password = str(input("Введите пароль: "))
                    token = self._server.register(username, password)
                    if token is None:
                        print("Такой пользователь уже существует. Поменяйте имя или войдите.")
                        input("Нажмите любую клавишу, чтобы продолжить")
                case "3":
                    clear_console()
                    print("Выход из программы...")
                    break
                case _:
                    input("Неверный выбор. Нажмите Enter, чтобы попробовать снова.")

            if token is not None:
                break
        return token


class UserMenu:
    def __init__(self, server_obj, token: str):
        self._server = server_obj
        self._token = token
        self._scheduler = sched.scheduler(time.time, time.sleep)
        self._save_folder = 'out'
        self._cache_folder = 'cache/img'

    def __download_wp(self, url: str, file_name: str, is_cache: bool = False):
        response = requests.get(url)
        if response.status_code == 200:
            file_extension = os.path.splitext(url)[-1]
            if file_extension.lower() not in ('.jpg', '.jpeg', '.png', '.webp'):
                file_extension = '.jpg'

            wp_folder = self._cache_folder if is_cache else self._save_folder

            with open(pathlib.Path(wp_folder) / (file_name + file_extension), 'wb') as f:
                f.write(response.content)
        else:
            print("Не удалось получить обои")

    def __save_wp(self, request_data: dict, index: int | None = None, is_cache: bool = False):
        if index is None:
            for i, wp_data in enumerate(request_data['data'], start=1):
                img_url = wp_data['path'] if not is_cache else wp_data['thumbs']['small']
                img_name = str(i) # wp_data['id']
                self.__download_wp(img_url, img_name, is_cache)
                if i > 10:
                    break
        else:
            wp_data = request_data['data'][index]
            img_url = wp_data['path'] if not is_cache else wp_data['thumbs']['small']
            img_name = wp_data['id']
            self.__download_wp(img_url, img_name, is_cache)

    def __display_images_in_folder_single_window(self):
        folder_path = self._cache_folder
        # Get a list of image files in the folder
        valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp')
        image_files = [f for f in os.listdir(folder_path) if f.lower().endswith(valid_extensions)]

        if not image_files:
            print("Никаких обоев не было найдено")
            return

        # Determine grid size for displaying images
        num_images = len(image_files)
        cols = min(4, num_images)  # Set the number of columns (max 4)
        rows = (num_images + cols - 1) // cols  # Calculate the required rows

        plt.figure(figsize=(15, 5 * rows))  # Adjust figure size

        # Loop through the images and add them to the plot
        for i, image_file in enumerate(image_files, 1):
            image_path = os.path.join(folder_path, image_file)
            try:
                img = Image.open(image_path)
                plt.subplot(rows, cols, i)
                plt.imshow(img)
                plt.title(image_file.split('.')[0], fontsize=10)
                plt.axis('off')
            except Exception as e:
                print(f"Could not open {image_file}: {e}")

        plt.tight_layout()
        plt.show()

    def __input_categories(self) -> str:
        general = input("Нужно ли искать General [Y/other]: ").strip() == 'Y'
        anime = input("Нужно ли искать Anime [Y/other]: ").strip() == 'Y'
        people = input("Нужно ли искать People [Y/other]: ").strip() == 'Y'
        return ''.join(['1' if elem else '0' for elem in [general, anime, people]])

    def __input_resolution(self) -> list:
        resolution = []
        need_to = input("Нужно ли определенное разрешение? [Y/other]").strip() == 'Y'
        while need_to:
            resolution.append(input("Введите разрешение: ").strip())
            need_to = input("Еще? [Y/other]").strip() == 'Y'
        return resolution

    def __input_wp_id(self) -> str | None:
        need_to = input("Есть ли определенный id [Y/other]") == 'Y'
        wp_id = None
        if need_to:
            wp_id = input("Введите определенный id").strip()
        return wp_id

    def __scheduled_wallpaper(self, delay: int, page: int):
        categories = self._server.get_user_preferences(self._token, 'categories')
        categories_str = ''.join(["1" if category in categories else "0" for category in ['General', 'Anime', 'People']])
        resolutions = self._server.get_user_preferences(self._token, 'resolutions')
        query: tuple[str] = self._server.get_user_preferences(self._token, 'tags')
        query: str = ' '.join(query)

        result = self._server.search_wallpapers(
            self._token, query, categories_str, resolutions, None, page
        )
        result: dict = json.loads(result)
        self.__save_wp(result, None, False)

        self._scheduler.enter(delay, 1, self.__scheduled_wallpaper, (delay, page + 1,))

    def _wallpaper_search_menu(self) -> None | str:
        result = None
        while True:
            clear_console()
            print("__Поиск обоев__")
            print("1) Поиск обоев")
            print("2) Случайные обои")
            print("3) Обои дня")
            print("4) Обои по рассылке")
            print("5) Вернуться")
            choice = input("Выберите действие: ")

            match choice:
                case "1":
                    try:
                        query = input("Введите поисковый запрос: ") or None
                        categories = self.__input_categories()
                        resolutions = self.__input_resolution()
                        wallpaper_id = self.__input_wp_id()
                        page = int(input("Введите номер страницы: ").strip())
                        result: str = self._server.search_wallpapers(
                            self._token, query, categories, resolutions, wallpaper_id, page
                        )
                        result: dict = json.loads(result)

                        shutil.rmtree(self._cache_folder)
                        pathlib.Path(self._cache_folder).mkdir(exist_ok=True)
                        self.__save_wp(result, None, True)
                        self.__display_images_in_folder_single_window()

                        wp_ids = input("Введите номер обоев для сохранения через пробел: ").split()

                        try:
                            wp_ids = [int(wp_id) - 1 for wp_id in wp_ids]
                            for wp_id in wp_ids:
                                assert 0 <= wp_id <= int(result['meta']['per_page'])
                        except Exception:
                            print("Произошла ошибка при выборе. Нажмите Enter, чтобы вернуться")

                        for wp_id in wp_ids:
                            self.__save_wp(result, wp_id, False)
                        break
                    except Exception:
                        print("Что-то пошло не так. Попробуйте снова")
                        input("Неверный ввод. Нажмите Enter, чтобы попробовать снова.")
                case "2":
                    result = self._server.random_wallpaper(self._token)
                    result: dict = json.loads(result)

                    shutil.rmtree(self._cache_folder)
                    pathlib.Path(self._cache_folder).mkdir(exist_ok=True)
                    self.__save_wp(result, 0, True)
                    self.__display_images_in_folder_single_window()
                    self.__save_wp(result, 0, False)
                    break
                case "3":
                    result = self._server.wallpaper_of_day(self._token)
                    result: dict = json.loads(result)

                    shutil.rmtree(self._cache_folder)
                    pathlib.Path(self._cache_folder).mkdir(exist_ok=True)
                    self.__save_wp(result, 0, True)
                    self.__display_images_in_folder_single_window()
                    self.__save_wp(result, 0, False)
                    break
                case "4":
                    try:
                        delay = int(input("Введите время рассылки новых обоев в секундах: "))
                    except Exception:
                        input("Неверный ввод. Нажмите Enter, чтобы выйти.")
                        continue

                    self._scheduler.enter(delay, 1, self.__scheduled_wallpaper, (delay, 1))
                    sched_thread = threading.Thread(target=self._scheduler.run, daemon=True)
                    sched_thread.start()
                    input("Рассылка настроена. Нажмите Enter, чтобы продолжить.")
                case "5":
                    clear_console()
                    print("Возврат...")
                    break
                case _:
                    input("Неверный выбор. Нажмите Enter, чтобы попробовать снова.")
        # print(result)
        return result

    def __choose_pref_for_remove(self):
        print("1) Категории")
        print("2) Тэг")
        print("3) Разрешение")
        choice = input("Выберите тип настройки:")
        match choice:
            case "1":
                type = 'categories'
            case "2":
                type = 'tags'
            case "3":
                type = 'resolutions'
            case _:
                input("Некорректный ввод. Нажмите Enter, чтобы выйти.")
                return None, None

        names = self._server.get_user_preferences(self._token, type)
        print('Выберите среди:', ', '.join(names))

        pref = input("Введите значение: ")
        if pref in names:
            print("Настройка введена.")
            return pref, type
        else:
            input("Некорректный ввод. Нажмите Enter, чтобы выйти.")
            return None, None

    def __choose_pref(self) -> (str | None, str | None):
        print("1) Категории")
        print("2) Тэг")
        print("3) Разрешение")
        choice = input("Выберите тип настройки:")
        match choice:
            case "1":
                type = "categories"
            case "2":
                type = "tags"
            case "3":
                type = "resolutions"
            case _:
                input("Некорректный ввод. Нажмите Enter, чтобы выйти.")
                return None, None

        names = self._server.get_all_preferences(type)
        print('Выберите среди:', ', '.join(names))

        pref = input("Введите значение: ")
        if pref in names:
            print("Настройка введена.")
            return pref, type
        else:
            input("Некорректный ввод. Нажмите Enter, чтобы выйти.")
            return None, None

    def _user_config_menu(self):
        while True:
            clear_console()
            print("__Меню пользователя__")
            print("1) Добавить предпочтение при рассылке")
            print("2) Удалить предпочтение при рассылке")
            print("3) Указать путь сохранения обоев")
            print("4) Выйти")
            choice = input("Выберите действие: ")

            match choice:
                case "1":
                    pref_value, pref_type = self.__choose_pref()
                    if pref_type is None:
                        continue
                    try:
                        self._server.add_user_config(self._token, pref_type, pref_value)
                    except Exception:
                        print("Значение уже было добавлено")
                        input("Нажмите Enter, чтобы попробовать снова.")
                case "2":
                    pref_value, pref_type = self.__choose_pref_for_remove()
                    if pref_type is None:
                        continue
                    try:
                        self._server.remove_user_config(self._token, pref_type, pref_value)
                    except Exception:
                        input("Произошла ошибка. Нажмите Enter, чтобы попробовать снова.")
                case "3":
                    print(f"Текущий путь для сохранения обоев: {self._save_folder}")
                    save_path = input("Введите путь для сохранения: ")
                    try:
                        pathlib.Path(save_path).mkdir(exist_ok=True)
                        if pathlib.Path(save_path).is_dir():
                            self._save_folder = save_path
                        else:
                            input("Некорректный путь. Нажмите Enter, чтобы вернуться.")
                    except:
                        input("Некорректный путь. Нажмите Enter, чтобы вернуться.")
                case "4":
                    clear_console()
                    print("Выход из программы...")
                    break
                case _:
                    input("Неверный выбор. Нажмите Enter, чтобы попробовать снова.")

    def user_menu(self) -> None:
        while True:
            clear_console()
            print("__Меню пользователя__")
            print("1) Найти обои")
            print("2) Настройки профиля")
            print("3) Выйти")
            choice = input("Выберите действие: ")

            match choice:
                case "0":
                    print(self._server.SayHello(self._token))
                case "1":
                    self._wallpaper_search_menu()
                case "2":
                    self._user_config_menu()
                case "3":
                    clear_console()
                    print("Выход из программы...")
                    break
                case _:
                    input("Неверный выбор. Нажмите Enter, чтобы попробовать снова.")


def main():
    server = client.Dispatch("WallpaperDCOM.Server")
    guest_menu = GuestMenu(server)

    token = guest_menu.register_menu()
    if token is None:
        exit()

    user_menu = UserMenu(server, token)
    user_menu.user_menu()


if __name__ == "__main__":
    main()
