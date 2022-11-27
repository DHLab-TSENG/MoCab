import datetime

from base.search_sets import get_patient_resources
from base.search_sets import get_resource_datetime_and_value


def model_feature_search_with_patient_id(patient_id: str,
                                         table: dict,
                                         default_time: str = None,
                                         data_alive_time: str = None):
    if default_time is None:
        default_time = datetime.datetime.now()

    data = dict()
    for key in table:
        data[key] = dict()
        data[key] = get_patient_resources(patient_id, table[key], default_time, data_alive_time)

    result_dict = dict()
    for data_key in data:
        result_dict[data_key] = dict()
        # get_resource_datetime_and_value returns two values, date & value.
        # for other purpose, use other functions instead
        result_dict[data_key]['date'], result_dict[data_key]['value'] = get_resource_datetime_and_value(
            data[data_key], default_time)

    return result_dict


if __name__ == '__main__':
    import os

    os.chdir("../")

    from search_sets import get_patient_resources
    from search_sets import get_resource_datetime_and_value
    from feature_table import feature_table

    features__table = feature_table
    patient__id = "test-03121002"
    feature__table = features__table.get_model_feature_dict('diabetes')
    default_time = datetime.datetime.now()

    print(model_feature_search_with_patient_id(patient__id, feature__table, default_time))
