from base.lib import transform_to_correct_type


def transformer(model_feature_table, data: dict, model_name):
    real_dict = model_feature_table.get_model_feature_dict(model_name)
    for k, v in data.items():
        try:
            real_dict["observer"].update_value(k, v["value"])
        except TypeError:
            continue

    return_list = []

    for element in real_dict["index"]:
        has_value = False
        for variable in element:
            try:
                if variable.get_value() is not None:
                    value = variable.get_value()
                    value = transform_to_correct_type(value)
                    return_list.append(value)
                    has_value = True
                    break
            except TypeError:
                continue
        # 所有Variable
        if not has_value:
            return_list.append(None)
            # TODO: add maybe an Nonetype of Nan to the list if there's no value in the variable

    return return_list
