import json
from flask import Flask 
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
import os

class NaverStockNewsCrawler:
    def __init__(self, url="https://finance.naver.com/news/mainnews.nhn"):
        self.url = url
        self.topic = '증권'

    def make_news_link(self, href_link):        
        parsed_url = urlparse(href_link)
        query_params = parse_qs(parsed_url.query)
        office_id = query_params.get('office_id', [None])[0]
        article_id = query_params.get('article_id', [None])[0]

        return f'https://n.news.naver.com/mnews/article/{office_id}/{article_id}'       
    
    def get_news_content_and_journalist(self, link):
        response = requests.get(link)
        soup = BeautifulSoup(response.text, 'html.parser')
        article = soup.find('article', {'id': 'dic_area'})
        content = article.text.strip()  

        journalist_tag = soup.select_one('.media_end_head_journalist_name')
        if journalist_tag:
            journalist = journalist_tag.text.strip()
        else:
            journalist = '기자명 없음'
        return content , journalist

    def crawl(self):
        response = requests.get(self.url)
        soup = BeautifulSoup(response.text, 'html.parser')
        news_list = soup.select('.mainNewsList li')

        news_data = []
        for news in news_list:
        
            title_tag = news.select_one('.articleSubject a')
            summary_tag = news.select_one('.articleSummary')

            if title_tag and summary_tag:
                title = title_tag.text.strip()
                link = self.make_news_link(title_tag['href'])
                content , journalist = self.get_news_content_and_journalist(link)

                summary = summary_tag.text.strip().split('\n')[0]
                press_text = summary_tag.select_one('.press').text.strip()
                date_text = summary_tag.select_one('.wdate').text.strip()

                news_data.append({'topic': self.topic, 'title': title, 'link': link, 'content': content, 'summary': summary, 'press': press_text, 'journalist': journalist, 'date': date_text })
            
        return news_data

def save_news_data(file_path, new_data):

    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        data.extend(new_data)
    else:
        data = new_data

    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)
    return json.dumps(data, ensure_ascii=False,indent=4)


app = Flask(__name__)

@app.route('/news')
def run():

    # stock
    stock_crawler = NaverStockNewsCrawler()
    stock_data = stock_crawler.crawl()
    news_data = save_news_data('news_data.json', stock_data)
    return news_data


if __name__ == '__main__':
    app.run(debug=True)
    
