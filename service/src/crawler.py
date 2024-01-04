import json
from flask import Flask 
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs

class NaverStockNewsCrawler:
    def __init__(self, url):
        self.url = url

    def make_news_link(self, href_link):        
        parsed_url = urlparse(href_link)
        query_params = parse_qs(parsed_url.query)
        office_id = query_params.get('office_id', [None])[0]
        article_id = query_params.get('article_id', [None])[0]

        return f'https://n.news.naver.com/mnews/article/{office_id}/{article_id}'       
    
    def get_news_content(self, link):
        response = requests.get(link)
        soup = BeautifulSoup(response.text, 'html.parser')
        article = soup.find('article', {'id': 'dic_area'})
        content = article.text.strip()  
        return content      

    def crawl(self):
        response = requests.get(self.url)
        soup = BeautifulSoup(response.text, 'html.parser')
        news_list = soup.select('.mainNewsList li')

        news_data = []
        for news in news_list:
            title_tag = news.select_one('.articleSubject a')

            if title_tag:
                title = title_tag.text.strip()
                link = self.make_news_link(title_tag['href'])
                content = self.get_news_content(link)
                news_data.append({'title': title, 'link': link, 'content': content})
            
        return news_data


app = Flask(__name__)

@app.route('/news')
def run():

    crawler = NaverStockNewsCrawler("https://finance.naver.com/news/mainnews.nhn")
    news_data = crawler.crawl()
    return json.dumps(news_data, ensure_ascii=False)


if __name__ == '__main__':
    app.run(debug=True)
    
