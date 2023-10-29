import csv
import operator
import re

import numpy as np

from datetime import datetime
from base.lib import FilterOperation, TimeObject, BaseVariable, transform_to_correct_type
from base.exceptions import VariableNoneError, ThresholdNoneError


class _TrainingSet:

    def __init__(self,
                 data_filter: list,
                 interval: TimeObject,
                 null_value_strategy: dict,
                 training_config: dict):
        self.data_filter = data_filter
        self.interval = interval
        self.null_value_strategy = null_value_strategy
        self.training_config = training_config


class _TrainingSetTable:

    def __init__(self, table_position="./config/continuous_training/training_sets.csv"):
        self.table = self.__create_table(table_position)

    def __create_table(self, table_position) -> dict:
        with open(table_position, newline='') as training_sets_table:
            return_dict = {}
            rows = csv.DictReader(training_sets_table)

            for row in rows:
                special_columns = ["models", "filter", "interval", "null_value_strategy"]
                data_filter = self.data_filter_handler(row["filter"])
                interval = TimeObject(row["interval"])
                null_value_strategy = self.null_value_strategy_handler(row["null_value_strategy"])
                training_configs = dict()

                for key, value in row.items():
                    if key not in special_columns:
                        training_configs[key] = value

                return_dict[row["models"]] = \
                    _TrainingSet(data_filter, interval, null_value_strategy, training_configs)

            return return_dict

    @staticmethod
    def data_filter_handler(param) -> list:
        regex = re.compile(r"(\((date|value)\))?((eq|ne|lt|le|gt|ge)\|)?((\[\w+])|(\S+))")
        return_list = []
        for sub_param in param.split("&"):
            sub_param_regex = regex.match(sub_param)
            typing = "value"
            prefix = "eq"

            if sub_param_regex:
                if sub_param_regex.group(2) is not None:
                    typing = sub_param_regex.group(2)

                if sub_param_regex.group(4) is not None:
                    prefix = sub_param_regex.group(4)

                if sub_param_regex.group(6) is not None:
                    threshold = sub_param_regex.group(6)
                elif sub_param_regex.group(7) is not None:
                    threshold = sub_param_regex.group(7)
                else:
                    raise ValueError(f"data_filter format error: Must have threshold. Error: {sub_param}")
            else:
                raise ValueError("data_filter format error")

            return_list.append(
                FilterOperation(threshold=threshold, prefix=prefix, type=typing)
            )

        return return_list

    @staticmethod
    def null_value_strategy_handler(param) -> dict:
        return_dict = {}

        # Handle drop strategy first
        drop_param = param.split("&")[0]
        drop_regex = re.compile(r"\(drop\)((gt|ge)\|)?(\d+)")

        # Error handling
        if not drop_regex.match(drop_param):
            raise ValueError(f"null_value_strategy has a wrong structure in drop: '{drop_param}'")

        prefix = "lt"
        if drop_regex.match(drop_param).group(2) is not None:
            prefix = drop_regex.match(drop_param).group(2)
        threshold = drop_regex.match(drop_param).group(3)
        return_dict["drop"] = {
            "prefix": prefix,
            "threshold": threshold
        }

        # Handle fillna strategy
        fillna_param = "&".join(param.split("&")[1:])
        fillna_regex = re.compile(r"(\((median|mean|mode)\)|([\.\w]+))\|?(\[(\w+)])?")
        for sub_param in fillna_param.split("&"):
            method = None
            column = "default"

            # Error handling while wrong structure
            if not fillna_regex.match(sub_param):
                raise ValueError(f"null_value_strategy has a wrong structure in fillna: '{sub_param}'")

            if fillna_regex.match(sub_param).group(2) is not None:
                method = fillna_regex.match(sub_param).group(2)

            if fillna_regex.match(sub_param).group(3) is not None:
                if method is not None:
                    raise ValueError(f"null_value_strategy has a wrong structure in fillna: '{sub_param}'")
                method = transform_to_correct_type(fillna_regex.match(sub_param).group(3))

            if fillna_regex.match(sub_param).group(5) is not None:
                column = fillna_regex.match(sub_param).group(5)

            # Error handling while duplicated
            if column in return_dict:
                if column == "default":
                    raise ValueError(f"null_value_strategy has a duplicated default fillNA strategy: '{fillna_param}'")
                raise ValueError(f"null_value_strategy has a duplicated column: '{sub_param}'")

            return_dict[column] = method

        return return_dict

    def get_training_set(self, name: str) -> _TrainingSet:
        return self.table[name]

    def get_training_set_schedule(self) -> list:
        return_dict = []
        for name, training_set in self.table.items():
            temp_dict = {"model_name": name, "interval": training_set.interval}
            return_dict.append(temp_dict)
        return return_dict
