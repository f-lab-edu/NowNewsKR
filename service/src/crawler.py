import json
from flask import Flask #, jsonify
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs

class NaverStockNewsCrawler:
    def __init__(self, url):
        self.url = url
    
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
                href_link = title_tag['href']

                # URL 파싱
                parsed_url = urlparse(href_link)
                query_params = parse_qs(parsed_url.query)

                # office_id와 article_id 추출
                office_id = query_params.get('office_id', [None])[0]
                article_id = query_params.get('article_id', [None])[0]
                
                print('title:',title)
                print('link:',href_link)

                link = f'https://n.news.naver.com/mnews/article/{office_id}/{article_id}'
                # https://n.news.naver.com/mnews/article/001/0014424507
                content = self.get_news_content(link)

                news_data.append({'title': title, 'link': link, 'content': content})
            
        return news_data


app = Flask(__name__)

@app.route('/news')
def run():

    crawler = NaverStockNewsCrawler("https://finance.naver.com/news/mainnews.nhn")
    news_data = crawler.crawl()
    print('news_data:',news_data)
    # return jsonify(news_data)
    # 인코딩 에러
    return json.dumps(news_data, ensure_ascii=False)


if __name__ == '__main__':
    app.run(debug=True)
    
