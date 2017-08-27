''' This module is used to collect data from anime page. '''
import calendar
import datetime
import urllib
import re
import pymysql
import sys
import bs4
import traceback
from bs4 import BeautifulSoup

NO_CHARACTER_WARNING_TEXT = 'No characters or voice actors have been added to this title. Help improve our database by adding characters or voice actors '


def parse_float(string):
    ''' Parse string float to float type otherwise return default value.

    :param str string: text score in MAL.
    '''
    try:
        string = string.replace(',', '')
        return float(string)
    except ValueError:
        return None

def parse_int(string):
    ''' Parse string int to int type otherwise return default value.

    :param str string: text score in MAL.
    '''
    try:
        string = string.replace(',', '')
        return int(string)
    except ValueError:
        return None

def parse_airing(string):
    ''' Parse date string to datetime.date type otherwise None
        return tuple of datetime.date, first is start airing date
        and second is finish airing date.  Normally, if anime is OVA or ONA
        it doesn't have finish airing.

        :param str string: The string appears in MAL airing text.
        '''
    def get_month_number(month_str):
        if month_str == 'Jan':
            return 1
        elif month_str == 'Feb':
            return 2
        elif month_str == 'Mar':
            return 3
        elif month_str == 'Apr':
            return 4
        elif month_str == 'May':
            return 5
        elif month_str == 'Jun':
            return 6
        elif month_str == 'Jul':
            return 7
        elif month_str == 'Aug':
            return 8
        elif month_str == 'Sep':
            return 9
        elif month_str == 'Oct':
            return 10
        elif month_str == 'Nov':
            return 11
        elif month_str == 'Dec':
            return 12
        else:
            return 0

    def parse_date(start_part, start=True):
        ''' Parse what ever format of date '''
        if start_part == '?':
            return None
        split = start_part.split(' ')
        if len(split) == 3:
            return datetime.date(int(split[2]), get_month_number(split[0]), int(split[1]))
        elif len(split) == 2:
            if start:
                return datetime.date(int(split[1]), get_month_number(split[0]), 1)
            else:
                year = int(split[1])
                month = get_month_number(split[0])
                return datetime.date(year, month, calendar.monthrange(year, month)[1])
        else:
            if start:
                return datetime.date(int(start_part), 1, 1)
            else:
                return datetime.date(int(start_part), 12, 31)
    try:
        string = string.replace(',', '')
        # Separate start airing and finish airing by 'to'.
        start_finish_list = string.split('to')
        start_finish_list = [s.strip() for s in start_finish_list]

        if len(start_finish_list) == 2:
            return parse_date(start_finish_list[0], start=True), parse_date(start_finish_list[1], start=False)
        elif start_finish_list[0] == 'Not available':
            return None, None
        else:
            return parse_date(start_finish_list[0]), None
    except Exception as ex:
        raise ex


