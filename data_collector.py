''' This module is used to collect data from anime page. '''
import urllib
import re
import pymysql
import bs4
from bs4 import BeautifulSoup

NO_CHARACTER_WARNING_TEXT = 'No characters or voice actors have been added to this title. Help improve our database by adding characters or voice actors '

class MALCollector:
    def __init__(self, useDb=False):
        if useDb:
            self.database = pymysql.connect(host='localhost', user='root', password='123456',
                                db='mal_data', charset='utf8')
            self.cursor = self.database.cursor()

    def start_collect_data(self):
        ''' Start collect data in each MAL anime page '''
        database = self.database
        cursor = self.cursor
        sql = "select * from mal_anime_link"

        try:
            cursor.execute(sql)

            while True:
                row = cursor.fetchone()
                if row is None:
                    break
        finally:
            cursor.close()
            database.close()

    def create_database(self):
        database = pymysql.connect(host='localhost', user='root', password='123456',
                            db='mal_data', charset='utf8')
        cursor = database.cursor()

        return (database, cursor)

    def collect_data(self, name, link):
        ''' Collect data of each anime page. '''
        with urllib.request.urlopen(link) as response:
            soup = BeautifulSoup(response.read(), 'lxml')
            print('Anime : ', name)

            # Left panel extraction
            left_panel = soup.find('div', class_='js-scrollfix-bottom').find_all('div', recursive=False)
            left_panel_2 = soup.find('div', class_='js-scrollfix-bottom')
            # Type
            print('Type', left_panel_2.find('span', string='Type:').parent.a.string.strip())
            # Episode -- there is also unknown episode
            print('Episode', left_panel_2.find('span', string='Episodes:').next_sibling.strip())
            # Status
            print('Status', left_panel_2.find('span', string='Status:').next_sibling.strip())
            # Start airing/Stop airing or sell date
            print('Airing', left_panel_2.find('span', string='Aired:').next_sibling.strip())
            # Season
            season_section = left_panel_2.find('span', string='Premiered:')
            season = None
            if season_section is not None:
                season = season_section.parent.a.string.strip()
            print('Season', season)
            # Producers -- Check first weather have producers
            producer_names = []
            producer_link = left_panel_2.find('span', string='Producers:').parent.find_all('a')
            if producer_link[0].string != 'add some':
                # This mean that producer is unknown
                producer_names = [str(a.string) for a in producer_link]
            print('Producers', ','.join(producer_names))
            # # Studios
            # print('Studios', ','.join([str(a.string) for a in left_panel[16].find_all('a')]))
            # # Source
            # print('Source', left_panel[17].span.next_sibling.strip())
            # # Genres
            # print('Genres', ','.join([str(a.string) for a in left_panel[18].find_all('a')]))
            # # Duration
            # print('Duration', left_panel[19].span.next_sibling.strip())
            # # Rating
            # print('Duration', left_panel[20].span.next_sibling.strip())
            # # Score
            # print('Score', left_panel[21].find_all('span')[1].string.strip())
            # # Member
            # print('Member', left_panel[24].span.next_sibling.strip())
            # # Favorites
            # print('Favorites', left_panel[25].span.next_sibling.strip())

            # Related anime
            related_anime_table = soup.find('table', class_='anime_detail_related_anime')
            if related_anime_table is not None:
                td_adaption = related_anime_table.find('td', string='Adaptation:')
                td_alternative_setting = related_anime_table.find('td', string='Alternative setting:')
                td_alternative_version = related_anime_table.find('td', string='Alternative version:')
                td_other = related_anime_table.find('td', string='Other:')
                td_prequel = related_anime_table.find('td', string='Prequel:')
                td_sequel = related_anime_table.find('td', string='Sequel:')
                td_side_story = related_anime_table.find('td', string='Side story:')
                td_spin_off = related_anime_table.find('td', string='Spin-off:')
                td_summary = related_anime_table.find('td', string='Summary:')

                have_adaption = False if td_adaption is None else True
                have_alternative_setting = False if td_alternative_setting is None else True
                have_alternative_version = False if td_alternative_version is None else True
                have_other = False if td_other is None else True
                have_prequel = False if td_prequel is None else True
                have_sequel = False if td_sequel is None else True
                have_side_story = False if td_side_story is None else True
                have_spin_off = False if td_spin_off is None else True
                have_summary = False if td_summary is None else True

            # Key character (only 4 characters)
            center_divs = soup.find_all('div', class_='detail-characters-list clearfix')
            if len(center_divs) == 0:
                # No thing available
                pass
            elif len(center_divs) == 1:
                # This mean only 1 available or nothing available
                # Have to check which one is available
                more_char_a = soup.find('a', style='font-weight: normal;', href=re.compile(r'\/anime\/[0-9]+'))
                # a > div > h2 -> (should be)text
                warning_char = more_char_a.parent.parent.next_sibling
                if str(warning_char) == NO_CHARACTER_WARNING_TEXT:
                    # Mean that there is no character data available
                    pass
                else:
                    pass
            else:
                # Both character VA and staff are available
                char_div = center_divs[0]
                each_char_side = char_div.find_all('div', recursive=False)
                char_va_list = []
                for side_char in each_char_side:
                    char_va_list = char_va_list + self.collect_character_va_name(side_char)
                    # Check if it possible to have more than 5 main character VA
                    # If not, break.
                    if len(char_va_list) < 5:
                        break

                # Key people (only 4 persons)
                people_div = center_divs[1]
                each_people_side = people_div.find_all('div', recursive=False)
                for side_people in each_people_side:
                    self.collect_key_people(side_people)

    def collect_character_va_name(self, div_va):
        ''' extract main characters VA's name and return list of name '''
        va_list = []
        tables = div_va.find_all('table', recursive=False)
        for table in tables:
            va_table = table.tr.find_all('td', recursive=False)
            # If he isn't a main character VA, don't collect
            if va_table[1].div.small.string != 'Main':
                return va_list
            # Collect main character VA name
            have_va = va_table[2].tr
            if have_va is None:
                continue
            va_name = have_va.td.a.string
            va_list.append(va_name)
            print('VA:', va_name)
        return va_list

    def collect_key_people(self, div_people):
        ''' extract key people's name and return list of name '''
        people_list = []
        tables = div_people.find_all('table', recursive=False)
        for table in tables:
            people_name_td = table.tr.find_all('td', recursive=False)[1]
            name = people_name_td.a.string
            people_list.append(name)
            print('Staff:', name)
        return people_list

    def write_test_file(self, html):
        with open('test.html', mode='w', encoding='utf8') as file:
            file.write(html)

def main():
    collector = MALCollector()
    collector.collect_data('Youkoso Jitsuryoku Shijou Shugi no Kyoushitsu e', 'https://myanimelist.net/anime/35507')

if __name__ == "__main__":
    main()