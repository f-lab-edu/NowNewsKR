from enum import Enum
import os
import re
import json
from typing import Dict, Tuple
from urllib.parse import urlparse, parse_qs

import requests
from bs4 import BeautifulSoup


class Config:
    STOCK_URL = "https://finance.naver.com/news/mainnews.nhn"
    FILE_PATH = "news_data.json"
    ENCODING = "utf-8"


class Topic(Enum):
    STOCK = "증권"

    # TODO: Add more topics
    # SPORTRS = "스포츠"
    # ENTERTAINMENT = "연예"
    # ECONOMY = "경제"
    # SOCIETY = "사회"
    # LIFE = "생활/문화"
    # WORLD = "세계"
    # IT = "IT/과학"


class StringUtils:
    @staticmethod
    def refine_raw_text(input_text: str) -> str:
        text = input_text.strip()
        text = re.sub(r"[^\w\s가-힣]", "", text)
        return text


class NaverStockNewsCrawler:
    def __init__(self, topic: Topic, url: str) -> None:
        self.url = url
        self.topic = topic.value

    def make_news_link(self, href_link: str) -> str:
        parsed_url = urlparse(href_link)
        query_params = parse_qs(parsed_url.query)
        office_id = query_params.get("office_id", [None])[0]
        article_id = query_params.get("article_id", [None])[0]

        return f"https://n.news.naver.com/mnews/article/{office_id}/{article_id}"

    def get_news_content_and_journalist(self, link: str) -> Tuple[str, str, bool]:
        try:
            response = requests.get(link)
            soup = BeautifulSoup(response.text, "html.parser")
            article = soup.find("article", {"id": "dic_area"})
            content = StringUtils.refine_raw_text(article.text)

            journalist_tag = soup.select_one(".media_end_head_journalist_name")
            journalist = (
                StringUtils.refine_raw_text(journalist_tag.text)
                if journalist_tag
                else ""
            )

            date_element = soup.find(
                "span",
                class_="media_end_head_info_datestamp_time _ARTICLE_DATE_TIME",
            )
            date_time = date_element["data-date-time"]

            return content, journalist, date_time, True
        except Exception as e:
            print(e)
            return "", "", False

    def crawl(self) -> list[Dict[str, str]]:
        response = requests.get(self.url)
        soup = BeautifulSoup(response.text, "html.parser")
        news_list = soup.select(".mainNewsList li")

        news_data = []
        for news in news_list:
            title_tag = news.select_one(".articleSubject a")
            summary_tag = news.select_one(".articleSummary")

            if title_tag and summary_tag:
                title = StringUtils.refine_raw_text(title_tag.text)
                news_url = self.make_news_link(title_tag["href"])
                (
                    content,
                    journalist,
                    date_time,
                    crawling_status,
                ) = self.get_news_content_and_journalist(news_url)

                summary = StringUtils.refine_raw_text(summary_tag.text).split("\n")[0]
                press_text = StringUtils.refine_raw_text(
                    summary_tag.select_one(".press").text
                )

                news_data.append(
                    {
                        "topic": self.topic,
                        "title": title,
                        "url": news_url,
                        "status": crawling_status,
                        "content": content,
                        "summary": summary,
                        "press": press_text,
                        "journalist": journalist,
                        "date": date_time,
                    }
                )

        return news_data


def save_news_data(file_path: str, new_data: list[Dict[str, str]]) -> str:
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
        data.extend(new_data)
    else:
        data = new_data

    with open(file_path, "w", encoding=Config.ENCODING) as file:
        json.dump(data, file, ensure_ascii=False, indent=4)
    return json.dumps(data, ensure_ascii=False, indent=4)


def main() -> None:
    # stock
    for topic in Topic:
        if topic == Topic.STOCK:
            crawler = NaverStockNewsCrawler(topic, Config.STOCK_URL)

        else:
            # Placeholder for adding more topics
            continue
        news_data = crawler.crawl()
        r = save_news_data(Config.FILE_PATH, news_data)
        print(r)


if __name__ == "__main__":
    main()
