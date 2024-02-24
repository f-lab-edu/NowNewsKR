import os
import logging
import sys
import yaml
from supabase import create_client, Client


def configure_project_paths():
    # Current script file's directory
    project_dir = os.path.dirname(os.path.abspath(__file__))

    # Add project directories to sys.path
    sys.path.append(os.path.join(project_dir, "llm/src"))
    sys.path.append(os.path.join(project_dir, "embedding/src"))
    sys.path.append(os.path.join(project_dir, "service/src"))


configure_project_paths()

from config import Config

# from supabase_handler import SupabaseConfig, SupabaseHandler
from embedding_model import EmbeddingModel
from llm_module import LLMModule
from es_handler import ElasticSearchHandler


class RAGApp:
    def __init__(self):
        self.embedding_model = None
        self.llm_model = None
        self.es_handler = None
        self.initialize_embedding_model()
        self.initialize_es_handler()
        self.initialize_llm()

    def initialize_embedding_model(self):
        try:
            # Initialize EmbeddingModel and index data to Elasticsearch
            self.embedding_model = EmbeddingModel()

        except Exception as e:
            logging.error("An error occurred in initialize_embedding_model: %s", e)

    def initialize_llm(self):
        try:
            # Initialize LLMModule
            self.llm_model = LLMModule()

        except Exception as e:
            logging.error("An error occurred in initialize_llm: %s", e)

    def initialize_es_handler(self):
        try:
            # Initialize Elasticsearch handler
            self.es_handler = ElasticSearchHandler()

        except Exception as e:
            logging.error("An error occurred in initialize_es_handler: %s", e)

    def search_newsdocuments(self, user_query, top_k, threshold):

        # Example user query for search
        user_query_vector = self.embedding_model.get_embedding_vector(user_query)
        search_results = self.es_handler.search_data_in_elasticsearch(
            user_query_vector, top_k, threshold
        )
        return search_results

    # TODO: input 청크
    def generate_answer(
        self, user_query, context, max_new_tokens=512, temperature=0.7, top_p=0.9
    ):
        # Generate answer using LLM
        answer = self.llm_model.ask(
            user_query, context, max_new_tokens, temperature, top_p
        )
        return answer


def main():
    rag_app = RAGApp()
    user_query = "엔비디아 관련뉴스 있어?"

    search_results = rag_app.search_newsdocuments(user_query, 3, 1.4)

    print(f"Combined search Text:\n{search_results}")

    answer = rag_app.generate_answer(user_query, context=search_results)
    print(f"Answer: {answer}")

    """성능 테스트
    [1]"엔비디아 관련 뉴스 있어?"
    ->
    Answer: 네, 최근 엔비디아가 AI 반도체 시장에서의 성장이 예상되어 많은 투자자들이 관심을 가지고 있습니다. 미국의 시장 조사업체 가트너는 엔비디아가 앞으로 더 많은 성장을 할 것으로 예측하고 있으며, 이에 따라 금융투자업계에서도 많은 관심을 받고 있습니다. 애플을 제외하고 엔비디아로 인해 서학개미들이 급격하게 매수세를 보이고 있습니다.

    [2] "엔비디아 매수할까?" (임베딩 결과는 threshold 값 통과하는 거 없었음)

    Answer: 주식 투자는 개인의 판단에 따라 다르기 때문에 정확한 답변을 드리기 어렵습니다. 그러나 엔비디아는 성장 가능성이 높은 기업으로 평가되고 있으며 최근 그래픽 카드 수요 증가와 인공지능 시장의 성장으로 인해 높은 수익성을 기대할 수 있습니다. 따라서 엔비디아에 대해 자세히 조사하고 투자 전 전략을 세우는 것이 중요합니다.
    
    """


if __name__ == "__main__":
    main()
