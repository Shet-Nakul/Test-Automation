from abc import ABC, abstractmethod
from core.models import ImpactReport

class BaseReporter(ABC):
    @abstractmethod
    def report(self, report: ImpactReport, **kwargs):
        pass
