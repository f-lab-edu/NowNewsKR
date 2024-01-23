import torch
from transformers import AutoModel, AutoTokenizer
from elasticsearch import Elasticsearch
import supabase


class EmbeddingModel:
    def __init__(self, model_name):
        self.model = AutoModel.from_pretrained(model_name)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)

    def get_embedding_vector(self, text):
        inputs = self.tokenizer(
            text, padding=True, truncation=True, return_tensors="pt"
        )
        with torch.no_grad():
            embeddings = self.model(**inputs).pooler_output
        return embeddings[0]

    def index_data_to_elasticsearch(self, data):
        es = Elasticsearch([{"host": "localhost", "port": 9200}])
        text = data["content"]  # 데이터 필드에 따라 수정 필요
        embedding_vector = self.get_embedding_vector(text)
        es.index(
            index="news_index",
            body={"text": text, "embedding": embedding_vector.numpy().tolist()},
        )

    def search_data_in_elasticsearch(self, user_query):
        # TODO
        pass
