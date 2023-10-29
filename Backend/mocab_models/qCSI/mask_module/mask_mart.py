from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List
from typing import Dict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mask_type import MaskType


class MaskMart(ABC):
    """
    The Subject interface declares a set of methods for managing subscribers.
    """

    @abstractmethod
    def attach(self, observer: MaskType) -> None:
        """
        Attach an observer to the subject.
        """
        pass

    @abstractmethod
    def detach(self, observer: MaskType) -> None:
        """
        Detach an observer from the subject.
        """
        pass

    @abstractmethod
    def notify(self) -> Dict or None:
        """
        Notify all observers about an event.
        """
        pass


class ConcreteMaskMart(MaskMart):
    """
    For the sake of simplicity, the Subject's state, essential to all
    subscribers, is stored in this variable.
    """

    _types: List[MaskType] = []
    """
    List of subscribers. In real life, the list of subscribers can be stored
    more comprehensively (categorized by event type, etc.).
    """

    def attach(self, observer: MaskType, index: int = 0) -> None:
        if observer in self._types:
            print('Observer was already attached.')
        elif index > 0 and (index - 1) < len(self._types):
            self._types.insert(index - 1, observer)
        else:
            self._types.append(observer)

    def detach(self, observer: MaskType) -> None:
        if observer in self._types:
            self._types.remove(observer)
        else:
            print("The observer is not in the Subject.")

    """
    The subscription management methods.
    """

    def notify(self, treatment_medication_request: str) -> Dict or None:
        """
        Trigger an update in each subscriber.
        """

        for observer in self._types:
            observer_response = observer.update(treatment_medication_request)
            if observer_response:
                return {
                    "mask_name": observer.name,
                    "unit_type": observer_response["type"],
                    "value": observer_response["value"]
                }

        # If none of the observers match the treatment medication request, return None
        return None

    def treatment_mining(self, treatment_medication_text: str) -> Dict or None:
        """
        Usually, the subscription logic is only a fraction of what a Subject can
        really do. Subjects commonly hold some important business logic, that
        triggers a notification method whenever something important is about to
        happen (or after it).
        """

        return self.notify(treatment_medication_text)
