import unittest
from unittest import TestCase
from crawler import NaverStockNewsCrawler  

class TestNaverStockNewsCrawler(TestCase):
    def setUp(self):
        self.crawler = NaverStockNewsCrawler("https://finance.naver.com/news/mainnews.nhn")

    def test_crawl(self):
        result = self.crawler.crawl()
        self.assertIsNotNone(result)  
        self.assertIsInstance(result, list)  
    
    def test_get_news_content(self):
        link = 'https://n.news.naver.com/mnews/article/001/0014424507'
        content = self.crawler.get_news_content(link)
        self.assertIsNotNone(content)
        self.assertIsInstance(content, str)
        

if __name__ == '__main__':
    unittest.main()
