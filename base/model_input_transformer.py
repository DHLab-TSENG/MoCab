import re
import operator
from pwn import safeeval
from base.model_feature_table import feature_table


def get_model_input(value, transfer) -> int or float or str or bool:
    if transfer['type'] == 'numeric':
        return value

    category = lambda val, transfer_list: getattr(operator, transfer_list['prefix'])(val, transfer_list['condition'])
    for transfer_dict in transfer['case']:
        for condition in transfer_dict['conditions']:
            if not category(value, condition):
                break
            return transfer_dict['category']

    raise ValueError('Value is not suitable in the configuration.')


def pack_list(model_data_dict, transform_style) -> list:
    list_temp = []
    for name, style in transform_style.items():
        # auto expand list length while inserted index is bigger than the list length
        if style["index"] is None:
            continue

        if style['index'] > len(list_temp):
            list_temp += [None] * (style['index'] - len(list_temp))
        list_temp[style['index'] - 1] = model_data_dict[name]
    if None in list_temp:
        raise IndexError("Index are not sequence. Check the configuration of transformation index.")
    return list_temp


def get_formulate_value(model_data_dict, param) -> int or float:
    # safeeval.values("weight/((height/100)**2)", {"weight": 70, 'height': 180})
    formula_feature_list = re.findall(r"\[\w*\]", param['formula'])
    feature_dict = {}
    rep = {"]": "", "[": ""}  # define desired replacements here

    # use these three lines to do the replacement
    rep = dict((re.escape(k), v) for k, v in rep.items())
    pattern = re.compile("|".join(rep.keys()))

    for feature in formula_feature_list:
        feature = pattern.sub(lambda m: rep[re.escape(m.group(0))], feature)
        feature_dict[feature] = model_data_dict[feature]

    formula = pattern.sub(lambda m: rep[re.escape(m.group(0))], param['formula'])
    result = safeeval.values(formula, feature_dict)

    return result


def transformer(patient_data_dict: dict, model: str) -> list:
    """
    This function takes the transformation of patient data into model input. The function requires patient data with
    dictionary and returns the list of the data.
    :param patient_data_dict: value of patient data from client or FHIR server
    :param model: name of model
    :return: list that are ready for prediction. Sort features by index.
    """
    transform_style = feature_table.get_model_feature_dict(model_name=model)
    # First, transfer patient numeric data to model require format
    # getattr(operator, 'eq')(2, 3)
    model_data_dict = dict()
    formula_idle_job = []
    for name in transform_style.keys():
        # First, ignore data that is not in the transformation.
        # The data not in the transformation means they are probably a feature of the formula
        if transform_style[name]['type'] == 'formula':
            formula_idle_job.append(name)
            continue

        if name not in patient_data_dict.keys():
            # What does this line do?
            # the action can be changed while MoCab supports features in formula do transfer.
            continue

        model_data_dict[name] = get_model_input(patient_data_dict[name]["value"], transform_style[name])

    for name in formula_idle_job:
        model_data_dict[name] = get_formulate_value(model_data_dict, transform_style[name])
    # At last, pack data into list.
    result_list = pack_list(model_data_dict, transform_style)

    return result_list

