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
                        "host": self.config["elastic_search"]["localhost"],
                        "port": self.config["elastic_search"]["port"],
                        "scheme": self.config["elastic_search"]["https"],
                    }
                ],
                basic_auth=(es_username, es_password),
                verify_certs=False,
            )
            return es
        except Exception as e:
            logging.error(f"elasticsearch 연결 실패,{e}")
            return False

    def chunked_text(self, text, chunk_size):
        chunked_texts = []
        overlap = int(chunk_size * self.config["overlap_ratio"])

        i = 0
        while i < len(text):
            chunked_texts.append(text[i : i + chunk_size])
            i += chunk_size - overlap

        return chunked_texts

    def get_embedding_vector(self, text):
        chunk_size = self.input_max_length
        if len(text) > chunk_size:
            logging.info(
                "Input text is longer than max length of the model. \n start chunking"
            )
            chunked_texts = self.chunked_text(text, chunk_size)
        else:
            chunked_texts = [text]

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
        # TODO: metadata 까지 인덱싱하도록 수정, text 값이 contents 만인지 제목+본문인지는 테스트 해서 더 잘되는걸로 수정
        context = data["title"] + data["content"]
        embedding_vector = self.get_embedding_vector(context)
        embedding_list = embedding_vector.numpy()[0].tolist()

        try:
            self.es.index(
                index="news",
                body={
                    "topic": data["topic"],
                    "title": data["title"],
                    "summary": data["summary"],
                    "context": context,
                    "embedding": embedding_list,
                },
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
