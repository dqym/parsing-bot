import requests
from bs4 import BeautifulSoup
import re


GENRES_URL = "https://www.kinoafisha.info/rating/movies/genres/"


class Parser:
    def __init__(self):
        self.genres = self.__init_genres()

    @staticmethod
    def __init_genres() -> dict:
        result = dict()

        data = requests.get(GENRES_URL)
        soup = BeautifulSoup(data.text, 'lxml')

        for tag in soup.find_all('a', class_="grid_cell3"):
            result[tag.string] = tag["href"]

        return result

    @staticmethod
    def __load_films(url: str, page_number: int) -> list | None:
        parameters = {"page": page_number}
        data = requests.get(url, params=parameters)
        if data.status_code in range(200, 300):
            soup = BeautifulSoup(data.text, 'lxml')
            films = soup.find_all(class_="movieItem_info")
            if not films:
                return None
            return films
        else:
            return None

    def get_genres(self) -> list:
        return list(self.genres.keys())

    def get_films(self, selected_genres: set, max_count: int = 10) -> dict:
        selected_genres = list(selected_genres)
        main_genre = selected_genres[0]
        result = dict()
        have_available_films = True

        page = 0
        films = self.__load_films(self.genres[main_genre], page)
        while films and have_available_films:
            for film in films:
                film_genres = film.find(class_="movieItem_details").find(class_="movieItem_genres").string.split(', ')
                if all(genre in film_genres for genre in selected_genres):
                    film_title = film.find(class_="movieItem_title").string
                    google_search_attributes = "?q=" + '+'.join(re.split(r'[\"«»()/:?!,.\- ]+', film_title))
                    result[film_title] = google_search_attributes
                    max_count -= 1
                    if max_count == 0:
                        have_available_films = False
                        break

            page += 1
            films = self.__load_films(self.genres[main_genre], page)

        return result

