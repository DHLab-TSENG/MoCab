import csv
import re
from base.exceptions import RegexUnrecognizedException
from munch import DefaultMunch

"""
    data structure of _ModelFeature :
        {
            model name: {
                feature: {
                    "type": category or numeric or formula,
                    "case": [{
                        "prefix": prefix, prefix in ModelFeature or None
                        "condition": value, int or float or str, time would probably be needed(any situation?),
                        "category": category
                    }]
                }
            }
        }
"""
prefix_list = [
    "eq",
    "ne",
    "gt",
    "lt",
    "ge",
    "lt",
    "ge",
    "le"
]


class _HooksConfigTable:
    def __init__(self, cds_hooks_config_table_position="./config/cds_hooks_config.csv"):
        self.table = self.__create_table(cds_hooks_config_table_position)

    @classmethod
    def __create_table(cls, cds_hooks_config_table_position):
        table = {}

        with open(cds_hooks_config_table_position, newline='') as hooks_config_table:
            rows = csv.DictReader(hooks_config_table)
            for row in rows:
                # 新建以model 為Key 的Dictionary
                if row['model'] not in table:
                    table[row['model']] = {}

                for key, value in row.items():
                    try:
                        table[row['model']][key] = globals()[f"{key}_value_handler"](value)
                    except KeyError:
                        table[row['model']][key] = value

        return table

    def get_cds_hooks_table_dict(self, model_name):
        # TODO: table_obj = DefaultMunch.fromDict(table.table), change table into table object
        if model_name not in self.table:
            raise KeyError(f"Model '{model_name}' is not exist in the CDS Hook table.")

        return self.table[model_name]


def condition_value_handler(value) -> dict:
    """
        Handler of columns in cds_hooks_config.csv. If the condition hasn't been given, it means execute this
    model anyway.

    :param: value: value in condition
    :return: dictionary, example:{"gender": [{"prefix": "", condition: ""}]
                                  "age": [{"prefix": "", condition: ""}],
                                  "encounter_type": [{"prefix": "",
                                                      "condition": any encounter_type in Encounter.class.code}]
                                }
    """
    return_dict = {}
    if value == '':
        return return_dict

    for i in value.split("&"):
        result = analyze_value(i)
        if result.category not in return_dict:
            return_dict[result.category] = []
        return_dict[result.category].append({"prefix": result.prefix,
                                             "condition": result.condition})
    return return_dict


def _range_value_handler(value) -> list:
    """
        Handler of columns in cds_hooks_config.csv. If the condition hasn't been given, it means execute this
    model anyway.

    :param: value: value in condition
    :return: list, example:[{"prefix": "lt", condition: "3"}, {"prefix": "ge", condition: "5"}]

    """
    return_list = []
    if value == '':
        return return_list

    for i in value.split("&"):
        result = analyze_value(i)
        return_list.append({"prefix": result.prefix, "condition": result.condition})
    return return_list


def info_range_value_handler(value) -> list:
    return _range_value_handler(value)


def warning_range_value_handler(value) -> list:
    return _range_value_handler(value)


def critical_range_value_handler(value) -> list:
    return _range_value_handler(value)


def analyze_value(value) -> DefaultMunch:
    return_dict = {
        "category": None,
        "prefix": "eq",
        "condition": None
    }
    regex_with_prefix = re.compile(r"(.*?) ?= ?([a-zA-Z]{2})\|(.*)")
    regex_without_prefix = re.compile(r"(.*?) ?= ?(.*)")
    regex_take_value_prefix = re.compile(r"(\w{2})\|(-?\d+\.?\d*)")

    result_regex_with_prefix = regex_with_prefix.search(value)
    result_regex_without_prefix = regex_without_prefix.search(value)
    result_regex_take_value_prefix = regex_take_value_prefix.search(value)

    if result_regex_with_prefix:
        return_dict['category'] = transform_to_correct_type(result_regex_with_prefix.group(1))
        return_dict['prefix'] = result_regex_with_prefix.group(2)
        return_dict['condition'] = transform_to_correct_type(result_regex_with_prefix.group(3))

    elif result_regex_without_prefix:
        return_dict['category'] = transform_to_correct_type(result_regex_without_prefix.group(1))
        return_dict['condition'] = transform_to_correct_type(result_regex_without_prefix.group(2))

    elif result_regex_take_value_prefix:
        return_dict['prefix'] = result_regex_take_value_prefix.group(1)
        return_dict['condition'] = transform_to_correct_type(result_regex_take_value_prefix.group(2))

    else:
        raise RegexUnrecognizedException(f"Regex cannot recognized '{value}'.")

    return DefaultMunch.fromDict(return_dict)


def transform_to_correct_type(input_string: str):
    if input_string.lower() == 'true':
        return True
    elif input_string.lower() == 'false':
        return False

    try:
        output = int(input_string)
    except ValueError:
        try:
            output = float(input_string)
        except ValueError:
            output = input_string

    return output


if __name__ == "__main__":
    import json

    # TODO: Write test case
    cds_hooks_config_table = _HooksConfigTable("../config/cds_hooks_config.csv")
    print(json.dumps(cds_hooks_config_table.get_cds_hooks_table_dict("pima_diabetes"), indent=2))

