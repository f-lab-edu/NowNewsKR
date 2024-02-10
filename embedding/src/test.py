import logging
from embedding_model import EmbeddingModel


def main():
    embedding_model = EmbeddingModel("./conf.yaml")

    # 데이터 색인화 예시
    data = {
        "url": "https://n.news.naver.com/mnews/article/014/0005140769",
        "topic": "증권",
        "title": "떡값 재테크 갑진년 어떤 펀드가 내 지갑 불려줄까",
        "status": "Success",
        "content": "미래에셋한투삼성NH아문디KB신한운용 등 국내 대표 운용사 추천펀드CD금리투자 ETFAI시대 반도체ETF 금채굴ETF 등 최근 트렌드 상품 눈길 \n\n\n\n 파이낸셜뉴스 설을 맞아 떡값 재테크에 관심이 집중되고 있다   10일 국내 대표 운용사들은 안정적인 성과와 함께 최신 트렌드에 적합한 반도체나 금 채굴 인공지능AI 등 다양한 테마형 섹터 상장지수펀드ETF를 추천했다   과거 어린이펀드나 전 생애주기에 맞춘 포트폴리오형 상품인 타깃데이트펀드TDF를 추천하던 트렌드와는 대비되는 행보라는 평가도 나온다   우선 미래에셋운용은 TIGER CD금리투자KIS ETF를 추천했다 아이들에게 금융상품 투자 교육 차원에서 위함상품 보다 안전한 상품을 통해 자산증식의 중요성을 가르치키 적절하다는 이유에서다   이 상품은 순자산이 7조원이 넘는 국내 최대 ETF다 미래에셋운용 관계자는 CD금리 ETF에 투자함을 통해 금리와 예금 ETF개념을 배우면서 확실하게 수익이 나는 과정을 통해서 투자에 대한 호기심 즐거움을 가질 수 있을 것이라고 말했다   삼성자산운용과 한국투신은용은 각각 AI 환경에 수혜를 받을 수 있는 KODEX 미국반도체MV ETF와 ACE 미국 빅테크 TOP7Plus ETF를 제안했다   최근 청소년들이 챗GPT 등 AI환경엔 친숙하고 반도체 산업이나 엔비디아와 같은 기업들이 익숙해서 관련 산업에 관심이 많아 쉽게 접근할 수 있다는 이유다 삼섬운용은 시간이 흐를수록 반도체 산업의 성장도 함께할 것으로 전망돼 이 상품을 추천한다고 언급했다   한투운용의 ACE 미국빅테크TOP7 Plus는 구글 엔비디아 메타 테슬라 등 갈수록 차별화된 경쟁력을 보유하고 있는 빅테크 M7에 집중 투자하는 상품이다   한투운용 측은 M7을 중심으로 한 빅테크 기업들이 최근 미국 주식시장 상승을 주도하고 있어 긍정적이라고 설명했다 실제 기기 자체에 AI를 장착하는 온디바이스 AI 시장의 경우 오는 2032년까지 연평균 20 수준으로 성장해 700억달러 규모가 될 것으로 전망되고 있다   NH아문디운용은 글로벌 금광업Gold Miners에 투자할 수 있는 국내 최초 금 채굴기업 ETF HANARO 금채굴기업 ETF를 추천했다   이 펀드는 NYSE Arca Gold Miner IndexGDM를 기초지수로 추종하며 GDM은 미국 캐나다 호주 남미 등지의 글로벌 금 채굴 관련 종목 51개를 편입중이다 금 채굴 기업의 주가는 금 가격 대비 높은 변동성을 보여 금 가격 상승 시 금 투자 대비 높은 투자 수익률 추구할 수 있어 중장기적으로 안정적이라는 분석이다   KB자산운용은 미국 대표지수에 투자하는 인덱스펀드 2종을 신한자산운용은 매달 이자처럼 용돈 받는 신한자산운용 월배당 ETF를 각각 떡값 재테크 대안으로 내세웠다   KB자산운용에 따르면 KB스타 미국 나스닥100 인덱스와 KB스타 미국 SP500 인덱스의 지난달 말 기준 1년 수익률은 각각 413 212다   KB운용 관계자는 지난 1년간 양호한 성과를 기록중인 두 미국 인덱스펀드에 각각 494억원 132억원이 유입됐다라며 인덱스펀드는 추종지수의 시장 평균 수익률을 따라가는 것을 목표로 하는 패시브수동형펀드여서 보수가 저렴하기 때문에 장기적으로 안정적인 투자가 중요한 연금 고객에게 적합하다고 전했다   국내 투자자들에게 솔미당이라 불리는 신한운용의 SOL미국배당다우존스 ETF는 매월 이자처럼 용돈을 받을 수 있는 신한자산운용의 대표 월배당 ETF다   한국판 SCHDSchwab US Dividend Equity로 미국 배당 대표 ETF에 월배당 구조를 가미한 상품이다 연 3대의 배당수익률을 안정적으로 유지하고 있으며 지난 5년간 연평균 약 12의 배당금 증가율을 기록했다 지수와 동일한 수준의 배당수익률과 증가율을 바탕으로 개인투자자들 중심으로 장기 적립식 투자에 최적화된 상품으로 평가받는다 미래에셋 kb자산운용 한국투신 펀드 신한자산운용 떡값재테크펀드",
        "summary": "설을 맞아 떡값 재테크에 관심이 집중되고 있다 10일 국내 대표 운용사들은 안정적인 성과와 함께 최신 트렌드에 적합한 반도체나 금",
        "press": "파이낸셜뉴스",
        "journalist": "김경아 기자",
        "date": "2024-02-10 10:31:01",
    }

    # data indexing
    # index_result = embedding_model.index_data_to_elasticsearch(data)
    # print(f"==============indexing 결과: {index_result}===============")

    # user query search

    user_query = "etf 추천 관련 뉴스 있어?"
    search_results = embedding_model.search_data_in_elasticsearch(user_query)
    if not search_results:
        logging.info("검색 결과가 없거나 검색 중 오류가 발생했습니다.")
    else:

        for i, hit in enumerate(search_results["hits"]["hits"]):
            print(f"[{i}] Score: {hit['_score']}, Text: {hit['_source']['text']}\n")


if __name__ == "__main__":
    main()
    # embedding_model = EmbeddingModel("./conf.yaml")
    # embedding_model.delete_news_index()
