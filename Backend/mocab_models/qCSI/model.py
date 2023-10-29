from mocab_models.qCSI import mask
from typing import Dict
from mocab_models.qCSI.mask import unit_type
from mocab_models.qCSI.mask import mask_type


def predict(data: list, base_path, model_type="register") -> int:
    """
    patient_data_dict is a dictionary that contains respiratory rate, o2 flow rate and spo2.
    The value of the keys are in dictionary type too, they are all in the same structure with date and value key-value.
    Date sometimes would be optional but the value must be required.

    The o2 flow rate key has two kinds of value, number of string.
    If the value of o2 flow rate is number, then it can be used without any further instructions.
    But if the value of o2 flow rate is string, it should be converted to the number by
    the method: mask_mart.treatment_mining(your_text_here), the method would return the number of the string.

    The goal of this function is to calculate the qCSI value with patient data that was given in patient_data_dict,
    and return the qCSI score.
    """
    if all(isinstance(n, int) for n in data):
        return sum(data)

    flow_rate_value = data[2]
    if type(flow_rate_value) == str:
        treatment_mining_result = \
            mask.mask_mart.treatment_mining(flow_rate_value)
        if treatment_mining_result is not None:
            # TODO: Convert FiO2 to Flow rate
            if treatment_mining_result['unit_type'] != unit_type[0]:
                data[2] = unit_conversion(treatment_mining_result)
            else:
                data[2] = treatment_mining_result['value']
        else:
            raise ValueError("The O2 flow rate string: \"{}\" cannot be identified \
            , please fill in the flow rate manually"
                             .format(flow_rate_value))
    # Convert the value into qCSI score format and calculate the score.
    return sum(data)


def unit_conversion(treatment_mining_result: Dict) -> int or float:
    """
    treatment_mining_result: Dict, {'mask_name': , 'mask_type', 'value'}
    unit_type = ("o2_flow_rate", "fio2")
    mask_type = ("Simple Mask", "Nasal Cannula", "Non-rebreathing Mask", "Tracheal Mask", "V-Mask", "High Flow Mask")
    """
    converted_value = 0
    fio2_value = int(treatment_mining_result['value'])
    # TODO: 補齊轉換的單位數值
    if treatment_mining_result['mask_name'] == mask_type[0]:
        converted_value = (fio2_value - 5) / 5
    elif treatment_mining_result['mask_name'] == mask_type[1]:
        converted_value = (fio2_value - 20) / 4
    elif treatment_mining_result['mask_name'] == mask_type[2]:
        converted_value = 15
    elif treatment_mining_result['mask_name'] == mask_type[3]:
        converted_value = (fio2_value - 21) / 3
    else:
        raise KeyError("Mask Name Undefined, check mask.mask_type sets for more info.")
    return round(converted_value)

