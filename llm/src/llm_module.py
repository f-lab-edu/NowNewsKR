import logging
import torch
import yaml
import os
import sys
import openai
from accelerate import disk_offload
from transformers import AutoTokenizer, AutoModelForCausalLM

current_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.join(current_dir, "..", "..")
service_src_path = os.path.join(project_dir, "service", "src")
sys.path.append(os.path.join(project_dir, service_src_path))

from config import Config


class LLMModule:
    def __init__(self, yaml_path=Config.YAML_PATH):
        self.config = None
        self.model = None
        self.tokenizer = None
        self.device = None
        self.use_openai = None
        self.load_configuration(yaml_path)

    def load_configuration(self, yaml_path):
        self.config = self.load_yaml(yaml_path)
        self.device = self.load_device()
        if self.config["llm"]["use_openai"]:
            self.use_openai = True
            openai.api_key = self.config["openai"]["api_key"]
        else:
            self.model, self.tokenizer = self.load_model()

    @staticmethod
    def load_yaml(yaml_path):
        with open(yaml_path, "r") as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
        return config

    def load_device(self):
        device_map = self.config["device"]
        device = torch.device(
            device_map["gpu"] if torch.cuda.is_available() else device_map["cpu"]
        )
        return device

    def load_model(self):
        # TODO: 모델 로드 및 토크나이저 설정

        model = AutoModelForCausalLM.from_pretrained(
            self.config["llm"]["model_path"],
            local_files_only=True,  # Load from local disk only
            use_cache=False,  # Disable caching
            return_dict=True,  # Return the model as a PyTorch dictionary)
        )
        tokenizer = AutoTokenizer.from_pretrained(self.config["llm"]["model_path"])

        return model, tokenizer

    # TODO: 프롬프트 엔지니어링(프롬프트 추가, 영어 테스트), indicator 포맷 변경(영어로 변경), input 청크
    def ask(
        self,
        question,
        context,
        last_interactions,
        max_new_tokens=512,
        temperature=0.7,
        top_p=0.9,
    ):

        # 이전 대화 내용을 프롬프트에 포함
        previous_context = " ".join(
            [
                f"Question: {interaction['text']} Answer: {interaction['answer']}"
                for interaction in last_interactions
            ]
        )

        # 질문과 맥락을 결합하여 입력 텍스트 생성
        prompt = (
            # "Let's consider our previous conversations: "
            # f"{previous_context} "
            "Now, moving on to the user's current question: "
            f"'{question}'. "
            f"{'Considering the provided context: ' + context + ', ' if context else ''}"
            "please provide an answer to the question. "
            "If the question is about summarizing an article, let's break down the information into a few key points, like bullet points, to make it easy to understand. "
            "If the question relates to advice or opinion, imagine you're a consultant or a friend giving thoughtful advice based on your knowledge and the information provided. "
            "Note: The response is expected to be in Korean if the user's question is in Korean."
        )
        if self.use_openai:
            answer = self.ask_openai(prompt, max_new_tokens, temperature, top_p)
        else:
            inputs = self.tokenizer.encode(prompt, return_tensors="pt").to(
                device=self.device
            )

            # 텍스트 생성
            outputs = self.model.generate(
                inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
                do_sample=True,
            )

            # 생성된 텍스트 디코딩
            answer = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        return answer

    def ask_openai(
        self,
        prompt,
        max_new_tokens,
        temperature,
        top_p,
    ):

        # GPT API를 사용하여 텍스트 생성
        try:
            response = openai.Completion.create(
                engine="gpt-3.5-turbo-instruct",  # 사용할 GPT 모델 버전 지정
                prompt=prompt,
                max_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
            )

            generated_text = response.choices[0].text.strip()

            return generated_text
        except Exception as e:
            logging.error(f"GPT API 호출 중 오류 발생: {e}")
            return False