class MALCollector:
    def __init__(self, name, link, use_db=False, debug=False):
        if use_db:
            self.database = pymysql.connect(host='localhost', user='root', password='123456',
                                            db='mal_data', charset='utf8')
            self.cursor = self.database.cursor()
        self.link = link
        self.name = name
        self.use_db = use_db
        self.debug = debug
        self.insert_dict = {}

    def start_collect_data(self):
        ''' Start collect data in each MAL anime page '''

        try:
            self.collect_data()
            self.write_to_db()
        except Exception as ex:
            if self.use_db:
                write_error_sql = 'insert into anime_fetching_error(err_anime_name, err_anime_link, err_text, err_traceback) values (%s,%s,%s,%s)'
                self.cursor.execute(write_error_sql, (self.name, self.link, str(ex), traceback.format_exc()))
                self.database.commit()
            else:
                raise ex
        finally:
            if self.use_db:
                self.cursor.close()
                self.database.close()

    def create_database(self):
        database = pymysql.connect(host='localhost', user='root', password='123456',
                                   db='mal_data', charset='utf8')
        cursor = database.cursor()

        return (database, cursor)

    def collect_data(self):
        ''' Collect data of each anime page. '''
        with urllib.request.urlopen(self.link) as response:
            soup = BeautifulSoup(response.read(), 'lxml')
            self.insert_dict['ani_name'] = self.name

            # Left panel extraction
            left_panel_2 = soup.find('div', class_='js-scrollfix-bottom')

            # Type
            type_a = left_panel_2.find('span', string='Type:').parent.a
            if type_a is not None:
                self.insert_dict['ani_type'] = type_a.string.strip().lower()
            else:
                self.insert_dict['ani_type'] = left_panel_2.find('span', string='Type:').next_sibling.strip().lower()

            # Episode -- there is also unknown episode
            episode = left_panel_2.find('span', string='Episodes:').next_sibling.strip()
            if episode != 'Unknown':
                self.insert_dict['ani_episode_count'] = int(episode)

            # Status
            self.insert_dict['ani_status'] = left_panel_2.find(
                'span', string='Status:').next_sibling.strip().lower()

            # Start airing/Stop airing or sell date
            aired_text = left_panel_2.find('span', string='Aired:').next_sibling.strip()
            start, end = parse_airing(aired_text)
            if start is not None:
                self.insert_dict['ani_start_airing'] = start.isoformat()
            if end is not None:
                self.insert_dict['ani_end_airing'] = end.isoformat()

            # Season
            season_section = left_panel_2.find('span', string='Premiered:')
            season = None
            if season_section is not None:
                # Handle when season information not available but premiered string available 
                try:
                    season = season_section.parent.a.string.strip()
                except AttributeError:
                    season = None
            if season is not None:
                self.insert_dict['ani_season'] = season

            # Producers -- Check first weather have producers
            ''' producer_names = []
            producer_link = left_panel_2.find(
                'span', string='Producers:').parent.find_all('a')
            if producer_link[0].string != 'add some':
                # This mean that producer is known
                producer_names = [str(a.string) for a in producer_link]
            print('Producers', ','.join(producer_names))
            # Studios
            studio_names = []
            studio_link = left_panel_2.find(
                'span', string='Studios:').parent.find_all('a')
            if studio_link[0].string != 'add some':
                # This mean that studio is known
                studio_names = [str(a.string) for a in studio_link]
            print('Studios', ','.join(studio_names)) '''

            # Source
            self.insert_dict['ani_source'] = left_panel_2.find(
                'span', string='Source:').next_sibling.strip()

            # Genres
            genre_link = left_panel_2.find(
                'span', string='Genres:').parent.find_all('a')
            genre_names = [str(a.string).lower().replace(' ', '_') for a in genre_link]
            for genre in genre_names:
                self.insert_dict['ani_genre_' + genre] = 1

            # Duration
            self.insert_dict['ani_duration'] = left_panel_2.find(
                'span', string='Duration:').next_sibling.strip().replace(' per ep.', '')

            # Rating
            rating_text = left_panel_2.find('span', string='Rating:').next_sibling.strip()
            if rating_text != 'None':
                self.insert_dict['ani_rating'] = rating_text

            # Score
            score_span = left_panel_2.find('span', itemprop='ratingValue')
            # Check in case score isn't available
            if score_span is not None:
                self.insert_dict['ani_score'] = score_span.string.strip()

            # Member
            self.insert_dict['ani_member'] = parse_int(left_panel_2.find(
                'span', string='Members:').next_sibling.strip())

            # Favorites
            self.insert_dict['ani_favorite'] = parse_int(left_panel_2.find(
                'span', string='Favorites:').next_sibling.strip())

            # Related anime
            related_anime_table = soup.find(
                'table', class_='anime_detail_related_anime')
            if related_anime_table is not None:
                td_adaption = related_anime_table.find(
                    'td', string='Adaptation:')
                td_alternative_setting = related_anime_table.find(
                    'td', string='Alternative setting:')
                td_alternative_version = related_anime_table.find(
                    'td', string='Alternative version:')
                td_character = related_anime_table.find(
                    'td', string='Character:')
                td_other = related_anime_table.find('td', string='Other:')
                td_prequel = related_anime_table.find('td', string='Prequel:')
                td_sequel = related_anime_table.find('td', string='Sequel:')
                td_side_story = related_anime_table.find(
                    'td', string='Side story:')
                td_spin_off = related_anime_table.find(
                    'td', string='Spin-off:')
                td_summary = related_anime_table.find('td', string='Summary:')

                if td_adaption is not None:
                    self.insert_dict['ani_adaptation'] = 1
                if td_alternative_setting is not None:
                    self.insert_dict['ani_alter_setting'] = 1
                if td_alternative_version is not None:
                    self.insert_dict['ani_alter_version'] = 1
                if td_character is not None:
                    self.insert_dict['ani_character'] = 1
                if td_other is not None:
                    self.insert_dict['ani_other'] = 1
                if td_prequel is not None:
                    self.insert_dict['ani_prequel'] = 1
                if td_sequel is not None:
                    self.insert_dict['ani_sequel'] = 1
                if td_side_story is not None:
                    self.insert_dict['ani_side_story'] = 1
                if td_spin_off is None:
                    self.insert_dict['ani_spin_off'] = 1
                if td_summary is None:
                    self.insert_dict['ani_summary'] = 1

            # Character VA and staffs extraction.
            center_divs = soup.find_all('div', class_='detail-characters-list clearfix')
            char_va_list = []
            staff_list = []
            if len(center_divs) == 0:
                # No thing available
                pass
            elif len(center_divs) == 1:
                # This mean only 1 available have to check which one is available
                more_char_a = soup.find(
                    'a', style='font-weight: normal;', href=re.compile(r'\/anime\/[0-9]+'))
                # a > div > h2 -> (should be)text
                warning_char = more_char_a.parent.parent.next_sibling
                if str(warning_char) == NO_CHARACTER_WARNING_TEXT:
                    # Mean that there is no character data available
                    # Handle staff
                    people_div = center_divs[0]
                    each_people_side = people_div.find_all('div', recursive=False)
                    for side_people in each_people_side:
                        staff_list = staff_list + self.collect_key_people(side_people)
                else:
                    # Mean that there is no staff data available
                    # Handle character VA
                    char_div = center_divs[0]
                    each_char_side = char_div.find_all('div', recursive=False)
                    char_va_list = self.collect_character_va_name(each_char_side[0])

            else:
                # Both character VA and staff are available
                char_div = center_divs[0]
                each_char_side = char_div.find_all('div', recursive=False)
                char_va_list = self.collect_character_va_name(each_char_side[0])
                # Staff (only 4 persons)
                people_div = center_divs[1]
                each_people_side = people_div.find_all('div', recursive=False)
                for side_people in each_people_side:
                    staff_list = staff_list + self.collect_key_people(side_people)

            # Character voice actors
            # Get only 4 VAs.
            if len(char_va_list) > 4:
                char_va_list = char_va_list[:4]
            for index, name in enumerate(char_va_list, 1):
                self.insert_dict['ani_char_va{}'.format(index)] = name

            # Anime staff
            for index, name in enumerate(char_va_list, 1):
                self.insert_dict['ani_staff{}'.format(index)] = name
            
            if self.debug:
                for key, value in self.insert_dict.items():
                    print('{} : {}'.format(key, value))


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
            va_name = have_va.td.a.string.strip()
            va_list.append(va_name.replace(',', ''))
        return va_list

    def collect_key_people(self, div_people):
        ''' extract key people's name and return list of name '''
        people_list = []
        tables = div_people.find_all('table', recursive=False)
        for table in tables:
            people_name_td = table.tr.find_all('td', recursive=False)[1]
            name = people_name_td.a.string.strip()
            people_list.append(name.replace(',', ''))
        return people_list

    def write_test_file(self, html):
        with open('test.html', mode='w', encoding='utf8') as file:
            file.write(html)

    def write_to_db(self):
        # Create insert query
        insert_columns = ','.join(['`{}`'.format(col) for col in self.insert_dict.keys()])
        insert_val_placeholer = ','.join(['%s' for index in range(len(self.insert_dict))])
        insert_val_tuple = tuple(self.insert_dict.values())
        insert_data_sql = 'insert into anime_data({}) values ({})'.format(insert_columns, insert_val_placeholer)
        if self.use_db:
            self.cursor.execute(insert_data_sql, insert_val_tuple)
            self.database.commit()
        elif self.debug:
            print(insert_data_sql)

def main():
    database = pymysql.connect(host='localhost', user='root', password='123456',
                               db='mal_data', charset='utf8')
    cursor = database.cursor()
    sql = "select anime_name, anime_link from mal_anime_link where anime_id > 5261"
    try:
        cursor.execute(sql)
        count = 1
        while True:
            row = cursor.fetchone()
            if row is None:
                break
            collector = MALCollector(row[0], row[1], use_db=True, debug=False)
            collector.start_collect_data()
            if count % 100 == 0:
                print(count, 'passed.')
            count += 1
    finally:
        cursor.close()
        database.close()

def debug():
    collector = MALCollector('0-sen Hayato Pilot', 'https://myanimelist.net/anime/33978', use_db=False, debug=True)
    collector.start_collect_data()

if __name__ == "__main__":
    main()
