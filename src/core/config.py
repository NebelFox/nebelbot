class Config:
    def __init__(self, data):
        self.__data = data

    def __getitem__(self, item):
        return self.__data.get(item)

    def __getattr__(self, item):
        return self.__data.get(item)
