from abc import ABC
from abc import abstractmethod


class BaseScraper(ABC):
    def __init__(self, order):
        self.order = order

    @abstractmethod
    def run(self):
        pass
