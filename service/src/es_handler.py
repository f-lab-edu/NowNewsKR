import yaml
import logging
from elasticsearch import Elasticsearch

from config import Config


class ElasticSearchHandler:
    def __init__(self, yaml_path=Config.YAML_PATH):
        self.config = None
        self.es = None
        self.load_configuration(yaml_path)

    def load_configuration(self, yaml_path):
        self.config = self.load_yaml(yaml_path)
        self.es = self.initialize_elasticsearch()

    @staticmethod
    def load_yaml(yaml_path):
        with open(yaml_path, "r") as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
        return config

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

    def search_data_in_elasticsearch(self, user_query_vector, top_k, score_threshold):
        # TODO: lexical search를 위한 elasticsearch 검색 구현

        search_body = {
            "query": {
                "script_score": {
                    "query": {"match_all": {}},
                    "script": {
                        "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                        "params": {
                            "query_vector": user_query_vector,
                        },
                    },
                }
            },
            "_source": ["db_id", "title", "text"],  # 검색 결과에 포함할 필드 지정
            "size": top_k,  # 반환할 문서의 최대 개수
            "min_score": score_threshold,  # 임계값 이상의 스코어를 가진 문서만 반환
        }

        try:
            response = self.es.search(index="news", body=search_body)
            combined_search_text = self.combine_search_results(response)
            db_ids, es_doc_ids = self.extract_document_ids(response)
            return combined_search_text, db_ids, es_doc_ids
        except Exception as e:
            logging.error(f"elasticsearch 데이터 검색 실패, {e}")
            return False, False, False

    def combine_search_results(self, response):
        combined_text = "\n".join(
            [hit["_source"]["text"] for hit in response["hits"]["hits"]]
        )
        return combined_text

    def extract_document_ids(self, response):
        db_ids = [hit["_source"]["db_id"] for hit in response["hits"]["hits"]]
        es_doc_ids = [hit["_id"] for hit in response["hits"]["hits"]]
        return db_ids, es_doc_ids
