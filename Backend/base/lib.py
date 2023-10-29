import operator
import re
from datetime import datetime
from dateutil.relativedelta import relativedelta

import numpy as np

from base.exceptions import ThresholdNoneError, VariableNoneError


def transform_to_correct_type(input_string: str, special_type="value"):
    special_types = ["value", "date"]
    if special_type not in special_types:
        raise ValueError(f"special_type must be one of {special_types}")

    if special_type == 'date':
        return datetime_handler(input_string)

    input_string = str(input_string)
    mapping_dict = {
        "true": True,
        "false": False,
        "nan": np.nan,
        "none": None
    }

    if input_string.lower() in mapping_dict:
        return mapping_dict[input_string.lower()]

    try:
        output = int(input_string)
    except ValueError:
        try:
            output = float(input_string)
        except ValueError:
            output = input_string

    return output


def datetime_handler(date_string: str or datetime):
    """
    Handle the datetime string to datetime object.
    """
    if type(date_string) == datetime:
        return date_string

    if date_string == "" or date_string is None:
        return None

    datetime_format = [
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%SZ"
    ]
    try:
        return datetime.fromisoformat(date_string)
    except ValueError:
        for fmt in datetime_format:
            try:
                return datetime.strptime(date_string, fmt)
            except ValueError:
                continue

    raise ValueError(
        "The datetime string is not in correct format. Got: " + date_string)


class TimeObject:
    def __init__(self, data_alive_time):
        self._years = 0
        self._months = 0
        self._days = 0
        self._hours = 0
        self._minutes = 0
        self._seconds = 0
        self.__set_data_alive_time(data_alive_time)

    def __set_data_alive_time(self, data_alive_time):
        datetime_prog = re.compile(
            r"[0-9]{4}-(0[0-9]|1[12])-([12][0-9]|3[01]|0[0-9])T(20|21|22|23|[0-1]\d):[0-5]\d:[0-5]\d")
        date_prog = re.compile(
            r"[0-9]{4}-(0[0-9]|1[12])-([12][0-9]|3[01]|0[0-9])")
        if datetime_prog.search(data_alive_time):
            date, time = data_alive_time.split(
                'T')[0], data_alive_time.split('T')[1]
            self._years = int(date.split('-')[0])
            self._months = int(date.split('-')[1])
            self._days = int(date.split('-')[2])
            self._hours = int(time.split(':')[0])
            self._minutes = int(time.split(':')[1])
            self._seconds = int(time.split(':')[2])
        elif date_prog.search(data_alive_time):
            self._years = int(data_alive_time.split('-')[0])
            self._months = int(data_alive_time.split('-')[1])
            self._days = int(data_alive_time.split('-')[2])
        else:
            raise ValueError(
                "The Time Format is incorrect, " + data_alive_time)

    def get_years(self):
        return self._years

    def get_months(self):
        return self._months

    def get_days(self):
        return self._days

    def get_hours(self):
        return self._hours

    def get_minutes(self):
        return self._minutes

    def get_seconds(self):
        return self._seconds

    def get_days_from_now(self):
        future_date = datetime.now() + relativedelta(years=self._years, months=self._months,
                                                     days=self._days, hours=self._hours, minutes=self._minutes, seconds=self._seconds)
        return (future_date - datetime.now()).days

    def return_datetime(self) -> datetime:
        return datetime(self._years, self._months, self._days, self._hours, self._minutes, self._seconds)


class BaseVariable:
    def __init__(self, feature, var_type):
        """
        Base object of all variables

        :param feature: name of feature
        :param var_type: type of variable, e.g. numeric, category, and formulate.
        """
        self.feature = feature
        self.type = var_type

    def get_value(self):
        pass


class Operation:

    # TODO: 原先的variable可以為None, 但為什麼？
    def __init__(self, variable: BaseVariable, threshold, prefix: str = "eq"):
        # Handle nan situation
        if threshold == "nan":
            threshold = np.nan
            if prefix == "eq":
                prefix = "is_"
            elif prefix == "ne":
                prefix = "is_not"
            else:
                raise ValueError(
                    f"prefix {prefix} is not valid for nan threshold.")

        self.variable = variable
        self.prefix = prefix
        self.threshold = threshold

    def validate(self):
        try:
            # TODO: 要想一下get_value 如果為nan時會不會有什麼Error
            thres = self.threshold
            if issubclass(type(thres), BaseVariable):
                thres = self.threshold.get_value()

            var = self.variable.get_value()

            if type(thres) == list:
                # TODO: 這裡有沒有可能是要用all? 極大機率要改架構
                return any(
                    [getattr(operator, self.prefix)(transform_to_correct_type(var), transform_to_correct_type(t)) for t in thres]
                )

            return getattr(operator, self.prefix)(transform_to_correct_type(var), transform_to_correct_type(thres))
        except KeyError:
            raise AttributeError(f"{self.prefix} is not a valid operator.")
        except Exception:
            return False


class FilterOperation:

    # TODO: 原先的variable可以為None, 但為什麼？
    def __init__(self, threshold, prefix: str = "eq", type: str = "value"):
        # Doesn't support nan threshold.
        # Reason: nan is not a valid filter while training. (Or maybe is?)
        self.prefix = prefix
        self.type = type
        self._threshold = threshold

    @property
    def threshold(self):
        return self._threshold

    @threshold.setter
    def threshold(self, value):
        if value == "nan":
            raise ValueError(f"nan is not a valid threshold.")
        else:
            self._threshold = value

    def validate(self, variable):
        if type(variable) == BaseVariable:
            var = variable.get_value()
        else:
            var = variable

        if type(self._threshold) == BaseVariable:
            thres = self._threshold.get_value()
        else:
            thres = self._threshold

        # Transfer to correct type
        thres = transform_to_correct_type(thres, self.type)
        var = transform_to_correct_type(var, self.type)

        # 目前想下來，當比較單位為時間，則threshold必須為datetime，否則回傳錯誤
        if thres is None:
            raise ThresholdNoneError(f"Threshold is None on {self.type} type.")

        if var is None:
            raise VariableNoneError(f"Variable is None on {self.type} type.")

        try:
            return getattr(operator, self.prefix)(var, thres)
        except KeyError:
            raise AttributeError(f"{self.prefix} is not a valid operator.")
        except TypeError as e:
            raise e
