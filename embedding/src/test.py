import logging
from embedding_model import EmbeddingModel


def main():
    embedding_model = EmbeddingModel("./conf.yaml")

    # 데이터 색인화 예시
    data = {
        "content": "샘 올트먼 오픈AI CEO왼쪽 과 사티야 나델라 마이크로소프트 CEO AFP뉴스1서울뉴스1 김정현 기자  연초 이후 상승세를 보인 반도체 관련주가 23일에도 강세를 보였다 챗 GPT를 개발한 오픈AI의 샘 올트먼 최고경영자CEO의 방한 및 협력 추진 소식도 영향을 미친 것으로 보인다이날 한국거래소에 따르면 반도체 기업 어보브반도체102120 가온칩스399720는 전일 대비 각각 3750원2318 9000원1345 오른 1만9930원 7만5900원에 거래를 마쳤다반도체 유통기업인 유니퀘스트077500 주가도 전일 대비 2070원3000 올라 상한가로 장을 마감했다이외에도 워트396470 1321 샘씨엔에스252990 1209 아이앤씨052860 666 SFA반도체036540 665 등 반도체 관련주들도 일제히 상승세를 보였다이날 반도체 관련주가 강세를 보인 것은 최근 미국에서 시작된 반도체인공지능AI 훈풍에 이어 샘 올트먼 CEO의 방한 소식도 영향을 미친 것으로 분석된다업계에 따르면 샘 울트먼 CEO는 오는 26일 한국을 방문해 삼성전자005930 SK하이닉스000660의 반도체 현장을 방문하고 협력을 논의할 예정이다 오픈 AI는 이번 한국 방문을 통해 국내 반도체 기업들과 공급망 구축을 추진할 것으로 예상되고 있다한지영 키움증권 연구원은 반도체 및 AI 주들의 주가 변화에 주목할 필요가 있다며 오픈 AI 의 CEO 샘올트만의 주중 국내 방한소식은 반도체 및 AI 관련 업체들과의 협업 혹은 투자 기대감이 형성될 것이라고 설명했다"
    }
    embedding_model.index_data_to_elasticsearch(data)

    # 사용자 쿼리 검색 예시
    user_query = "검색할 텍스트 입력"
    search_results = embedding_model.search_data_in_elasticsearch(user_query)

    # 검색 결과 출력
    for hit in search_results["hits"]["hits"]:
        logging.info(f"Score: {hit['_score']}, Text: {hit['_source']['text']}")


if __name__ == "__main__":
    main()
