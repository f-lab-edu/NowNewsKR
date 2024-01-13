from datetime import datetime
from unittest import TestCase, main

from crawler import NaverStockNewsCrawler, Topic, Config


class TestNaverStockNewsCrawler(TestCase):
    def setUp(self):
        self.crawler = NaverStockNewsCrawler(Topic.STOCK, Config.STOCK_URL)

    def test_crawl(self):
        self.crawler.crawl()

        # TODO: Add test case here

    def test_get_news_content(self):
        link = "https://n.news.naver.com/mnews/article/001/0014424507"
        (
            content,
            journalist,
            date_time,
            status,
        ) = self.crawler.get_news_content_and_journalist(link)

        # 결과가 None이 아닌지 확인
        self.assertIsNotNone(content)
        self.assertIsNotNone(journalist)
        self.assertIsNotNone(date_time)
        self.assertIsNotNone(status)

        # 결과의 타입 확인
        self.assertIsInstance(content, str)
        self.assertIsInstance(journalist, str)
        self.assertIsInstance(date_time, datetime)  # Fix: Check the type of date_time
        self.assertIsInstance(status, bool)


if __name__ == "__main__":
    main()
