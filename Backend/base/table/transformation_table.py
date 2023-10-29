import csv
import re

from pwnlib.util import safeeval

from base.lib import transform_to_correct_type, Operation, BaseVariable

prefix_list = [
    "eq",
    "ne",
    "gt",
    "ge",
    "lt",
    "le"
]

type_list = [
    "category",
    "numeric",
    "formula"
]


class NumericVariable(BaseVariable):
    def __init__(self, feature, observer):
        super().__init__(feature, "numeric")
        self._value = None
        observer.attach(self)

    def set_value(self, value):
        self._value = value

    def get_value(self):
        if issubclass(type(self._value), BaseVariable):
            return self._value.get_value()

        return self._value


class NumericObserver:
    def __init__(self):
        self._observers = []

    def attach(self, observer: NumericVariable):
        for i in range(len(self._observers)):
            if self._observers[i].feature == observer.feature:
                self._observers[i] = observer
                return
        self._observers.append(observer)

    def detach(self, observer: NumericVariable):
        self._observers.remove(observer)

    def callout_feature(self, feature_name) -> NumericVariable or None:
        for observer in self._observers:
            if observer.feature == feature_name:
                return observer
        return None

    def update_value(self, feature_name, value):
        for observer in self._observers:
            if observer.feature == feature_name:
                observer.set_value(value)
                break


"""
Transformation Table:
    having_betelnut,category,1=[betelnul1]|0&[betelnut2]gt|1&[betelnut3]|88,2
    having_betelnut,category,2=[betelnul1]|99&[betelnut2]gt|99&[betelnut3]|88,2

    Transformation Table:
        {
            index: 2,
            variables: [first_variable, second_variable, more_variables]
        }

    first_ConditionVariable = 1, [operation1_1, operation1_2, operation1_3]
    second_ConditionVariable = 2, [operation2_1, operation2_2, operation2_3]

    operation1_1: 
        baseVariable {default: variable_with_same_name}
        prefix {default: "eq"}
        threshold
"""


class CategoryVariable(BaseVariable):
    def __init__(self, feature):
        super().__init__(feature, "category")
        self.operations = []
        self._category = None

    @property
    def category(self):
        return self._category

    @category.setter
    def category(self, category):
        self._category = category

    def add_condition(self, condition: Operation):
        self.operations.append(condition)

    def get_value(self):
        if all([operation.validate() for operation in self.operations]):
            if issubclass(type(self.category), BaseVariable):
                return self.category.get_value()

            return self.category
        return None


class FormulaVariable(BaseVariable):
    def __init__(self, feature, formula=None):
        super().__init__(feature, "formula")
        self._formula = formula
        self._attributes = {}

    @property
    def formula(self):
        return self._formula

    @formula.setter
    def formula(self, formula):
        self._formula = formula

    def set_new_attr(self, name: str, variable: BaseVariable):
        self._attributes[name] = variable

    def get_value(self):
        formula = self.formula
        attributes = {(k, v.get_value()) for k, v in self._attributes.items()}

        return safeeval.values(formula, attributes)


def numeric_handler(feature_name: str, observer) -> NumericVariable:
    if observer.callout_feature(feature_name) is None:
        return NumericVariable(feature_name, observer)
    return observer.callout_feature(feature_name)


def category_handler(feature_name: str, formula: str, store_dict: dict, observer: NumericObserver) -> CategoryVariable:
    temp_variable = CategoryVariable(feature_name)
    category = transform_to_correct_type(formula.split("=")[0].strip())
    # Handle category while it is a variable
    if type(category) == str:
        if category.startswith("[") and category.endswith("]"):
            category = category[1:-1]
            if category in store_dict:
                category = store_dict[category]
            elif observer.callout_feature(category):
                category = observer.callout_feature(category)
            else:
                category = NumericVariable(category, observer)

    temp_variable.category = category
    formula = formula.split("=")[1].strip()

    condition_regex = re.compile(r"(\[.*])?([a-z]{2})?\|(.*)")
    # 將個別的condition拆開，並且將其轉換成Operation物件。
    for condition in formula.split("&"):
        regex_result = condition_regex.search(condition)

        # 如果沒有"|", 代表該condition只有threshold，沒有prefix與 variables。
        # 這時，prefix預設為"eq"，variables預設為與此feature name 相同的variable。
        if not regex_result:
            if condition == "[default]":
                # Default condition handling
                variable = store_dict['default']
            elif feature_name in store_dict:
                variable = store_dict[feature_name]
            elif observer.callout_feature(feature_name):
                variable = observer.callout_feature(feature_name)
            else:
                variable = NumericVariable(feature_name, observer)

            # Default prefix is "eq"
            prefix = "eq"

            # Threshold
            threshold = condition if condition != "[default]" else 99999
        else:
            # 如果有"|", 代表該condition 有prefix or variables
            # Variable
            if regex_result.group(1):
                variable_name = regex_result.group(1).strip("[]")
                variable = store_dict[variable_name]
            else:
                # 只有Feature name，沒有variable name
                if feature_name in store_dict:
                    variable = store_dict[feature_name]
                elif observer.callout_feature(feature_name):
                    variable = observer.callout_feature(feature_name)
                else:
                    variable = NumericVariable(feature_name, observer)

            # Prefix
            if regex_result.group(2):
                prefix = regex_result.group(2)
            else:
                prefix = "eq"

            # Threshold
            if regex_result.group(3):
                threshold = regex_result.group(3)
                if threshold.startswith('[') and threshold.endswith(']'):
                    threshold = threshold.strip('[]')
                    if threshold in store_dict:
                        threshold = store_dict[threshold]
                    elif observer.callout_feature(threshold):
                        threshold = observer.callout_feature(threshold)
                    else:
                        threshold = NumericVariable(threshold, observer)
            else:
                raise ValueError(f"Condition '{condition}' is not valid.")
        # 將Operation物件加入CategoryVariable物件中。
        if issubclass(type(threshold), BaseVariable):
            temp_variable.add_condition(Operation(variable, threshold, prefix))
        else:
            temp_variable.add_condition(Operation(variable, transform_to_correct_type(threshold), prefix))
    return temp_variable


