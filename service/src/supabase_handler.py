import os
import sys
import logging
import yaml

from supabase import create_client, Client

from config import Config, Topic, NewsDocuments


class SupabaseConfig:
    def __init__(self, config_file_path):
        self.config_file_path = config_file_path
        self.supabase_url = None
        self.supabase_key = None
        self.supabase_table = None
        self.load_config()

    def load_config(self):
        try:
            with open(self.config_file_path) as f:
                conf = yaml.load(f, Loader=yaml.FullLoader)
            self.supabase_url = conf["supabase"]["supabase_url"]
            self.supabase_key = conf["supabase"]["supabase_key"]
            self.supabase_table = conf["supabase"]["supabase_table"]
        except Exception as e:
            logging.error("yaml 파일 load 실패: %s", e)


class SupabaseHandler:
    def __init__(self, supabase_config):
        self.supabase_url = supabase_config.supabase_url
        self.supabase_key = supabase_config.supabase_key
        self.supabase_table = supabase_config.supabase_table
        self.client: Client = create_client(self.supabase_url, self.supabase_key)

    def save_news_to_supabase(self, news_document):
        news_item = news_document.to_superbase_format()
        logging.info(f"Saving to Supabase: {news_item}")

        try:
            existing_record = (
                self.client.table(self.supabase_table)
                .select("*")
                .eq("url", news_item["url"])
                .execute()
            )
            if existing_record.data:
                # 기존 레코드 업데이트
                response = (
                    self.client.table(self.supabase_table)
                    .update(news_item)
                    .eq("url", news_item["url"])
                    .execute()
                )
            else:
                # 새 레코드 삽입
                response = (
                    self.client.table(self.supabase_table).insert(news_item).execute()
                )
            if hasattr(response, "error") and response.error:
                logging.error(f"Error saving data: {response.error.message}")

        except Exception as e:
            logging.error("An error occurred while saving to Supabase: %s", e)

    def get_data_from_supabase(self):
        try:
            existing_record = (
                self.client.table(self.supabase_table).select("*").execute()
            )
            if existing_record.data:
                return existing_record.data
            else:
                logging.info("No data found in Supabase.")
                return []
        except Exception as e:
            logging.error("Supabase data load 실패: %s", e)
            return False

    # 데이터를 Python dictionary 형태로 반환하는 함수 추가
    def data_to_news_documents(self, data):
        documents = []
        for item in data:
            document = NewsDocuments(
                url=item.get("url"),
                topic=item.get("topic"),
                title=item.get("title"),
                status=item.get("status"),
                content=item.get("content"),
                summary=item.get("summary"),
                press=item.get("press"),
                journalist=item.get("journalist"),
                date=item.get("date"),
            )
            documents.append(document)
        return documents


def main():

    # SupabaseConfig 객체 생성
    supabase_config = SupabaseConfig(Config.YAML_PATH)
    # SupabaseHandler 객체 생성
    supabase_handler = SupabaseHandler(supabase_config)

    # 데이터 가져오기
    data = supabase_handler.get_data_from_supabase()

    # 데이터를 NewsDocuments 객체로 변환
    news_documents = supabase_handler.data_to_news_documents(data)

    # 반환된 데이터 사용
    for item in news_documents:
        logging.info(item)


if __name__ == "__main__":
    main()
