from enum import Enum
import os
import re
from typing import Dict, Tuple
from urllib.parse import urlparse, parse_qs


import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
SUPABASE_TABLE = os.environ.get("SUPABASE_TABLE")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


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

                news_item = {
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

                # Save each news to Supabase immediately after crawling
                save_news_to_supabase(news_item)


def save_news_to_supabase(news_item: Dict[str, str]) -> None:
    # 중복 체크
    existing_record = (
        supabase.table(SUPABASE_TABLE).select("*").eq("url", news_item["url"]).execute()
    )

    # 해당 URL이 이미 존재하는 경우, 업데이트하거나 무시
    if existing_record.data:
        # 업데이트 또는 기타 처리
        pass
    else:
        # 새 레코드 삽입
        supabase.table(SUPABASE_TABLE).insert(news_item).execute()


def main() -> None:
    # stock
    for topic in Topic:
        if topic == Topic.STOCK:
            crawler = NaverStockNewsCrawler(topic, Config.STOCK_URL)

        else:
            # Placeholder for adding more topics
            continue
        crawler.crawl()


if __name__ == "__main__":
    main()