def formula_handler(feature_name: str, formula: str, store_dict: dict) -> FormulaVariable:
    formula_feature_list = re.findall(r"\[\w*]", formula)
    rep = {"]": "", "[": ""}

    rep = dict((re.escape(k), v) for k, v in rep.items())
    pattern = re.compile("|".join(rep.keys()))

    formula = pattern.sub(lambda m: rep[re.escape(m.group(0))], formula)
    temp_variable = FormulaVariable(feature_name, formula)

    for feature in formula_feature_list:
        feature = pattern.sub(lambda m: rep[re.escape(m.group(0))], feature)
        temp_variable.set_new_attr(feature, store_dict[feature])

    return temp_variable


def variable_handler(variable_name, **kwargs) -> BaseVariable:
    variable_name = variable_name.lower()

    if variable_name == "numeric":
        return numeric_handler(kwargs["feature_name"], kwargs["observer"])
    elif variable_name == "category":
        return category_handler(kwargs["feature_name"], kwargs["formulate"], kwargs["store_dict"], kwargs["observer"])
    elif variable_name == "formula":
        return formula_handler(kwargs["feature_name"], kwargs["formulate"], kwargs["store_dict"])

    raise ValueError(f"Type '{variable_name}' is not valid.")


class _TransformationTable:
    def __init__(self, model_feature_table_position="./config/transformation.csv"):
        self.table = self.__create_table(model_feature_table_position)

    @classmethod
    def __create_table(cls, model_feature_table_position):
        with open(model_feature_table_position, newline='') as model_feature_table:
            rows = csv.DictReader(model_feature_table)
            """
            temp_dict = {
                row["models"]: {
                    row["feature"]: baseVariable
                }
            }
            """
            temp_dict = {}

            """
            real_dict = {
                row["models"]: {
                    "index": [],
                    "observer": NumericObserver()
                }
            }
            """
            real_dict = {}
            for row in rows:
                if row["feature"] == "default":
                    raise NameError(
                        "Feature name 'default' is a keyword in MoCab, change another feature name instead.")

                # Initialize
                if row["model"] not in real_dict:
                    real_dict[row["model"]] = {}
                    real_dict[row["model"]]["index"] = []
                    real_dict[row["model"]]["observer"] = NumericObserver()
                    real_dict[row["model"]]["column"] = []

                list_of_index = real_dict[row["model"]]["index"]
                list_of_column = real_dict[row["model"]]["column"]
                observer = real_dict[row["model"]]["observer"]

                if row["model"] not in temp_dict:
                    temp_dict[row["model"]] = {}
                    # [default] 為預設的Variable，只會在Category type 中出現。
                    # 必定回傳其category，所以只能寫在Transformation table中的最後面。
                    # e.g.: 9=[default]，必定回傳9。

                    # 實作上會先將[default]的Variable加入temp_dict中，並且將其value設為99999。
                    # Operator 則是[default]eq|99999。
                    default_variable = NumericVariable("default", observer)
                    default_variable.set_value(99999)
                    temp_dict[row["model"]]["default"] = default_variable

                # Create Variables
                kwargs = {
                    "feature_name": row["feature"],
                    "formulate": row["formulate"],
                    "store_dict": temp_dict[row["model"]],
                    "observer": observer
                }

                temp_variable = variable_handler(row["type"], **kwargs)

                # 如果row["index"] 為空，該variable 就會存放到temp_variable 中以利後續使用
                # 否則會直接儲存成list
                if row['index'] == "":
                    temp_dict[row["model"]][row["feature"]] = temp_variable
                else:
                    index = int(row["index"])
                    if index > len(list_of_index):
                        list_of_index += [None] * (index - len(list_of_index))
                        list_of_column += [None] * (index - len(list_of_column))
                    if list_of_index[index - 1] is None:
                        list_of_index[index - 1] = []
                    list_of_index[index - 1].append(temp_variable)
                    list_of_column[index - 1] = row["feature"]

        return real_dict

    def get_model_feature_dict(self, model_name):
        # TODO: table_obj = DefaultMunch.fromDict(table.table), change table into table object
        if model_name not in self.table:
            raise KeyError("Model is not exist in the feature table.")

        return self.table[model_name]

    def get_model_feature_column(self, model_name) -> list:
        if model_name not in self.table:
            raise KeyError("Model is not exist in the feature table.")

        return self.table[model_name]["column"]


if __name__ == "__main__":
    import json

    model_feature_table = _TransformationTable("../config/transformation.csv")
    print(json.dumps(model_feature_table.get_model_feature_dict("CHARM"), sort_keys=True, indent=4))
