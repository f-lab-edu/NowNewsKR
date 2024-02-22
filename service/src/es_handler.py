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
        self.create_es_index()

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
                        "format": "yyyy-MM-dd'T'HH:mm:ss",  # 이 필드에 대한 날짜 형식을 지정
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
            "_source": ["title", "text"],  # 검색 결과에 포함할 필드 지정
            "size": top_k,  # 반환할 문서의 최대 개수
            "min_score": score_threshold,  # 임계값 이상의 스코어를 가진 문서만 반환
        }

        try:
            response = self.es.search(index="news", body=search_body)
            return response
        except Exception as e:
            logging.error(f"elasticsearch 데이터 검색 실패, {e}")
            return False
