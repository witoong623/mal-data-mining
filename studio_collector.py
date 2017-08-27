import urllib
import pymysql
from bs4 import BeautifulSoup

cursor = db.cursor()
with urllib.request.urlopen('https://myanimelist.net/anime/producer') as response:
    soup = BeautifulSoup(response.read(), 'lxml')
    write_test_file(soup.prettify())
    studio_link_divs = soup.find_all('div', class_='genre-list al')
    studio_name_list = []
    for div in studio_link_divs:
        studio_name = str(div.a.string.strip())
        splited_name = studio_name.split(' ')
        studio_name = '_'.join(splited_name[:len(splited_name) - 1]).lower()
        studio_name_list.append(studio_name)
        print(studio_name)
print('There are', len(studio_name_list), 'studios')