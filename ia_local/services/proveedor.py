from abc import ABC, abstractmethod


class AIProvider(ABC):
    @abstractmethod
    def healthcheck(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def model_available(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def structured_chat(self, messages, schema) -> str:
        raise NotImplementedError
