from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mask_mart import MaskMart
    from regex import RegexSearch


class MaskType(ABC):
    """
    The Observer interface declares the update method, used by subjects.
    """

    @abstractmethod
    def update(self, subject: MaskMart) -> int:
        """
        Receive update from subject.
        """
        pass


"""
Concrete Observers react to the updates issued by the Subject they had been
attached to.
"""


class ConcreteMaskType(MaskType):

    def __init__(self, name, *regexes: RegexSearch):
        self.name = name
        self.regex_search_sets = []
        for regex in regexes:
            if isinstance(regex, RegexSearch):
                self.regex_search_sets.append(regex)
            else:
                raise AttributeError("Regexes expected a RegexSearch Object, but {} was initialized"
                                     .format(type(regex).__name__)
                                     )

    def update(self, treatment_medication_text: str) -> dict | None:
        response = None
        if len(self.regex_search_sets) == 0:
            print("There are no search regex in the MaskObserver, please update new searches into MaskObserver with \
             update_search_regex() Observer function.")
        else:
            response = self._regex_search_method(treatment_medication_text)

            # TODO: 應該要用一個contains來先判斷treatment_medication_text是否有change等特殊連貫字詞
            # TODO: 特殊連貫字詞應該有一個value set儲存各種字詞
            # 判斷treatment text是否有連貫特殊字詞，如"->", "change", reverse的目的是要優先讓split後面的字串被判斷
            treatment_medication_text_after_split = treatment_medication_text.split("->")
            treatment_medication_text_after_split.reverse()
            if len(treatment_medication_text_after_split) != 1:
                for treatment_medication_text_split in treatment_medication_text_after_split:
                    temp = self._regex_search_method(treatment_medication_text_split)
                    if temp is not None:
                        response = temp
                        break
            return response

    def _regex_search_method(self, treatment_medication_text: str) -> dict | None:
        response = {"type": "", "value": 0}
        for regex_search in self.regex_search_sets:
            regex_search_response = regex_search.search(treatment_medication_text)
            if regex_search_response is not None:
                response['type'] = regex_search.name
                response['value'] = int(regex_search_response)
                return response
        return None

    def attach_search_regex(self, *regex_searches: RegexSearch):
        for regex_search in regex_searches:
            self.regex_search_sets.append(regex_search)
