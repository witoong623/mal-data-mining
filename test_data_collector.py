import unittest
import datetime
import data_collector as dc


class link_collector_test(unittest.TestCase):
    @unittest.skip("skip parse anime page")
    def test_complete_anime_page(self):
        collector = dc.MALCollector('Tsuki ga Kirei', 'https://myanimelist.net/anime/34822', debug=True)
        collector.start_collect_data()

    @unittest.skip("skip parse anime page")
    def test_lack_data_anime_page(self):
        collector = dc.MALCollector('001', 'https://myanimelist.net/anime/29978', debug=True)
        collector.start_collect_data()

    @unittest.skip("skip parse anime page")
    def test_airing_season_score_unavailable_anime_page(self):
        collector = dc.MALCollector('Alice in Deadly School', 'https://myanimelist.net/anime/33839', debug=True)
        collector.start_collect_data()

    @unittest.skip("skip parse anime page")
    def test_airing_none_problem(self):
        collector = dc.MALCollector('0-sen Hayato Pilot', 'https://myanimelist.net/anime/33978', debug=True)
        collector.start_collect_data()

    @unittest.skip("skip parse anime page")
    def test_anime_type_problem(self):
        collector = dc.MALCollector('1989', 'https://myanimelist.net/anime/30234', debug=True)
        collector.start_collect_data()

    def test_parse_airing_year_only(self):
        start, end = dc.parse_airing('2017')
        actual_start = datetime.date(2017, 1, 1)
        self.assertEqual(start, actual_start)
        self.assertIsNone(end)

    def test_parse_airing_start_airing_only(self):
        start, end = dc.parse_airing('May 3, 2017')
        actual_start = datetime.date(2017, 5, 3)
        self.assertEqual(start, actual_start)
        self.assertIsNone(end)

    def test_parse_unknown_airing(self):
        start, end = dc.parse_airing('Not available')
        self.assertIsNone(start)
        self.assertIsNone(end)

    def test_parse_airing_unknows_finish(self):
        start, end = dc.parse_airing('Aug 25, 2017 to ?')
        actual_start = datetime.date(2017, 8, 25)
        self.assertEqual(start, actual_start)
        self.assertIsNone(end)

        start, end = dc.parse_airing('Oct, 2017 to ?')
        actual_start = datetime.date(2017, 10, 1)
        self.assertEqual(start, actual_start)
        self.assertIsNone(end)
    
    def test_parse_airing_complete(self):
        start, end = dc.parse_airing('Apr 11, 2017 to Jun 27, 2017')
        actual_start = datetime.date(2017, 4, 11)
        actual_end = datetime.date(2017, 6, 27)
        self.assertEqual(start, actual_start)
        self.assertEqual(end, actual_end)

    def test_parse_airing_not_available(self):
        start, end = dc.parse_airing('Not available')
        self.assertIsNone(start)
        self.assertIsNone(end)

    def test_parse_airing_starting_complete_finishing_year_only(self):
        start, end = dc.parse_airing('Feb 11, 2001 to 2001')
        actual_start = datetime.date(2001, 2, 11)
        actual_end = datetime.date(2001, 12, 31)
        self.assertEqual(start, actual_start)
        self.assertEqual(end, actual_end)

    def test_parse_airing_starting_year_only_finishing_unknown(self):
        start, end = dc.parse_airing('2018 to ?')
        actual_start = datetime.date(2018, 1, 1)
        self.assertEqual(start, actual_start)
        self.assertIsNone(end)

    def test_parse_airing_starting_year_only_finishing_year_only(self):
        start, end = dc.parse_airing('2006 to 2009')
        actual_start = datetime.date(2006, 1, 1)
        actual_end = datetime.date(2009, 12, 31)
        self.assertEqual(start, actual_start)
        self.assertEqual(end, actual_end)

    def test_parse_airing_dayoutofrange_problem(self):
        start, end = dc.parse_airing('Apr, 2000 to Nov, 2000')
        actual_start = datetime.date(2000, 4, 1)
        actual_end = datetime.date(2000, 11, 30)
        self.assertEqual(start, actual_start)
        self.assertEqual(end, actual_end)