import logging
import os
import sys

from config import Config
from supabase_handler import SupabaseConfig, SupabaseHandler
from es_handler import ElasticSearchHandler

current_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.join(current_dir, "..", "..")
emb_src_path = os.path.join(project_dir, "embedding", "src")
sys.path.append(os.path.join(project_dir, emb_src_path))

from embedding_model import EmbeddingModel


class ESIndexer:
    def __init__(
        self, embedding_model: EmbeddingModel, es_handler: ElasticSearchHandler
    ):
        self.embedding_model = embedding_model
        self.es = es_handler.es

    def index_data_to_elasticsearch(self, data):

        # TODO: metadata 까지 인덱싱하도록 수정, text 값이 contents 만인지 제목+본문인지는 테스트 해서 더 잘되는걸로 수정
        prompt_text = f"뉴스제목: {data.title}\n 뉴스내용: "
        context = data.content
        # get chunked texts
        chunk_size = self.embedding_model.input_max_length - len(prompt_text)

        chunked_texts = (
            [prompt_text + context]
            if len(context) <= chunk_size
            else self.embedding_model.chunked_text(prompt_text, context, chunk_size)
        )

        for chunk in chunked_texts:
            embedding_vector = self.embedding_model.get_embedding_vector(chunk)
            if embedding_vector is None:
                return False

            body = {
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

    # SupabaseConfig 객체 생성
    supabase_config = SupabaseConfig(Config.YAML_PATH)
    # SupabaseHandler 객체 생성
    supabase_handler = SupabaseHandler(supabase_config)

    # 데이터 가져오기
    news_db = supabase_handler.get_data_from_supabase()

    # 데이터를 NewsDocuments 객체로 변환
    news_documents = supabase_handler.data_to_news_documents(news_db)

    embedding_model = EmbeddingModel(Config.YAML_PATH)
    es_handler = ElasticSearchHandler(Config.YAML_PATH)
    es_indexer = ESIndexer(embedding_model, es_handler)

    # 반환된 데이터 사용
    for news_doc in news_documents:
        logging.info(news_doc)

        # data indexing
        index_result = es_indexer.index_data_to_elasticsearch(news_doc)
        logging.info(f"Indexing result: {index_result}")

        if index_result:
            news_doc.is_indexed = True
            # supabase에 is_indexed 값 업데이트
            update_result = supabase_handler.update_db_index_status(news_doc)
            logging.info(f"Update result: {update_result}")

    # indexed data 삭제
    # es_indexer.delete_news_index()
    # supabase_handler.reset_db_index_status()
