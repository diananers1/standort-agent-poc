from abc import ABC, abstractmethod

from standort_agent.models import (
    InterpretedProfile,
    Municipality,
    SignalResult,
)


class SignalAgent(ABC):

    @abstractmethod
    def evaluate(
        self,
        municipality: Municipality,
        profile: InterpretedProfile,
        municipalities: list[Municipality],
    ) -> SignalResult:
        raise NotImplementedError