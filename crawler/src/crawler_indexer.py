import os
import sys
import time
from apscheduler.schedulers.background import BackgroundScheduler

from crawler import NaverNewsCrawler, Topic
from es_indexer import ESIndexer

current_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.join(current_dir, "..", "..")

common_src_path = os.path.join(project_dir, "common", "src")
sys.path.append(os.path.join(project_dir, common_src_path))

from config import Config, Topic, NewsDocuments
from supabase_handler import SupabaseHandler


def crawl_and_index_news():
    # 모든 주제에 대해 크롤링을 수행합니다.
    supabase_handler = SupabaseHandler()
    es_indexer = ESIndexer()

    for topic in Topic:
        crawler = NaverNewsCrawler(
            topic=topic,
            url=Config.STOCK_URL,
            supabase_handler=supabase_handler,
        )
        crawler.crawl()
        indexing_news(supabase_handler, es_indexer)


def indexing_news(supabase_handler, es_indexer):
    news_db = supabase_handler.get_news_data_from_supabase()
    news_documents = supabase_handler.data_to_news_documents(news_db)

    for news_doc in news_documents:
        index_result = es_indexer.index_data_to_elasticsearch(news_doc)
        if index_result:
            news_doc.is_indexed = True
            supabase_handler.update_news_db_index_status(news_doc)


if __name__ == "__main__":
    scheduler = BackgroundScheduler()
    scheduler.add_job(crawl_and_index_news, "interval", hours=1)
    scheduler.start()

    try:
        # 메인 스레드가 바로 종료되지 않도록 무한 루프를 사용
        while True:
            time.sleep(10)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
