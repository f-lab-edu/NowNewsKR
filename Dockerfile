# 베이스 이미지 지정
FROM python:3.11.7

# 작업 디렉토리 설정
WORKDIR /app

# 현재 디렉토리의 requirements.txt를 /app으로 복사
COPY requirements.txt ./

# 필요한 패키지와 라이브러리 설치
RUN pip install --no-cache-dir -r requirements.txt

# 프로젝트의 모든 파일을 /app으로 복사
COPY . ./

# Flask 애플리케이션 실행 명령
CMD ["flask", "run", "--host=0.0.0.0", "--port=8080"]
