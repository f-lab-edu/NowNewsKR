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
from supabase_handler import SupabaseConfig, SupabaseHandler
from embedding_model import EmbeddingModel
from llm_module import LLMModule


def initialize_supabase():
    try:
        # Initialize Supabase configuration and handler
        supabase_config = SupabaseConfig(Config.YAML_PATH)
        supabase_handler = SupabaseHandler(supabase_config)

        # Retrieve data from Supabase
        data = supabase_handler.get_data_from_supabase()

        # Convert data to Python dictionary format
        data_dict = supabase_handler.data_to_news_documents(data)

        return data_dict

    except Exception as e:
        logging.error("An error occurred in initialize_supabase: %s", e)
        return None


def initialize_embedding_model(data_dict):
    try:
        # Initialize EmbeddingModel and index data to Elasticsearch
        embedding_model = EmbeddingModel(Config.YAML_PATH)
        embedding_model.index_data_to_elasticsearch(data_dict)

        return embedding_model

    except Exception as e:
        logging.error("An error occurred in initialize_embedding_model: %s", e)
        return None


def search_and_generate_response(embedding_model, user_query):
    try:
        # Example user query for search
        search_results = embedding_model.search_data_in_elasticsearch(user_query)
        logging.info(f"Search results: {search_results}")

        input_text = ""

        # Display search results
        for hit in search_results["hits"]["hits"]:
            logging.info(f"Score: {hit['_score']}, Text: {hit['_source']['text']}")
            input_text += hit["_source"]["text"] + " "

        # Initialize LLMModule and generate a response
        llm_model = LLMModule(Config.YAML_PATH)
        max_new_tokens = 512
        temperature = 0.7
        top_p = 0.9
        llm_model.ask(user_query, input_text, max_new_tokens, temperature, top_p)

    except Exception as e:
        logging.error("An error occurred in search_and_generate_response: %s", e)


def main():
    try:

        data_dict = initialize_supabase()
        embedding_model = initialize_embedding_model(data_dict)
        user_query = "Do you have any news related to semiconductors?"

        if data_dict and embedding_model:
            search_and_generate_response(embedding_model, user_query)

    except Exception as e:
        logging.error("An error occurred in main func: %s", e)


if __name__ == "__main__":
    main()
