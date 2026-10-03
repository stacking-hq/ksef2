import httpx
from pydantic import BaseModel


class JsonResponseCodec:
    @staticmethod
    def parse[T: BaseModel](resp: httpx.Response, model: type[T]) -> T:
        return model.model_validate(resp.json())

    @staticmethod
    def parse_list[T: BaseModel](resp: httpx.Response, model: type[T]) -> list[T]:
        return [model.model_validate(item) for item in resp.json()]
