from typing import Dict


class Config:
    """
    Wraps a dict and allows accessing its content as attributes of this instance
    """

    def __init__(self, data: Dict):
        self.__data = data

    def __getitem__(self, item):
        return self.__data.get(item)

    def __getattr__(self, item):
        return self.__data.get(item)
