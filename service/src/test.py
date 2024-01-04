import unittest
from unittest import TestCase , main
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
        content,journalist = self.crawler.get_news_content_and_journalist(link)
        self.assertIsNotNone(content)
        self.assertIsInstance(content, str)

        self.assertIsNotNone(journalist)
        self.assertIsInstance(journalist, str)
        

if __name__ == '__main__':
    main()
