import datetime
from base.search_sets import get_patient_resources_data_set
from base.search_sets import get_resource_datetime
from base.search_sets import get_resource_value
from base.search_sets import get_datetime_value_with_func


def model_feature_search_with_patient_id(patient_id: str,
                                         table: dict,
                                         default_time: str = None,
                                         data_alive_time: str = None) -> dict:
    """
    This function will return the result of model feature search with patient id. Different from smart search, this
    function will return the single result in dictionary type with the search_type defined in feature table.
    :param patient_id:
    :param table:
    :param default_time: Not yet implemented
    :param data_alive_time:
    :return: return date and value in dictionary type
    e.g.: {'date': "2020-12-13", 'value': 87}
    """
    result_dict = smart_model_feature_search_with_patient_id(patient_id, table, default_time, data_alive_time)

    for key in result_dict:
        """
        get_datetime_value_with_func will return date and value in dictionary type
        return e.g.: {'date': "2020-12-13", 'value': 87}
        """
        result_dict[key] = get_datetime_value_with_func(result_dict[key], table[key])

    return result_dict


def smart_model_feature_search_with_patient_id(patient_id: str,
                                               table: dict,
                                               default_time: str = None,
                                               data_alive_time: str = None) -> dict:
    if default_time is None:
        default_time = datetime.datetime.now()

    # First is to get all patient resources from FHIR server.
    data = dict()
    for key in table:
        # Key 即為features
        data[key] = dict()
        data[key] = get_patient_resources_data_set(patient_id, table[key], default_time, data_alive_time)

    # Next is to extract the data in data sets.
    result_dict = dict()
    for key in data:
        result_dict[key] = dict()
        result_dict[key] = extract_data_in_data_sets(data[key], table[key], default_time)

    # smart_model_feature_search_with_patient_id will return datetime and value in dictionary type
    # e.g.:{
    #       "diastolic blood pressure": {
    #          "date": ["2020-12-13", "2020-12-14", "2020-12-15"],
    #         "value": [87, 87, 87]
    #      },...
    #   }
    return result_dict


def extract_data_in_data_sets(data_sets, table, default_time=datetime.datetime.now()) -> dict:
    """
    This function will extract the data in data_sets and return a dictionary
    :param data_sets:
    :param default_time:
    :return: All features value and date in dictionary type
    e.g.:{
        "diastolic blood pressure": {
            "date": ["2020-12-13", "2020-12-14", "2020-12-15"],
            "value": [87, 87, 87]
        },...
    }
    """
    result_list = {"date": [], "value": []}
    origin_data = data_sets.copy()

    for sync_fhir_resource in data_sets['resource']:
        # TODO: 其實也可以改這個動作，畢竟真的很多餘，但有點怕大改
        origin_data['resource'] = sync_fhir_resource

        temp_date = get_resource_datetime(origin_data, table, default_time)
        temp_value = get_resource_value(origin_data, table)
        pass

        result_list['date'].append(temp_date)
        result_list['value'].append(temp_value)
    return result_list


if __name__ == '__main__':
    from base.object_store import feature_table

    # Note that this test should be processed with the Bulk Server
    features__table = feature_table
    patient__id = "07458CF801637945E1276A0B154C7718607BFD93"
    feature__table = features__table.get_model_feature_dict('SPC')

    print(model_feature_search_with_patient_id(patient__id, feature__table))
