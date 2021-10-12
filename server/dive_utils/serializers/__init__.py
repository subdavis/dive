from abc import ABC, abstractmethod
from typing import ByteString, Iterable, List


class WrongDataType(Exception):
    """
    Parse operations return this exception if they are asked to parse
    incompatible data.
    """

    pass


class BaseParser(ABC):
    """
    Absctract base class for all data parser implementations
    """

    @classmethod
    @abstractmethod
    def parse(readers: List[Iterable[ByteString]]):
        pass
