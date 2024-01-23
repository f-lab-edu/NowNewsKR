import os
import sys
import torch
from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from transformers import AutoModel, AutoTokenizer

# 현재 스크립트의 디렉토리를 가져와 sys.path에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, ".."))


class EmbeddingModel:
    def __init__(self, model_name):
        dotenv_path = "./service/src/.env"  # .env 파일의 실제 경로로 변경해야 합니다.
        # /Users/yunhuicho/Documents/myGit/NowNewsKR/service/src/.env
        # .env 파일을 불러옵니다.
        load_dotenv(dotenv_path)
        self.model = AutoModel.from_pretrained(model_name)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.es_username = os.getenv("ES_USERNAME")
        self.es_password = os.getenv("ES_PASSWORD")
        try:
            self.es = Elasticsearch(
                [{"host": "localhost", "port": 9200, "scheme": "https"}],
                basic_auth=(self.es_username, self.es_password),
                verify_certs=False,
            )
        except Exception as e:
            print(e, "Elasticsearch 연결 실패")

    def get_embedding_vector(self, text):
        inputs = self.tokenizer(
            text, padding=True, truncation=True, return_tensors="pt"
        )
        with torch.no_grad():
            embeddings = self.model(**inputs).pooler_output
        return embeddings[0]

    def index_data_to_elasticsearch(self, data):
        text = data["content"]  # 데이터 필드에 따라 수정 필요
        embedding_vector = self.get_embedding_vector(text)
        try:
            self.es.index(
                index="news",
                body={"text": text, "embedding": embedding_vector.numpy().tolist()},
            )
        except Exception as e:
            print(e, "데이터 인덱싱 실패")

    def search_data_in_elasticsearch(self, user_query):
        query_embedding = self.get_embedding_vector(user_query)
        search_body = {
            "query": {
                "script_score": {
                    "query": {"match_all": {}},
                    "script": {
                        "source": "cosineSimilarity(params.query_embedding, doc['embedding']) + 1.0",
                        "params": {"query_embedding": query_embedding.tolist()},
                    },
                }
            }
        }
        try:
            results = self.es.search(index="news", body=search_body)
            return results
        except Exception as e:
            print(e, "데이터 검색 실패")
            return None
