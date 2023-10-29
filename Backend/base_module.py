import importlib
import os
import shutil

import pandas as pd

from mocab_models import *
from base.model_input_transformer import transformer
from base.object_store import feature_table
from base.object_store import model_feature_table

table = feature_table


def verify_data(patient_data_dict, api):
    # MUST HAVE: 1. Keys with each feature. 2. Value with Dict type and has Key with the name "value".
    try:
        validation_table = table.get_model_feature_dict(api)
    except KeyError:
        raise KeyError("{} Model is not in the table".format(api))

    for key in validation_table.keys():
        if key not in patient_data_dict.keys():
            raise KeyError("{} was not given".format(key))

        if "value" not in patient_data_dict[key].keys():
            raise KeyError("{}'s value has no 'value' key.".format(key))


def return_model_result(patient_data_dict, api):
    """
        Function return_model_result會對 model執行 predict的動作，回傳 model的結果
        2022-10-10 新增一個新的動作：在丟入Model之前，會先將資料根據ModelFeature Table轉譯成model prefer的category
        TODO: 把return_model_result獨立成一個新的檔案，需要解決的技術難點: globals()[api]
    """

    # transfer patient data into model preferred input
    patient_data_list = transformer(model_feature_table, patient_data_dict, api)
    return get_model_result(patient_data_list, api)


def get_model_result(patient_data_list, api, model_type="register"):
    base_path = f"./mocab_models/{api}"
    try:
        patient_data_list = encode_model_data_set(patient_data_list, api=api)
        model_results = globals()[api].predict(patient_data_list, base_path, model_type)
        return model_results
    except Exception as e:
        print(e)
        return None


def encode_model_data_set(x, y=None, api=None) -> pd.DataFrame or (pd.DataFrame, pd.DataFrame):
    base_path = f"./mocab_models/{api}"
    try:
        x, y = globals()[api].encode(x, y, base_path)
    except AttributeError:
        pass

    if y is None:
        return x

    return x, y


def train_model(x_train, y_train, api):
    base_path = f"./mocab_models/{api}"
    return globals()[api].train(x_train, y_train, base_path)


def get_machine_learning_model(model_type, api):
    base_path = f"./mocab_models/{api}"
    return globals()[api].get_model(model_type, base_path)


def choose_model(api, choosed_model):
    prev_model = "register_model"
    new_model = "new_model"
    base_path = f"./mocab_models/{api}/"
    if not os.path.exists(base_path + prev_model):
        raise FileNotFoundError("Registered Model not found")

    if not os.path.exists(base_path + new_model):
        raise FileNotFoundError("New Model not found")

    if choosed_model == "new":
        print("New Model is chosen.")
        if os.path.isfile(base_path + prev_model):
            os.remove(base_path + prev_model)
        elif os.path.isdir(base_path + prev_model):
            shutil.rmtree(base_path + prev_model)
        os.rename(base_path + new_model, base_path + prev_model)
    elif choosed_model == "register":
        print("Registered Model is chosen.")
        if os.path.isfile(base_path + new_model):
            os.remove(base_path + new_model)
        elif os.path.isdir(base_path + new_model):
            shutil.rmtree(base_path + new_model)


def import_model():
    # TODO: Need to figure out what actions does this function done, and optimize it.
    # get a handle on the module
    mdl = importlib.import_module('mocab_models')

    # is there an __all__?  if so respect it
    if "__all__" in mdl.__dict__:
        names = mdl.__dict__["__all__"]
    else:
        # otherwise we import all names that don't begin with _
        names = [x for x in mdl.__dict__ if not x.startswith("_")]

    # now drag them in
    globals().update({k: getattr(mdl, k) for k in names})


import_model()
