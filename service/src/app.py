from flask import Flask, request, jsonify
import requests
import os
import sys
import json

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

# 모듈 인스턴스 생성 예시
embedding_model = EmbeddingModel()
llm_model = LLMModule()
supabase_handler = SupabaseHandler()
es_handler = ElasticSearchHandler()


@app.route("/query", methods=["POST"])
def handle_query():
    data = request.get_json()
    user_id = data.get("user_id")
    session_id = data.get("session_id")
    user_query = data.get("user_query")

    user_query_vector = embedding_model.get_embedding_vector(user_query)
    search_results = es_handler.search_data_in_elasticsearch(user_query_vector, 3, 1.4)

    combined_text = "\n".join(
        [hit["_source"]["text"] for hit in search_results["hits"]["hits"]]
    )

    # TODO: supabase에 결과 저장
    # 결과를 Supabase에 저장하는 예시 코드 (실제 구현에 따라 변경 필요)
    # supabase_handler.save_query_response(user_id, session_id, user_query, answer)

    answer = llm_model.ask(user_query, combined_text)
    # 임시 응답 반환 (실제 구현에 맞게 수정 필요)
    response = {
        "user_id": user_id,
        "session_id": session_id,
        "user_query": user_query,
        "answer": answer,
    }

    return json.dumps(response, ensure_ascii=False)


if __name__ == "__main__":
    app.run(debug=True, port=8080)


"""
curl -X POST http://localhost:8080/query \
-H "Content-Type: application/json" \
-d '{
  "user_id": "uni2237",
  "chat_session_id": "000",
  "user_query": "미래에셋맵스 92호 펀드와 부동산 매각 관련 뉴스 있어?"
}'
"""
