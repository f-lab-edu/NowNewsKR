from flask import Flask, request
import os
import sys
import json
import uuid
from apscheduler.schedulers.background import BackgroundScheduler

from config import Config
from supabase_handler import SupabaseHandler
from es_handler import ElasticSearchHandler
from crawler import NaverNewsCrawler, Topic
from es_indexer import ESIndexer

current_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.join(current_dir, "..", "..")
emb_src_path = os.path.join(project_dir, "embedding", "src")
llm_src_path = os.path.join(project_dir, "llm", "src")
sys.path.append(os.path.join(project_dir, emb_src_path))
sys.path.append(os.path.join(project_dir, llm_src_path))


from embedding_model import EmbeddingModel
from llm_module import LLMModule

# 싱글톤 객체 관리자를 위한 코드
_singleton_instances = {}


def get_singleton_instance(cls, *args, **kwargs):
    if cls not in _singleton_instances:
        _singleton_instances[cls] = cls(*args, **kwargs)
    return _singleton_instances[cls]


app = Flask(__name__)


class QueryApp:
    def __init__(self, embedding_model, llm_model, supabase_handler, es_handler):
        self.embedding_model = embedding_model
        self.llm_model = llm_model
        self.supabase_handler = supabase_handler
        self.es_handler = es_handler

    def handle_query(self, user_id, session_id, user_query):
        user_query_vector = self.embedding_model.get_embedding_vector(user_query)
        search_documents = self.es_handler.search_data_in_elasticsearch(
            user_query_vector, 3, 1.4
        )

        self.supabase_handler.check_or_create_user_session(user_id, session_id)
        answer = self.llm_model.ask(user_query, search_documents)

        self.supabase_handler.save_message(session_id, user_query, "user")
        self.supabase_handler.save_message(session_id, answer, "bot")

        return {
            "user_id": user_id,
            "session_id": session_id,
            "user_query": user_query,
            "answer": answer,
        }


embedding_model = get_singleton_instance(EmbeddingModel)
llm_model = get_singleton_instance(LLMModule)
supabase_handler = get_singleton_instance(SupabaseHandler)
es_handler = get_singleton_instance(ElasticSearchHandler)
es_indexer = ESIndexer(embedding_model)

query_app = QueryApp(embedding_model, llm_model, supabase_handler, es_handler)


@app.route("/query", methods=["POST"])
def query_endpoint():
    data = request.get_json()
    user_id = data.get("user_id", str(uuid.uuid4()))
    session_id = data.get("session_id", str(uuid.uuid4()))
    user_query = data.get("user_query")

    response = query_app.handle_query(user_id, session_id, user_query)

    return json.dumps(response, ensure_ascii=False)


def crawl_news():
    # 모든 주제에 대해 크롤링을 수행합니다.
    for topic in Topic:
        crawler = NaverNewsCrawler(
            topic=topic,
            url=Config.STOCK_URL,
            supabase_handler=supabase_handler,
        )
        crawler.crawl()


def index_news():
    news_db = supabase_handler.get_news_data_from_supabase()
    news_documents = supabase_handler.data_to_news_documents(news_db)

    for news_doc in news_documents:
        index_result = es_indexer.index_data_to_elasticsearch(news_doc)
        if index_result:
            news_doc.is_indexed = True
            supabase_handler.update_news_db_index_status(news_doc)


def schedule_tasks():
    # 크롤랑,인덱싱 백그라운드로 주기적으로 실행합니다.
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        crawl_news, "interval", hours=1
    )  # Customize the interval as needed
    scheduler.add_job(
        index_news, "interval", hours=1
    )  # Customize the interval as needed
    scheduler.start()


if __name__ == "__main__":
    schedule_tasks()  # 크롤러 스케줄링 시작
    app.run(debug=True, port=8080)


# 명령어 예시
"""
curl -X POST http://localhost:8080/query \
-H "Content-Type: application/json" \
-d '{
  "user_id": "uni2237",
  "session_id": "000",
  "user_query": "미래에셋맵스 92호 펀드와 부동산 매각 관련 뉴스 있어?"
}'

curl -X POST http://localhost:8080/query \
-H "Content-Type: application/json" \
-d '{
  "user_id": "uni2237",
  "user_query": "미래에셋맵스 92호 펀드와 부동산 매각 관련 뉴스 있어?"
}'
"""
