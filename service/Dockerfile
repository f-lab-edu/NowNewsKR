
# 베이스 이미지 지정
FROM python:3.11

# 작업 디렉토리 지정
WORKDIR /app

# 의존성 파일 복사 및 설치
COPY ./service/requirements.txt /app/

RUN pip install -r requirements.txt

# 소스 코드 복사
COPY ./service/src /app/src/
# COPY ./service/src /app/
# COPY ./service/scripts /app/scripts/

# 컨테이너 실행 시 실행할 명령어 지정
CMD ["python", "src/crawler.py"]
