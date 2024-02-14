import logging
import urllib3

import torch
import yaml
from elasticsearch import Elasticsearch
from transformers import AutoModel, AutoTokenizer

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class EmbeddingModel:
    def __init__(self, yaml_path):
        self.config = None
        self.model = None
        self.tokenizer = None
        self.es = None
        self.load_configuration(yaml_path)

    def load_configuration(self, yaml_path):
        self.config = self.load_yaml(yaml_path)
        self.model, self.tokenizer, self.input_max_length = self.load_model()
        self.es = self.initialize_elasticsearch()
        self.create_es_index()

    @staticmethod
    def load_yaml(yaml_path):
        with open(yaml_path, "r") as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
        return config

    def load_model(self):
        model = AutoModel.from_pretrained(self.config["embedding"]["model_path"])
        tokenizer = AutoTokenizer.from_pretrained(
            self.config["embedding"]["model_path"]
        )
        input_max_length = tokenizer.model_max_length
        return model, tokenizer, input_max_length

    def initialize_elasticsearch(self):
        es_username = self.config["elastic_search"]["es_username"]
        es_password = self.config["elastic_search"]["es_password"]

        try:
            es = Elasticsearch(
                [
                    {
                        "host": self.config["elastic_search"]["host"],
                        "port": self.config["elastic_search"]["port"],
                        "scheme": self.config["elastic_search"]["scheme"],
                    }
                ],
                basic_auth=(es_username, es_password),
                verify_certs=False,
            )
            return es
        except Exception as e:
            logging.error(f"elasticsearch 연결 실패,{e}")
            return False

    def create_es_index(self):
        index_name = "news"  # 인덱스 이름 변경 가능
        index_settings = {
            "settings": {
                "number_of_shards": 1,  # 샤드 수는 요구 사항에 따라 조정
                "number_of_replicas": 0,  # 복제본 수는 요구 사항에 따라 조정
            },
            "mappings": {
                "properties": {
                    "topic": {
                        "type": "keyword"
                    },  # 주제는 필터링에 사용될 수 있으므로 keyword 타입 사용
                    "title": {
                        "type": "text"
                    },  # 제목은 텍스트 검색에 사용될 수 있으므로 text 타입 사용
                    "summary": {
                        "type": "text"
                    },  # 요약은 텍스트 검색에 사용될 수 있으므로 text 타입 사용
                    "press": {"type": "keyword"},  # 출판사는 keyword 타입 사용
                    "date": {
                        "type": "date",  # 날짜 필드 유형을 명시
                        "format": "yyyy-MM-dd HH:mm:ss",  # 이 필드에 대한 날짜 형식을 지정
                    },
                    "text": {"type": "text"},  # 텍스트 검색을 위한 text 타입 사용
                    "embedding": {
                        "type": "dense_vector",
                        "dims": 768,
                    },  # 임베딩 벡터는 dense_vector 타입 사용
                }
            },
        }

        # 인덱스가 이미 존재하는지 확인
        if not self.es.indices.exists(index=index_name):
            # 인덱스 생성
            self.es.indices.create(index=index_name, body=index_settings)
            logging.info(f"{index_name} 인덱스 생성 완료.")
        else:
            logging.info(f"{index_name} 인덱스는 이미 존재합니다.")

    def chunked_text(self, prompt_text, text, chunk_size):
        chunked_texts = []
        overlap = int(chunk_size * self.config["overlap_ratio"])

        i = 0
        while i < len(text):
            chunk = prompt_text + text[i : i + chunk_size]
            chunked_texts.append(chunk)
            if len(chunk) < chunk_size:
                break
            i += chunk_size - overlap

        return chunked_texts

    def get_embedding_vector(self, text):
        try:
            inputs = self.tokenizer(
                text, padding=True, truncation=True, return_tensors="pt"
            )
            with torch.no_grad():
                embedding = self.model(**inputs).pooler_output
            return embedding.numpy()[0].tolist()
        except Exception as e:
            logging.error(f"Embedding vector 생성 실패: {e}")
            return None

    def index_data_to_elasticsearch(self, data):
        # TODO: metadata 까지 인덱싱하도록 수정, text 값이 contents 만인지 제목+본문인지는 테스트 해서 더 잘되는걸로 수정
        prompt_text = f"뉴스제목: {data['title']}\n 뉴스내용: "
        context = data["content"]
        # get chunked texts
        chunk_size = self.input_max_length - len(prompt_text)

        chunked_texts = (
            [prompt_text + context]
            if len(context) <= chunk_size
            else self.chunked_text(prompt_text, context, chunk_size)
        )

        for chunk in chunked_texts:

            embedding_vector = self.get_embedding_vector(chunk)
            if embedding_vector is None:
                return False

            body = {
                "topic": data["topic"],
                "title": data["title"],
                "summary": data["summary"],
                "press": data["press"],
                "date": data["date"],
                "text": chunk,
                "embedding": embedding_vector,
            }

            try:
                response = self.es.index(
                    index="news",
                    body=body,
                )
                logging.info(
                    f"[1] elasticsearch 데이터 인덱싱 성공, 문서 ID: {response['_id']}"
                )
            except Exception as e:
                logging.error(f"elasticsearch 데이터 인덱싱 실패: {e}")
                return False

        return True

    def search_data_in_elasticsearch(self, user_query):
        # TODO: search 수정
        user_query_vector = self.get_embedding_vector(user_query)

        search_body = {
            "query": {
                "script_score": {
                    "query": {"match_all": {}},
                    "script": {
                        "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                        "params": {"query_vector": user_query_vector},
                    },
                }
            },
            "_source": ["title", "text"],  # 검색 결과에 포함할 필드 지정
            "size": 3,  # 반환할 문서의 최대 개수
        }

        try:
            response = self.es.search(index="news", body=search_body)
            return response
        except Exception as e:
            logging.error(f"elasticsearch 데이터 검색 실패, {e}")
            return False

    def delete_news_index(self):
        try:
            response = self.es.indices.delete(index="news")
            logging.info("인덱스 'news'가 성공적으로 삭제되었습니다.")
            return response
        except Exception as e:
            logging.error(f"인덱스 삭제 중 오류가 발생했습니다: {e}")
            return None
