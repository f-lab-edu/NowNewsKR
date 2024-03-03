from enum import Enum


class Config:
    STOCK_URL = "https://finance.naver.com/news/mainnews.nhn"
    NEWS_URL = "https://n.news.naver.com/mnews/article"
    YAML_PATH = "conf.yaml"
    ENCODING = "utf-8"


class Topic(Enum):
    STOCK = "증권"

    # TODO : Add more topics
    # SPORTRS = "스포츠"
    # ENTERTAINMENT = "연예"
    # ECONOMY = "경제"
    # SOCIETY = "사회"
    # LIFE = "생활/문화"
    # WORLD = "세계"
    # IT = "IT/과학"


class NewsDocuments:
    def __init__(
        self,
        url,
        topic,
        title,
        status,
        content,
        summary,
        press,
        journalist,
        date,
        is_indexed,
        id=None,
    ):
        self.id = id
        self.url = url
        self.topic = topic
        self.title = title
        self.status = status
        self.content = content
        self.summary = summary
        self.press = press
        self.journalist = journalist
        self.date = date
        self.is_indexed = is_indexed

    def __repr__(self):
        return f"NewsDocuments({self.id}, {self.url}, {self.topic}, {self.title}, {self.status}, {self.content}, {self.summary}, {self.press}, {self.journalist}, {self.date}, {self.is_indexed})"

    def to_superbase_format(self):
        data = {
            "url": self.url,
            "topic": self.topic,
            "title": self.title,
            "status": self.status,
            "content": self.content,
            "summary": self.summary,
            "press": self.press,
            "journalist": self.journalist,
            "date": self.date,
            "is_indexed": self.is_indexed,
        }
        if self.id is not None:
            data["id"] = self.id
        return data
