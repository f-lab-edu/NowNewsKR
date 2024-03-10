from flask import Flask, request
import os
import sys
import json
import uuid
import yaml

# from apscheduler.schedulers.background import BackgroundScheduler

from es_handler import ElasticSearchHandler

current_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.join(current_dir, "..", "..")

common_src_path = os.path.join(project_dir, "common", "src")
sys.path.append(os.path.join(project_dir, common_src_path))

emb_src_path = os.path.join(project_dir, "embedding", "src")
sys.path.append(os.path.join(project_dir, emb_src_path))

llm_src_path = os.path.join(project_dir, "llm", "src")
sys.path.append(os.path.join(project_dir, llm_src_path))

crawler_src_path = os.path.join(project_dir, "crawler", "src")
sys.path.append(os.path.join(project_dir, crawler_src_path))


from config import Config
from supabase_handler import SupabaseHandler

from embedding_model import EmbeddingModel

from llm_module import LLMModule

app = Flask(__name__)


class QueryApp:
    def __init__(
        self,
        embedding_model,
        llm_model,
        supabase_handler,
        es_handler,
        yaml_path=Config.YAML_PATH,
    ):

        self.embedding_model = embedding_model
        self.llm_model = llm_model
        self.supabase_handler = supabase_handler
        self.es_handler = es_handler
        self.config = self.load_configuration_from_yaml(yaml_path)

    @staticmethod
    def load_configuration_from_yaml(yaml_path):
        with open(yaml_path, "r") as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
        return config

    def handle_query(self, user_id, session_id, user_query):
        user_query_vector = self.embedding_model.get_embedding_vector(user_query)
        search_documents, original_db_ids, es_document_ids = (
            self.es_handler.search_data_in_elasticsearch(
                user_query_vector, self.config["top_k"], self.config["threshold"]
            )
        )
        self.supabase_handler.check_or_create_user_session(user_id, session_id)

        last_interactions = self.supabase_handler.get_last_user_interactions(session_id)

        answer = self.llm_model.ask(user_query, search_documents, last_interactions)

        self.supabase_handler.save_message(
            session_id, user_query, "user", original_db_ids, es_document_ids
        )
        self.supabase_handler.save_message(
            session_id, answer, "bot", original_db_ids, es_document_ids
        )

        return {
            "user_id": user_id,
            "session_id": session_id,
            "user_query": user_query,
            "answer": answer,
            "original_db_ids": original_db_ids,
            "es_document_ids": es_document_ids,
        }


@app.route("/query", methods=["POST"])
def query_endpoint():
    data = request.get_json()
    user_id = data.get("user_id", str(uuid.uuid4()))
    session_id = data.get("session_id", str(uuid.uuid4()))
    user_query = data.get("user_query")

    response = query_app.handle_query(user_id, session_id, user_query)

    return json.dumps(response, ensure_ascii=False)


def create_app():
    embedding_model = EmbeddingModel()
    llm_model = LLMModule()
    supabase_handler = SupabaseHandler()
    es_handler = ElasticSearchHandler()

    query_app = QueryApp(embedding_model, llm_model, supabase_handler, es_handler)
    return query_app


query_app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)


# 명령어 예시
"""
curl -X POST http://localhost:8080/query \
-H "Content-Type: application/json" \
-d '{
  "user_id": "uni2237",
  "session_id": "000",
  "user_query": "파두 공동 대표 관련 뉴스 있어?"
}'

curl -X POST http://localhost:8080/query \
-H "Content-Type: application/json" \
-d '{
  "user_id": "uni2237",
  "user_query": "파두 공동 대표 관련 뉴스 있어?"                      
}'
"""
