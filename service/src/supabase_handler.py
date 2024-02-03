import os
import sys
import logging
import yaml

from supabase import create_client, Client


class SupabaseConfig:
    def __init__(self, config_file_path):
        self.config_file_path = config_file_path
        self.supabase_url = None
        self.supabase_key = None
        self.supabase_table = None
        self.load_config()

    def load_config(self):
        with open(self.config_file_path) as f:
            conf = yaml.load(f, Loader=yaml.FullLoader)
            self.supabase_url = conf["supabase"]["supabase_url"]
            self.supabase_key = conf["supabase"]["supabase_key"]
            self.supabase_table = conf["supabase"]["supabase_table"]


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
