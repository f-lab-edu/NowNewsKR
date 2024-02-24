import logging
import sys
import os
from embedding_model import EmbeddingModel

current_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.join(current_dir, "..", "..")
es_src_path = os.path.join(project_dir, "service", "src")
sys.path.append(os.path.join(project_dir, es_src_path))

from es_handler import ElasticSearchHandler


def main():
    embedding_model = EmbeddingModel()
    es_handler = ElasticSearchHandler()
    # user query search

    user_query = "엔비디아 관련뉴스 있어?"
    user_query_vector = embedding_model.get_embedding_vector(user_query)
    search_results = es_handler.search_data_in_elasticsearch(user_query_vector, 3, 1.4)

    print(f"Combined searched Text:\n{search_results}")


if __name__ == "__main__":
    main()

    # indexed data 삭제
    # embedding_model = EmbeddingModel()
    # embedding_model.delete_news_index()
