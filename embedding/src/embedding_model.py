import logging
import os
import sys
import torch
import yaml
import urllib3

from transformers import AutoModel, AutoTokenizer

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

current_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.join(current_dir, "..", "..")
common_src_path = os.path.join(project_dir, "common", "src")
sys.path.append(os.path.join(project_dir, common_src_path))

from config import Config


class EmbeddingModel:
    def __init__(self, yaml_path=Config.YAML_PATH):
        self.config = None
        self.model = None
        self.tokenizer = None
        self.load_configuration(yaml_path)

    def load_configuration(self, yaml_path):
        self.config = self.load_yaml(yaml_path)
        self.model, self.tokenizer, self.input_max_length = self.load_model()

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
