from abc import ABC, abstractmethod
import re


class RegexSearch(ABC):
    """
    The regex_search interface declares the regex search method and a list to store all the regex that it needs. Used for MaskObserver.
    """

    @abstractmethod
    def search(self, string: str) -> int:
        pass


class ConcreteRegexSearch(RegexSearch):

    def __init__(self, name: str, regex_patterns: str = None):
        self.name = name
        self._regex_patterns = []
        if isinstance(regex_patterns, str):
            self._regex_patterns.append(regex_patterns)
        elif isinstance(regex_patterns, list):
            self._regex_patterns += regex_patterns
        else:
            print("Regex patterns must be String or List[str]")

    def search(self, string: str) -> int or None:
        if len(self._regex_patterns) > 0:
            for pattern in self._regex_patterns:

                regex = re.search(pattern, string, re.IGNORECASE)
                if regex:
                    result = regex.group(1)
                    result = result \
                        .replace(" ", "") \
                        .replace("l", "") \
                        .replace("L", "") \
                        .replace("%", "")
                    return int(result)
        else:
            return None

    @property
    def pattern(self):
        return self._regex_patterns

    @pattern.setter
    def pattern(self, pattern_string: str):
        self._regex_patterns.append(pattern_string)

    @pattern.setter
    def pattern(self, pattern_list: list):
        self._regex_patterns.append(pattern_list)

    def delete(self, pattern_string: str):
        if pattern_string in self._regex_patterns:
            self._regex_patterns.remove(pattern_string)
            print(pattern_string + " deleted successfully")
        else:
            print(pattern_string + " is not in the list, please check again.")
