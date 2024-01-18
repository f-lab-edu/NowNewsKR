import sys
import os

import re
import logging
from enum import Enum
from typing import Dict, Tuple
from urllib.parse import urlparse, parse_qs


import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from supabase import create_client, Client
from supabase_handler import SupabaseHandler


class Config:
    STOCK_URL = "https://finance.naver.com/news/mainnews.nhn"
    FILE_PATH = "news_data.json"
    ENCODING = "utf-8"


class Topic(Enum):
    STOCK = "증권"

    # TODO : Add more topics
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


class NewsDocuments:
    def __init__(
        self, topic, title, url, status, content, summary, press, journalist, date
    ):
        self.topic = topic
        self.title = title
        self.url = url
        self.status = status
        self.content = content
        self.summary = summary
        self.press = press
        self.journalist = journalist
        self.date = date

    def __repr__(self):
        return f"NewsDocuments({self.topic}, {self.title}, {self.url}, {self.status}, {self.content}, {self.summary}, {self.press}, {self.journalist}, {self.date})"

    def to_superbase_format(self):
        return {
            "topic": self.topic,
            "title": self.title,
            "url": self.url,
            "status": self.status,
            "content": self.content,
            "summary": self.summary,
            "press": self.press,
            "journalist": self.journalist,
            "date": self.date,
        }

    def to_db(self):
        return self.to_superbase_format()


class NaverNewsCrawler:
    def __init__(
        self, topic: Topic, url: str, supabase_handler: SupabaseHandler
    ) -> None:
        self.url = url
        self.topic = topic.value
        self.supabase_handler = supabase_handler  # SupabaseHandler 인스턴스를 저장

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
        except requests.RequestException as e:
            logging.error("Request failed: %s", e)
            return "", "", False
        except Exception as e:
            logging.error("Failed to parse HTML: %s", e)
            return "", "", False

    def crawl(self) -> None:
        response = requests.get(self.url)
        soup = BeautifulSoup(response.text, "html.parser")
        news_list = soup.select(".mainNewsList li")

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

                news_item = NewsDocuments(
                    self.topic,
                    title,
                    news_url,
                    crawling_status,
                    content,
                    summary,
                    press_text,
                    journalist,
                    date_time,
                )

                self.supabase_handler.save_news_to_supabase(news_item)


def main() -> None:
    try:
        # stock
        for topic in Topic:
            if topic == Topic.STOCK:
                supabase_handler = SupabaseHandler()
                supabase_handler.superbase_init()
                crawler = NaverNewsCrawler(topic, Config.STOCK_URL, supabase_handler)

            else:
                # TODO : adding more topics
                continue
            crawler.crawl()
    except Exception as e:
        logging.error("An error occurred in main func: %s", e)


if __name__ == "__main__":
    main()
