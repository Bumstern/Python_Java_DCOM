import json
import logging
import sys
from pathlib import Path

logging.basicConfig(filename='dcom_server.log', level=logging.DEBUG)

import win32com.server.register

from managers.account_manager import AccountManager
from managers.wallpaper_manager import WPManager
from managers.db_manager import DBManager, PREFERENCE


# import pythoncom


class WallpaperDCOMServer:
    _reg_clsid_ = '{EEC8D5C1-6971-48FE-9ED0-D9FE80BC93AD}' # import pythoncom; pythoncom.CreateGuid()
    _public_methods_ = [
        'register',
        'login',
        'search_wallpapers',
        'random_wallpaper',
        'wallpaper_of_day',
        'add_user_config',
        'remove_user_config',
        'get_all_preferences',
        'get_user_preferences'
    ] 
    _reg_progid_ = 'WallpaperDCOM.Server'

    def __init__(self):
        self._account_manager = AccountManager()
        self._db_manager = DBManager()
        self._wp_manager = WPManager()

    def login(self, username, password) -> str | None:
        try:
            token = self._account_manager.login_user(username, password)
        except ValueError:
            return None
        return token

    def register(self, username, password) -> str | None:
        try:
            token = self._account_manager.register_user(username, password)
        except ValueError:
            return None
        return token

    @AccountManager.user_data_wrapper
    def search_wallpapers(
            self,
            username: str,
            query: str = None,
            categories: str = "111",
            resolutions: str = None,
            wallpaper_id: str = None,
            page: int = 1
    ) -> str:
       return json.dumps(self._wp_manager.search_wallpapers(query, categories, resolutions, wallpaper_id, page))

    @AccountManager.user_data_wrapper
    def random_wallpaper(self, username: str) -> str:
        return json.dumps(self._wp_manager.get_random_wallpapers())

    @AccountManager.user_data_wrapper
    def wallpaper_of_day(self, username: str) -> str:
        return json.dumps(self._wp_manager.get_wallpaper_of_day())

    @AccountManager.user_data_wrapper
    def add_user_config(self, username: str, pref_name: str, value: str) -> None:
        self._db_manager.add_user_preference(username, PREFERENCE(pref_name), value)

    @AccountManager.user_data_wrapper
    def remove_user_config(self, username: str, pref_name: str, value: str):
        self._db_manager.remove_user_preference(username, PREFERENCE(pref_name), value)

    def get_all_preferences(self, preference: str) -> list[str]:
        result = self._db_manager.get_all_preferences(PREFERENCE(preference))
        if result is not None:
            result = [item[0] for item in result]
        return result

    @AccountManager.user_data_wrapper
    def get_user_preferences(self, username: str, preference: str) -> list[str]:
        result = self._db_manager.get_user_preferences(username, PREFERENCE(preference))
        if result is not None:
            result = [item[0] for item in result]
        return result


if __name__ == "__main__":
    win32com.server.register.UseCommandLine(WallpaperDCOMServer)
