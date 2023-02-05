from typing import Any
from abc import ABC, abstractmethod


class Assets(ABC):
    """
    Base class for getting and setting values by key
    """

    @abstractmethod
    def get(self, key: str) -> Any:
        pass

    @abstractmethod
    def set(self, key: str, value: Any):
        pass

    def __getitem__(self, key: str) -> Any:
        return self.get(key)

    def __setitem__(self, key: str, value: Any):
        self.set(key, value)
