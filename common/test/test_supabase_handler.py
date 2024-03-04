import sys
import os

# 현재 스크립트의 디렉토리를 가져와 sys.path에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, ".."))

from unittest import TestCase, main
from supabase_handler import SupabaseHandler
from crawler import NewsDocuments


class TestSupabaseHandler(TestCase):
    def setUp(self):
        self.supabase_handler = SupabaseHandler()
        self.news_document = NewsDocuments(
            "url",
            "증권",
            "title",
            "crawling_status",
            "content",
            "summary",
            "press_text",
            "journalist",
            "2024-01-22 19:15:01",
            False,
        )

    def test_superbase_init(self):
        # Call the superbase_init method
        self.supabase_handler.superbase_init()

        # Assert that the supabase_url, supabase_key, and supabase_table are set correctly
        self.assertIsNotNone(
            self.supabase_handler.supabase_url, "supabase_url is not set"
        )
        self.assertIsNotNone(
            self.supabase_handler.supabase_key, "supabase_key is not set"
        )
        self.assertIsNotNone(
            self.supabase_handler.supabase_table_news, "supabase_table is not set"
        )

        self.assertIsNotNone(self.supabase_handler.client, "client is not created")

    def test_save_news_to_supabase(self):
        # Call the superbase_init method
        self.supabase_handler.superbase_init()

        # TODO: Implement test for the save_news_to_supabase method


if __name__ == "__main__":
    main()
