import os
import sys
import logging
from dotenv import load_dotenv
from supabase import create_client, Client


class SupabaseHandler:
    def __init__(self):
        self.supabase_url = None
        self.supabase_key = None
        self.supabase_table = None
        self.client = None

    def superbase_init(self):
        (
            self.supabase_url,
            self.supabase_key,
            self.supabase_table,
        ) = self.load_env_variables()
        self.client: Client = create_client(self.supabase_url, self.supabase_key)

    @classmethod
    def load_env_variables(cls):
        load_dotenv()
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_KEY")
        supabase_table = os.environ.get("SUPABASE_TABLE")

        if not all([supabase_url, supabase_key, supabase_table]):
            logging.error("Please set SUPABASE_URL, SUPABASE_KEY, SUPABASE_TABLE")
            sys.exit(1)

        return supabase_url, supabase_key, supabase_table

    def save_news_to_supabase(self, news_document):
        news_item = news_document.to_superbase_format()

        print(news_item)
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
                if hasattr(response, "error") and response.error:
                    print(f"Error saving data: {response.error.message}")
            else:
                # 새 레코드 삽입
                response = (
                    self.client.table(self.supabase_table).insert(news_item).execute()
                )
                if hasattr(response, "error") and response.error:
                    print(f"Error saving data: {response.error.message}")
        except Exception as e:
            print("An error occurred while saving to Supabase: %s", e)
