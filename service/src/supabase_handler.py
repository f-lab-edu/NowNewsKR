import os
import sys
import logging
import yaml

from supabase import create_client, Client

from config import Config, Topic, NewsDocuments


class SupabaseConfig:
    def __init__(self, yaml_path=Config.YAML_PATH):
        self.config = None
        self.supabase_url = None
        self.supabase_key = None
        self.supabase_table = None
        self.load_config(yaml_path)

    def load_config(self, yaml_path):
        self.config = self.load_yaml(yaml_path)
        self.supabase_url = self.config["supabase"]["supabase_url"]
        self.supabase_key = self.config["supabase"]["supabase_key"]
        self.supabase_table = self.config["supabase"]["supabase_table"]

    def load_yaml(self, yaml_path):
        with open(yaml_path, "r") as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
        return config


class SupabaseHandler:
    def __init__(self, yaml_path=Config.YAML_PATH):
        self.supabase_config = SupabaseConfig(yaml_path)
        self.supabase_url = self.supabase_config.supabase_url
        self.supabase_key = self.supabase_config.supabase_key
        self.supabase_table = self.supabase_config.supabase_table
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
                self.client.table(self.supabase_table)
                .select("*")
                .eq("is_indexed", False)  # 인덱싱되지 않은 데이터만 가져오기
                .execute()
            )
            if existing_record.data:
                return existing_record.data
            else:
                logging.info("No data found in Supabase.")
                return []
        except Exception as e:
            logging.error("Supabase data load 실패: %s", e)
            return False

    def update_db_index_status(self, data):
        try:
            response = (
                self.client.table(self.supabase_table)
                .update({"is_indexed": True})
                .eq("url", data.url)
                .execute()
            )
            return response
        except Exception as e:
            logging.error("An error occurred while updating Supabase: %s", e)
            return False

    def reset_db_index_status(self):
        try:
            # Supabase 테이블의 모든 아이템에 대해 is_indexed 값을 False로 설정
            response = (
                self.client.table(self.supabase_table)
                .update({"is_indexed": False})
                .eq("is_indexed", True)
                .execute()  # 특정 조건 없이 모든 레코드에 대해 실행
            )

            logging.info(
                "Successfully reset is_indexed status for all items in Supabase."
            )
            return response
        except Exception as e:
            logging.error("An error occurred while resetting Supabase: %s", e)
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
                is_indexed=item.get("is_indexed"),
            )
            documents.append(document)
        return documents


def main():

    # SupabaseHandler 객체 생성
    supabase_handler = SupabaseHandler()

    # 데이터 가져오기
    data = supabase_handler.get_data_from_supabase()

    # 데이터를 NewsDocuments 객체로 변환
    news_documents = supabase_handler.data_to_news_documents(data)

    # 반환된 데이터 사용
    for item in news_documents:
        logging.info(item)


if __name__ == "__main__":
    main()
