import torch
import yaml
import logging
from elasticsearch import Elasticsearch
from transformers import AutoModel, AutoTokenizer


class EmbeddingModel:
    def __init__(self, yaml_path):
        self.config = None
        self.model = None
        self.tokenizer = None
        self.es = None
        self.load_configuration(yaml_path)

    def load_configuration(self, yaml_path):
        self.config = self.load_yaml(yaml_path)
        self.model, self.tokenizer = self.load_model()
        self.es = self.initialize_elasticsearch()

    @staticmethod
    def load_yaml(yaml_path):
        with open(yaml_path, "r") as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
        return config

    def load_model(self):
        model = AutoModel.from_pretrained(self.config["embedding_model"])
        tokenizer = AutoTokenizer.from_pretrained(self.config["embedding_model"])
        return model, tokenizer

    def initialize_elasticsearch(self):
        es_username = self.config["elastic_search"]["es_username"]
        es_password = self.config["elastic_search"]["es_password"]
        try:
            es = Elasticsearch(
                [{"host": "localhost", "port": 9200, "scheme": "https"}],
                basic_auth=(es_username, es_password),
                verify_certs=False,
            )
            return es
        except Exception as e:
            print(e, "Elasticsearch 연결 실패")
            return None

    def get_embedding_vector(self, text):
        max_length = self.tokenizer.model_max_length
        print(f"==== max_length : {max_length}  / len(text) : {len(text)}====")
        try:
            if len(text) > max_length:
                logging.warning("Input text is longer than max length of the model.")
                raise ValueError
            else:
                inputs = self.tokenizer(
                    text, padding=True, truncation=True, return_tensors="pt"
                )
                with torch.no_grad():
                    embeddings = self.model(**inputs).pooler_output
                return embeddings[0]
        except ValueError as ve:
            logging.error(ve)
            return None

    def index_data_to_elasticsearch(self, data):
        # TODO: metadata 까지 인덱싱하도록 수정, 데이터 청크로 나눔 여부 고려
        text = data["content"]
        embedding_vector = self.get_embedding_vector(text)
        try:
            self.es.index(
                index="news",
                body={"text": text, "embedding": embedding_vector.numpy().tolist()},
            )
        except Exception as e:
            print(e, "데이터 인덱싱 실패")

    def search_data_in_elasticsearch(self, user_query):
        # TODO: search 수정
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
