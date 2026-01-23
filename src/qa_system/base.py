from abc import ABC, abstractmethod
from typing import Dict, Any

class QAModule(ABC):
    def __init__(self, name: str):
        self.name = name
        self.results: Dict[str, Any] = {}
        self.status: str = "PENDING"  # PASS, FAIL, PENDING, ERROR

    @abstractmethod
    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the validation logic.
        :param data: Input data dictionary containing images, metadata, etc.
        :return: Dictionary of validation results.
        """
        pass
