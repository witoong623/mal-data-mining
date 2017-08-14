import urllib
import re
import pymysql
from bs4 import BeautifulSoup

MAL_SEARCH_URL = 'https://myanimelist.net/anime.php?letter={}&show={}'
LINK_INSERT_QUERY = 'insert into mal_anime_link(anime_name, anime_link) values (%s, %s)'

def walk_anime_url(first_char, cursor):
    ''' Walk MAL search page and collect all anime link. '''
    print('Start collecting anime begin with {}'.format(first_char))
    for page in range(0, 10000, 50):
        try:
            with urllib.request.urlopen(MAL_SEARCH_URL.format(first_char, page)) as response:
                soup = BeautifulSoup(response.read(), 'lxml')
                anime_table = soup.find_all('table')[2]
                for tr in anime_table.contents:
                    if tr.name is None:
                        continue
                    link = tr.find('a', class_='hoverinfo_trigger fw-b fl-l')
                    if link is None:
                        continue
                    substr = re.search(
                        r'https:\/\/myanimelist.net\/anime\/[0-9]+',
                        link['href'])
                    cursor.execute(
                        LINK_INSERT_QUERY, (substr.group(0), link.string))
        except urllib.error.HTTPError as httpe:
            if httpe.code == 404:
                print('break at page {}'.format(page))
                break
            elif httpe.code >= 500:
                pass
        except pymysql.DatabaseError as db_err:
            print('Error {} at anime {}'.format(db_err, link.string))
        except IndexError:
            ''' Sometime MAL return blank result instead of 404 error
            must manually check it'''
            with open('blank_table_page.txt', mode='a') as file:
                file.writelines('Current page that out of range {}'.format(
                    MAL_SEARCH_URL.format(first_char, page)))


def prepare_collect_mal_link():
    dbs = create_database()
    database = dbs[0]
    cursor = dbs[1]

    first_chars = ['.', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L',
                   'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
    for char in first_chars:
        walk_anime_url(char, cursor)
        database.commit()
    cursor.close()
    database.close()
    print('Finished.')

def create_database():
    database = pymysql.connect(host='localhost', user='root', password='123456',
                         db='mal_data', charset='utf8')
    cursor = database.cursor()

    return (database, cursor)