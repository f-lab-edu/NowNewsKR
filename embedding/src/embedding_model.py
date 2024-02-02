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
        self.model, self.tokenizer, self.input_max_length = self.load_model()
        self.es = self.initialize_elasticsearch()

    @staticmethod
    def load_yaml(yaml_path):
        with open(yaml_path, "r") as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
        return config

    def load_model(self):
        model = AutoModel.from_pretrained(self.config["embedding_model"])
        tokenizer = AutoTokenizer.from_pretrained(self.config["embedding_model"])
        input_max_length = tokenizer.model_max_length
        return model, tokenizer, input_max_length

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
            logging.error(f"elasticsearch 연결 실패,{e}")
            return False

    def chunked_text(self, text):
        if len(text) > self.input_max_length:
            logging.info(
                "Input text is longer than max length of the model. \n start chunking"
            )
            return [
                text[i : i + self.input_max_length]
                for i in range(0, len(text), self.input_max_length)
            ]
        else:
            return [text]

    def get_embedding_vector(self, text):
        chunked_texts = self.chunked_text(text)
        embeddings = []
        for chunk in chunked_texts:
            inputs = self.tokenizer(
                chunk, padding=True, truncation=True, return_tensors="pt"
            )
            with torch.no_grad():
                embedding = self.model(**inputs).pooler_output
                embeddings.append(embedding)

        result_embedding = torch.mean(torch.stack(embeddings), dim=0)
        return result_embedding

    def index_data_to_elasticsearch(self, data):
        # TODO: metadata 까지 인덱싱하도록 수정, 데이터 청크로 나눔 여부 고려
        text = data["content"]
        embedding_vector = self.get_embedding_vector(text)
        embedding_list = embedding_vector.numpy()[0].tolist()
        print(self.es)
        print(embedding_list)
        try:
            self.es.index(
                index="news",
                body={"text": text, "embedding": embedding_list},
            )
        except Exception as e:
            logging.error(f"elasticsearch 데이터 인덱싱 실패, {e}")

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
            logging.error(f"elasticsearch 데이터 검색 실패, {e}")
            return False
