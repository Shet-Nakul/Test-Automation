from abc import ABC, abstractmethod
from typing import List, Optional
from core.models import ParsedFile

class BaseParser(ABC):
    @abstractmethod
    def parse_file(self, file_path: str) -> Optional[ParsedFile]:
        pass

    @abstractmethod
    def scan_repository(self, repo_path: str) -> List[ParsedFile]:
        pass
