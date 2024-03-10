# 베이스 이미지 지정
FROM python:3.11.7

# 작업 디렉토리 설정
WORKDIR /app

# 현재 디렉토리의 requirements.txt를 /app으로 복사
COPY rag-service/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 프로젝트의 모든 파일을 /app으로 복사
COPY rag-service/src ./rag-service/src
COPY crawler/src ./crawler/src
COPY llm/src ./llm/src
COPY embedding/src ./embedding/src
COPY embedding/models ./embedding/models
COPY common/src ./common/src
COPY conf.yaml ./
# Flask 애플리케이션 실행 명령
CMD ["python", "rag-service/src/app.py"]

# root directory에서 다음 명령어 실행
# docker build -t rag-service:latest -f rag-service/Dockerfile .