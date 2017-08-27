import urllib
import pymysql
from bs4 import BeautifulSoup

GENRE_INSERT_QUERY = 'insert into genres(gn_name) values (%s)'

db = pymysql.connect(host='localhost', user='root', password='123456',
                     db='mal_data', charset='utf8')
cursor = db.cursor()

with urllib.request.urlopen('https://myanimelist.net/anime.php') as response:
    soup = BeautifulSoup(response.read(), 'lxml')
    genre_section = soup.find_all('div', class_='genre-link')[0]
    genre_divs = genre_section.find_all('div', class_='genre-list al')
    for div in genre_divs:
        studio_name = str(div.a.string.strip())
        splited_name = studio_name.split(' ')
        studio_name = '_'.join(splited_name[:len(splited_name) - 1]).lower()
        cursor.execute(GENRE_INSERT_QUERY, (studio_name,))
        print('Wrote', studio_name, 'to database.')
db.commit()
cursor.close()
db.close()