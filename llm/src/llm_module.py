import torch
import yaml
import logging
from transformers import AutoTokenizer, AutoModelForCausalLM
from accelerate import disk_offload


class LLMModule:
    def __init__(self, yaml_path):
        self.config = None
        self.model = None
        self.tokenizer = None
        self.load_configuration(yaml_path)

    def load_configuration(self, yaml_path):
        self.config = self.load_yaml(yaml_path)
        self.model, self.tokenizer = self.load_model()

    @staticmethod
    def load_yaml(yaml_path):
        with open(yaml_path, "r") as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
        return config

    def load_model(self):
        # TODO: 모델 로드 및 토크나이저 설정
        """
        model = AutoModelForCausalLM.from_pretrained(
            self.config["llm_module"], device_map="cuda:0"
        )
        model = AutoModelForCausalLM.from_pretrained(
            self.config["llm_module"], device_map="auto"
        )"""

        model = AutoModelForCausalLM.from_pretrained(
            self.config["llm_module"],
            local_files_only=True,  # Load from local disk only
            use_cache=False,  # Disable caching
            return_dict=True,  # Return the model as a PyTorch dictionary)
        )
        tokenizer = AutoTokenizer.from_pretrained(self.config["llm_module"])

        return model, tokenizer

    # TODO: 프롬프트 엔지니어링(프롬프트 추가, 영어 테스트), indicator 포맷 변경(영어로 변경), input 청크
    def ask(self, question, context="", max_new_tokens=512, temperature=0.7, top_p=0.9):
        # 질문과 맥락을 결합하여 입력 텍스트 생성
        input_text = (
            f"### 질문: {question}\n\n### 맥락: {context}\n\n### 답변:"
            if context
            else f"### 질문: {question}\n\n### 답변:"
        )
        inputs = self.tokenizer.encode(input_text, return_tensors="pt").to(
            device="cuda:0"
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
        print(answer)
