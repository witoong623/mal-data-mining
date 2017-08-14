import unittest
import data_collector as dc


class link_collector_test(unittest.TestCase):
    def test_complete_anime_page(self):
        collector = dc.MALCollector(useDb=False)
        collector.collect_data('Tsuki ga Kirei', 'https://myanimelist.net/anime/34822')

    def test_lack_data_anime_page(self):
        collector = dc.MALCollector(useDb=False)
        collector.collect_data('001', 'https://myanimelist.net/anime/29978')