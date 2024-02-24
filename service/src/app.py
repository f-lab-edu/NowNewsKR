from flask import Flask, request
import os
import sys
import json
import uuid

from config import Config
from supabase_handler import SupabaseHandler
from es_handler import ElasticSearchHandler

current_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.join(current_dir, "..", "..")
emb_src_path = os.path.join(project_dir, "embedding", "src")
llm_src_path = os.path.join(project_dir, "llm", "src")
sys.path.append(os.path.join(project_dir, emb_src_path))
sys.path.append(os.path.join(project_dir, llm_src_path))


from embedding_model import EmbeddingModel
from llm_module import LLMModule

app = Flask(__name__)


class QueryApp:
    def __init__(self):
        self.embedding_model = EmbeddingModel()
        self.llm_model = LLMModule()
        self.supabase_handler = SupabaseHandler()
        self.es_handler = ElasticSearchHandler()

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


query_app = QueryApp()


@app.route("/query", methods=["POST"])
def query_endpoint():
    data = request.get_json()
    user_id = data.get("user_id", str(uuid.uuid4()))
    session_id = data.get("session_id", str(uuid.uuid4()))
    user_query = data.get("user_query")

    response = query_app.handle_query(user_id, session_id, user_query)

    return json.dumps(response, ensure_ascii=False)


if __name__ == "__main__":
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
