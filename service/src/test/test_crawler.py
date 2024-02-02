import sys
import os

# 현재 스크립트의 디렉토리를 가져와 sys.path에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, ".."))

from unittest import TestCase, main
from supabase_handler import SupabaseHandler
from crawler import NaverNewsCrawler, Topic, Config


class TestNaverNewsCrawler(TestCase):
    def setUp(self):
        self.topic = Topic.STOCK
        self.url = "https://example.com"
        self.supabase_handler = SupabaseHandler()
        self.crawler = NaverNewsCrawler(self.topic, self.url, self.supabase_handler)

    def test_make_news_link(self):
        href_link = "https://example.com/article?office_id=123&article_id=456"
        expected_link = "https://n.news.naver.com/mnews/article/123/456"
        actual_link = self.crawler.make_news_link(href_link)
        self.assertEqual(actual_link, expected_link)

    def test_crawl(self):
        # TODO: Implement test for the crawl method
        pass

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
        self.assertIsInstance(date_time, str)  # Fix: Check the type of date_time
        self.assertIsInstance(status, str)


if __name__ == "__main__":
    main()
