from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ElasticSettings:
    host: str = "elastic"
    port: int = 9200
    username: str = "elastic"
    password: str = "pass123"
    index: str = "pages"

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}/"


ELASTIC_SETTINGS = ElasticSettings()
