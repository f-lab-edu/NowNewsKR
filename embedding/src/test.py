import logging
from embedding_model import EmbeddingModel


def main():
    embedding_model = EmbeddingModel("./conf.yaml")

    # user query search

    user_query = "엔비디아 관련 뉴스 있어?"
    search_results = embedding_model.search_data_in_elasticsearch(user_query, 3, 1.4)
    if not search_results:
        logging.info("검색 결과가 없거나 검색 중 오류가 발생했습니다.")
    else:

        for i, hit in enumerate(search_results["hits"]["hits"]):
            print(f"[{i}] Score: {hit['_score']}, Text: {hit['_source']['text']}\n")


if __name__ == "__main__":
    main()

    # indexed data 삭제
    # embedding_model = EmbeddingModel("./conf.yaml")
    # embedding_model.delete_news_index()
