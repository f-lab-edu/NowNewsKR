import os
from transformers import AutoModel, AutoTokenizer


def save_model_with_name(model_name):
    # 모델 및 토크나이저 불러오기
    model = AutoModel.from_pretrained(model_name)
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    # 모델 저장 경로 설정
    model_path = f"./embedding/models/{model_name.replace('/', '_')}"

    # 모델 저장
    os.makedirs(model_path, exist_ok=True)  # 폴더 생성
    model.save_pretrained(model_path)
    tokenizer.save_pretrained(model_path)


# 모델 이름을 입력하고 호출하면 모델을 저장합니다.
model_name = "BM-K/KoSimCSE-roberta"
save_model_with_name(model_name)
