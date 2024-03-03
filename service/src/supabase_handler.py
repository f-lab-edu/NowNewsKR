import os
import sys
import logging
import yaml
from datetime import datetime

from supabase import create_client, Client

from config import Config, Topic, NewsDocuments


class SupabaseConfig:
    def __init__(self, yaml_path=Config.YAML_PATH):
        self.config = None
        self.supabase_url = None
        self.supabase_key = None
        self.supabase_table_news = None
        self.supabase_table_users = None
        self.supabase_table_sessions = None
        self.supabase_table_messages = None
        self.load_config(yaml_path)

    def load_config(self, yaml_path):
        self.config = self.load_yaml(yaml_path)
        self.supabase_url = self.config["supabase"]["supabase_url"]
        self.supabase_key = self.config["supabase"]["supabase_key"]
        self.supabase_table_news = self.config["supabase"]["tables"]["news"]
        self.supabase_table_users = self.config["supabase"]["tables"]["users"]
        self.supabase_table_sessions = self.config["supabase"]["tables"]["sessions"]
        self.supabase_table_messages = self.config["supabase"]["tables"]["messages"]

    def load_yaml(self, yaml_path):
        with open(yaml_path, "r") as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
        return config


class SupabaseHandler:
    def __init__(self, yaml_path=Config.YAML_PATH):
        self.supabase_config = SupabaseConfig(yaml_path)
        self.supabase_url = self.supabase_config.supabase_url
        self.supabase_key = self.supabase_config.supabase_key
        self.supabase_table_news = self.supabase_config.supabase_table_news
        self.supabase_table_users = self.supabase_config.supabase_table_users
        self.supabase_table_sessions = self.supabase_config.supabase_table_sessions
        self.supabase_table_messages = self.supabase_config.supabase_table_messages

        self.client: Client = create_client(self.supabase_url, self.supabase_key)

    def save_news_to_supabase(self, news_document):
        news_item = news_document.to_superbase_format()
        logging.info(f"Saving to Supabase: {news_item}")

        try:
            existing_record = (
                self.client.table(self.supabase_table_news)
                .select("*")
                .eq("url", news_item["url"])
                .execute()
            )
            if existing_record.data:
                # 기존 레코드 업데이트
                response = (
                    self.client.table(self.supabase_table_news)
                    .update(news_item)
                    .eq("url", news_item["url"])
                    .execute()
                )
            else:
                # 새 레코드 삽입
                response = (
                    self.client.table(self.supabase_table_news)
                    .insert(news_item)
                    .execute()
                )

            if hasattr(response, "error") and response.error:
                logging.error(f"Error saving data: {response.error.message}")

        except Exception as e:
            logging.error("An error occurred while saving to Supabase: %s", e)

    def get_news_data_from_supabase(self):
        try:
            existing_record = (
                self.client.table(self.supabase_table_news)
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

    def update_news_db_index_status(self, data):
        try:
            response = (
                self.client.table(self.supabase_table_news)
                .update({"is_indexed": True})
                .eq("url", data.url)
                .execute()
            )
            return response
        except Exception as e:
            logging.error("An error occurred while updating Supabase: %s", e)
            return False

    def reset_news_db_index_status(self):
        try:
            # Supabase 테이블의 모든 아이템에 대해 is_indexed 값을 False로 설정
            response = (
                self.client.table(self.supabase_table_news)
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
                id=item.get("id"),
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

    def check_or_create_user_session(self, user_id, session_id):
        # 사용자 존재 여부 확인
        user_response = (
            self.client.table(self.supabase_table_users)
            .select("user_id")
            .eq("user_id", user_id)
            .execute()
        )
        if not user_response.data:
            # 사용자가 존재하지 않으면 생성
            self.client.table(self.supabase_table_users).insert(
                {"user_id": user_id}
            ).execute()

        # 세션 존재 여부 확인
        session_response = (
            self.client.table(self.supabase_table_sessions)
            .select("session_id")
            .eq("session_id", session_id)
            .execute()
        )
        if not session_response.data:
            # 세션이 존재하지 않으면 생성
            self.client.table(self.supabase_table_sessions).insert(
                {
                    "session_id": session_id,
                    "user_id": user_id,
                    "created_at": datetime.now().isoformat(),
                }
            ).execute()

    def save_message(self, session_id, text, sender, original_db_ids, es_document_ids):
        # 메시지 정보를 DB에 저장
        message_data = {
            "session_id": session_id,
            "text": text,
            "sender": sender,
            "es_document_id": es_document_ids,
            "original_db_id": original_db_ids,
            "created_at": datetime.utcnow().isoformat(),
        }
        self.client.table(self.supabase_table_messages).insert(message_data).execute()

    def get_last_user_interactions(self, session_id, limit=3):
        # 세션 ID에 해당하는 마지막 몇 번의 질문과 대답을 가져옴
        response = (
            self.client.table(self.supabase_table_messages)
            .select("*")
            .eq("session_id", session_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )

        if response.data:
            return response.data
        else:
            return []


def main():

    # SupabaseHandler 객체 생성
    supabase_handler = SupabaseHandler()

    # 데이터 가져오기
    data = supabase_handler.get_news_data_from_supabase()

    # 데이터를 NewsDocuments 객체로 변환
    news_documents = supabase_handler.data_to_news_documents(data)

    # 반환된 데이터 사용
    for item in news_documents:
        logging.info(item)


if __name__ == "__main__":
    main()
