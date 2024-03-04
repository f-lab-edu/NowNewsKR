
# 베이스 이미지 지정
FROM python:3.11

# 작업 디렉토리 지정
WORKDIR /app

# 의존성 파일 복사 및 설치
COPY crawler/requirements.txt ./
RUN pip install -r requirements.txt

# 소스 코드 복사
COPY rag-service/src ./rag-service/src
COPY crawler/src ./crawler/src
COPY llm/src ./llm/src
COPY embedding/src ./embedding/src
COPY embedding/models ./embedding/models
COPY common/src ./common/src
COPY conf.yaml ./
#COPY . .

# Python 모듈 경로 추가
ENV PYTHONPATH "${PYTHONPATH}:/app"

# 컨테이너 실행 시 실행할 명령어 지정
CMD ["python", "crawler/src/crawler_indexer.py"]
