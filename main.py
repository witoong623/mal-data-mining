import urllib
import re
import pymysql
from bs4 import BeautifulSoup

MAL_SEARCH_URL = 'https://myanimelist.net/anime.php?letter={}&show={}'
LINK_INSERT_QUERY = 'insert into mal_anime_link(anime_name, anime_link) values (%s, %s)'


def collect_anime_data(link):
    pass



