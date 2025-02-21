import os
from enum import Enum
from datetime import datetime
from random import randint
from pathlib import Path

import requests


class SORTING_TYPE(Enum):
    RELEVANCE = "relevance"
    DATE = "date_added"
    RANDOM = "random"
    VIEWS = "views"


class WPManager:
    _API_KEY = os.environ.get('API_KEY')
    _BASE_URL = "https://wallhaven.cc/"
    # _RANDOM_SEED = datetime.today().strftime("%m%d%Y")[:-2]

    def search_wallpapers(
            self,
            query: str = None,
            categories: str = "111",
            resolutions: list[str] = None,
            wallpaper_id: str = None,
            page: int = 1,
            sorting: SORTING_TYPE = SORTING_TYPE.RANDOM,
    ) -> dict:
        purity = '100'
        if wallpaper_id is not None:
            url = f"{self._BASE_URL}api/v1/w/{wallpaper_id}"
            response = requests.get(url, params={'apikey': self._API_KEY})
        else:
            url = f"{self._BASE_URL}api/v1/search"
            params = {
                "q": query,
                "categories": categories,
                "purity": purity,
                "resolutions": resolutions,
                "page": page,
                "sorting": sorting.value,
                "apikey": self._API_KEY
            }
            response = requests.get(url, params=params)

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"API request failed with status code {response.status_code}: {response.text} {response.request.url}")

    def get_random_wallpapers(self) -> dict:
        return self.search_wallpapers(sorting=SORTING_TYPE.RANDOM)

    def get_wallpaper_of_day(self) -> dict:
        response = self.search_wallpapers(query='cat', sorting=SORTING_TYPE.RELEVANCE)
        new_res = response['meta']
        new_res['data'] = [response['data'][0]]
        return new_res

    def get_list_of_wallpapers_urls_from_response(self, response: dict, light: bool = False) -> list[str]:
        wp_per_save = 10
        urls_list = []
        for wp_index, wp_data in enumerate(response['data'], start=1):
            if wp_index > wp_per_save:
                break
            if light:
                urls_list.append(wp_data['thumbs']['small'])
            else:
                urls_list.append(wp_data['path'])
        return urls_list

    def SayHello(self, username: str):
        return f"Hi from wp manager, {username}!"