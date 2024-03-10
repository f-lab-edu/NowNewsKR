import logging
import os
import sys
import yaml

current_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.join(current_dir, "..", "..")

emb_src_path = os.path.join(project_dir, "embedding", "src")
sys.path.append(os.path.join(project_dir, emb_src_path))

common_src_path = os.path.join(project_dir, "common", "src")
sys.path.append(os.path.join(project_dir, common_src_path))

rag_src_path = os.path.join(project_dir, "rag-service", "src")
sys.path.append(os.path.join(project_dir, rag_src_path))

from config import Config, Topic, NewsDocuments
from supabase_handler import SupabaseHandler

from embedding_model import EmbeddingModel

from es_handler import ElasticSearchHandler


class ESIndexer:
    def __init__(self, embedding_model, yaml_path=Config.YAML_PATH):
        self.config = None
        self.es = None
        self.embedding_model = embedding_model
        self.load_configuration(yaml_path)
        self.create_es_index()

    def load_configuration(self, yaml_path):
        self.config = self.load_yaml(yaml_path)
        self.es = ElasticSearchHandler().es

    @staticmethod
    def load_yaml(yaml_path):
        with open(yaml_path, "r") as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
        return config

    def create_es_index(self):
        index_name = "news"  # 인덱스 이름 변경 가능
        index_settings = {
            "settings": {
                "number_of_shards": 1,  # 샤드 수는 요구 사항에 따라 조정
                "number_of_replicas": 0,  # 복제본 수는 요구 사항에 따라 조정
            },
            "mappings": {
                "properties": {
                    "db_id": {"type": "long"},  # 원본 DB의 int8 ID를 위한 매핑
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

    def index_data_to_elasticsearch(self, data):

        # TODO: metadata 까지 인덱싱하도록 수정, text 값이 contents 만인지 제목+본문인지는 테스트 해서 더 잘되는걸로 수정
        prompt_text = f"뉴스제목: {data.title}\n 뉴스내용: "
        context = data.content
        # get chunked texts
        chunk_size = self.embedding_model.input_max_length - len(prompt_text)

        chunked_texts = (
            [prompt_text + context]
            if len(context) <= chunk_size
            else self.chunked_text(prompt_text, context, chunk_size)
        )

        for chunk in chunked_texts:
            embedding_vector = self.embedding_model.get_embedding_vector(chunk)
            if embedding_vector is None:
                return False

            body = {
                "db_id": data.id,
                "topic": data.topic,
                "title": data.title,
                "summary": data.summary,
                "press": data.press,
                "date": data.date,
                "text": chunk,
                "embedding": embedding_vector,
            }

            try:
                response = self.es.index(
                    index="news",
                    body=body,
                )
                logging.info(
                    f"elasticsearch 데이터 인덱싱 성공, 문서 ID: {response['_id']}"
                )
            except Exception as e:
                logging.error(f"elasticsearch 데이터 인덱싱 실패: {e}")
                return False

        return True

    def delete_news_index(self):
        try:
            response = self.es.indices.delete(index="news")
            logging.info("인덱스 'news'가 성공적으로 삭제되었습니다.")
            return response
        except Exception as e:
            logging.error(f"인덱스 삭제 중 오류가 발생했습니다: {e}")
            return None


if __name__ == "__main__":

    # SupabaseHandler 객체 생성
    supabase_handler = SupabaseHandler()
    embedding_model = EmbeddingModel()

    # 데이터 가져오기
    news_db = supabase_handler.get_news_data_from_supabase()

    # 데이터를 NewsDocuments 객체로 변환
    news_documents = supabase_handler.data_to_news_documents(news_db)
    es_indexer = ESIndexer(embedding_model)
    # 반환된 데이터 사용
    for news_doc in news_documents:
        logging.info(news_doc)

        # data indexing
        index_result = es_indexer.index_data_to_elasticsearch(news_doc)
        logging.info(f"Indexing result: {index_result}")

        if index_result:
            news_doc.is_indexed = True
            # supabase에 is_indexed 값 업데이트
            update_result = supabase_handler.update_news_db_index_status(news_doc)
            logging.info(f"Update result: {update_result}")

    # indexed data 삭제
    # es_indexer.delete_news_index()
    # supabase_handler.reset_news_db_index_status()
