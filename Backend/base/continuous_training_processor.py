import numpy as np
import pandas as pd
import copy
from datetime import date, datetime

from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, roc_curve
from sklearn.model_selection import train_test_split
import tensorflow as tf

from base.exceptions import ThresholdNoneError
from base.exceptions import VariableNoneError
from base.object_store import feature_table
from base.object_store import training_feature_table
from base.route_converter import get_by_path
from base.patient_data_search import extract_data_in_data_sets
from base.search_sets import get_datetime_value_with_func
from base.model_input_transformer import transformer
from base.lib import transform_to_correct_type
from base_module import get_model_result


# First, we need to check what features are those resources belong to.
def separate_patients(resource: dict) -> dict:
    """
    While retrieving the data from the bulk server, we need to separate the data by patient.
    :param resource: dictionary. Keys are the resource type, and values are the list of resources.
    :return: dictionary. Keys are the patient id, and values are the list of resources.
    """
    return_data = {}
    for resources in resource["Patient"]:
        return_data[resources["id"]] = [resources]

    for resource_type, resources in resource.items():
        if resource_type == "Patient":
            continue
        for resource in resources:
            try:
                if resource["subject"]["id"] in return_data:
                    return_data[resource["subject"]["id"]].append(resource)
            except KeyError:
                continue

    return return_data


def allocate_feature_resources(resources, code_dict) -> dict:
    """
    Allocate the resources by the feature table configurations.

    :return:
    """
    return_data = {}

    # Iterate all the patients.
    for patient_id, resources in resources.items():
        patient_separated_data = {}
        for resource in resources:
            try:
                codes = code_dict[resource["resourceType"]]
            except KeyError:
                continue

            for feature_name, code_list in codes.items():
                if feature_name not in patient_separated_data:
                    patient_separated_data[feature_name] = []

                if resource["resourceType"] == "Patient":
                    patient_separated_data[feature_name].append(resource)
                    continue

                for code in code_list:
                    if get_by_path(resource, code) is not None:
                        patient_separated_data[feature_name].append(resource)
                        break

        for patient_separated_data_key, patient_separated_data_value in patient_separated_data.items():
            if len(patient_separated_data_value) == 0:
                # 當無資料時，補個None
                patient_separated_data[patient_separated_data_key].append(None)

        return_data[patient_id] = patient_separated_data

    return return_data


def combine_training_and_predicting_feature_table(model_name: str):
    """
    Combine the training and predicting feature table.
    :param training_feature_table:
    :param feature_table:
    :return:
    """
    # Combine the feature table of training and predicting.
    training_feature_code_dict = get_feature_code_dict(
        training_feature_table, model_name)
    feature_code_dict = get_feature_code_dict(feature_table, model_name)
    code_dict = {}
    for key in set(list(feature_code_dict.keys()) + list(training_feature_code_dict.keys())):
        code_dict[key] = feature_code_dict.get(key, {})
        code_dict[key].update(training_feature_code_dict.get(key, {}))

    return code_dict


def get_feature_code_dict(table, model_name) -> dict:
    """
    Get the feature code dictionary for the model.
    :param model_name:
    :return: {resource_type: {features: [{"code": str, "system": str or None}]}}
    """
    feature_code_dict = {}

    for feature_name, feature_dict in table.get_model_feature_dict(model_name).items():
        # For the features, we need to store the code for each feature.
        # {"Observation": {"Glucose": [route of codes...]} ... }
        resource_type = feature_dict["type_of_data"].capitalize()
        if resource_type not in feature_code_dict:
            feature_code_dict[resource_type] = {}

        temp_code_system_list = []
        for code_system in feature_dict["code"].split(","):
            temp_code_system_dict = {}

            if "|" in code_system:
                feature_system, feature_code = code_system.split("|")
                temp_code_system_dict["code"] = feature_code
                temp_code_system_dict["system"] = feature_system
            else:
                temp_code_system_dict["code"] = code_system

            temp_code_system_list.append(
                ["code", "coding", temp_code_system_dict])

        feature_code_dict[resource_type][feature_name] = temp_code_system_list

    return feature_code_dict


def extract_value_and_datetime(resources: dict, table) -> dict:
    """
    Extract the value and datetime from the resources.

    :param resources: dictionary. Keys are the patient id, and values are the list of resources.
    :return: dictionary. Keys are the patient id, and values are the list of resources.
    """
    return_data = {}
    for patient_id, resources in resources.items():
        patient_separated_data = {}
        for feature_name, resources in resources.items():
            temp_data = {"resource": resources,
                         "type": table[feature_name]["type_of_data"]}
            patient_separated_data[feature_name] = extract_data_in_data_sets(
                temp_data, table[feature_name])

        return_data[patient_id] = patient_separated_data

    return return_data


def filter_data_in_data_sets(data_sets: dict, filter_list):
    """
    Filter the data in the data sets.
    :param data_sets: dict, {"datetime": [], "value": []}
    :param filter_list:
    :return:
    """

    return_dict = {}
    # Prepare the thresholds

    # First, convert data_sets from dictionary to list to make it easier to filter.
    # Expected: [({date1}, {value1}), ...]

    data_sets_list = list(zip(data_sets["date"], data_sets["value"]))

    # Some exceptions for Patient data. Still need some clever way for Patient data exceptions.
    if len(data_sets_list) == 1:
        try:
            if datetime.fromisoformat(data_sets_list[0][0]) == datetime.fromordinal(date.today().toordinal()):
                return_dict["date"], return_dict["value"] = zip(
                    *data_sets_list)
                return_dict["date"] = list(return_dict["date"])
                return_dict["value"] = list(return_dict["value"])
                return return_dict
        except TypeError:
            pass

    # Iterate the filter list.
    return_dict["date"] = []
    return_dict["value"] = []
    for date_value_set in data_sets_list:
        filter_list_validate = []
        for obj in filter_list:
            if obj.type == "date":
                validated_data = transform_to_correct_type(
                    date_value_set[0], "date")
            elif obj.type == "value":
                validated_data = transform_to_correct_type(date_value_set[1])
            else:
                raise ValueError("The type of filter is not supported.")

            try:
                validate = obj.validate(validated_data)
            except ThresholdNoneError:
                validate = True
            except VariableNoneError:
                validate = False
            filter_list_validate.append(validate)
            if not validate:
                break

        if all(filter_list_validate):
            return_dict["date"].append(date_value_set[0])
            return_dict["value"].append(date_value_set[1])

    return return_dict


def extract_value(value_and_datetime_of_patients_after_filter) -> dict:
    return_data = {}
    for patient_id, value_and_datetime_of_patient in value_and_datetime_of_patients_after_filter.items():
        feature_value = {}
        for feature_name, value_and_datetime_of_feature in value_and_datetime_of_patient.items():
            feature_value[feature_name] = value_and_datetime_of_feature["value"] if value_and_datetime_of_feature[
                "value"] else np.nan
        return_data[patient_id] = feature_value

    return return_data


def resources_filter(value_and_datetime_of_patients,
                     predict_feature_table,
                     training_feature_table,
                     filter_list) -> (dict, dict):
    """
    Filter the resources by the filter list.
    :param value_and_datetime_of_patients:
    :param predict_feature_table:
    :param training_feature_table:
    :param filter_list:
    :return:
    """
    return_x_data = {}
    return_y_data = {}
    for patient_id, value_and_datetime_of_patient in value_and_datetime_of_patients.items():
        temp_filter_list = copy.deepcopy(filter_list)
        patient_separated_data = {}
        # First is to get the datetime and value of the filtered features
        # filtered_features =
        value_and_datetime_for_threshold_feature = {}
        for obj in temp_filter_list:
            threshold = str(obj.threshold)
            if threshold.startswith("[") and threshold.endswith("]"):
                # keep the value inside []
                threshold = threshold[1:-1]
                # get the datetime and value with search_type strategy defined in feature table
                # store the rest data
                value_and_datetime_threshold = value_and_datetime_of_patient.pop(
                    threshold)
                value_and_datetime_for_threshold_feature[threshold] = value_and_datetime_threshold
                # get the value and datetime with the strategy defined in feature table
                threshold = get_datetime_value_with_func(
                    value_and_datetime_threshold, training_feature_table[threshold])
                threshold = threshold[obj.type]

                # update the threshold to the object
                obj.threshold = threshold

        # Exclude the y data features that are not in the filter list
        for feature_name in training_feature_table.keys():
            if feature_name in value_and_datetime_of_patient.keys():
                value_and_datetime_for_threshold_feature[feature_name] = \
                    value_and_datetime_of_patient.pop(feature_name)

        for feature_name, value_and_datetime_of_features in value_and_datetime_of_patient.items():
            patient_separated_data[feature_name] = \
                filter_data_in_data_sets(
                    value_and_datetime_of_features, temp_filter_list)

        return_x_data[patient_id] = patient_separated_data
        return_y_data[patient_id] = value_and_datetime_for_threshold_feature

    # get the value and datetime with the strategy (latest, max, min, etc) defined in feature table
    for patient_id, value_and_datetime_of_patient in return_x_data.items():
        for feature_name, value_and_datetime_of_features in value_and_datetime_of_patient.items():
            return_x_data[patient_id][feature_name] = \
                get_datetime_value_with_func(
                    value_and_datetime_of_features, predict_feature_table[feature_name])

    for patient_id, value_and_datetime_of_patient in return_y_data.items():
        for feature_name, value_and_datetime_of_features in value_and_datetime_of_patient.items():
            return_y_data[patient_id][feature_name] = \
                get_datetime_value_with_func(
                    value_and_datetime_of_features, training_feature_table[feature_name])

    return return_x_data, return_y_data


def imputation_stategy(df: pd.DataFrame, null_value_strategy: dict) -> pd.DataFrame:
    """
    Fill the null value in the dataframe with the strategy defined in the null_value_strategy.
    :param df:
    :param null_value_strategy:
    :return:
    """
    return_df = df.copy()
    # Fill the null value with the strategy defined in the null_value_strategy
    del null_value_strategy["drop"]

    # Pop the default strategy, and be ready to fill the rest columns based on the config of the strategy.
    default_strategy = null_value_strategy.pop("default")
    for feature_name, strategy in null_value_strategy.items():
        if strategy == "mean":
            return_df[feature_name].fillna(
                return_df[feature_name].mean(), inplace=True, downcast="infer")
        elif strategy == "median":
            return_df[feature_name].fillna(
                return_df[feature_name].median(), inplace=True, downcast="infer")
        elif strategy == "mode":
            return_df[feature_name].fillna(return_df[feature_name].mode()[
                                               0], inplace=True, downcast="infer")
        elif type(transform_to_correct_type(strategy)) in [int, float]:
            return_df[feature_name].fillna(transform_to_correct_type(
                default_strategy), inplace=True, downcast="infer")
        else:
            raise ValueError(
                "The type of null value strategy is not supported.")

    # Fill the rest columns with the default strategy
    if default_strategy == "mean":
        return_df.fillna(return_df.mean(), inplace=True, downcast="infer")
    elif default_strategy == "median":
        return_df.fillna(return_df.median(), inplace=True, downcast="infer")
    elif default_strategy == "mode":
        for feature_name in return_df.columns:
            return_df[feature_name].fillna(return_df[feature_name].mode()[
                                               0], inplace=True, downcast="infer")
    elif type(transform_to_correct_type(default_strategy)) in [int, float]:
        return_df.fillna(transform_to_correct_type(
            default_strategy), inplace=True, downcast="infer")
    else:
        raise ValueError("The type of null value strategy is not supported.")

    return return_df


def transform_data(
        model_feature_table,
        value_and_datetime_of_patients_after_filter,
        model_name,
        y_data=False
) -> dict:
    """
    Transform the data to the format that can be used in the model.
    :param model_feature_table:
    :param value_and_datetime_of_patients_after_filter:
    :param model_name:
    :return:
    """
    return_dict = {}

    for patient_id, value_and_datetime_of_patient in value_and_datetime_of_patients_after_filter.items():
        if y_data:
            # 如果是y data, 需要將resource date 強制抓出，以為了後續剔除上次訓練過的資料
            y_datatime = None
            for feature_name, value_and_datetime_of_features in value_and_datetime_of_patient.items():
                if value_and_datetime_of_features["date"] is None or \
                        type(value_and_datetime_of_features["date"]) == list:
                    # List means the y data is in getAll Strategy.
                    continue
                if y_datatime is None:
                    y_datatime = transform_to_correct_type(
                        value_and_datetime_of_features["date"], "date")
                else:
                    y_datatime = max(y_datatime, transform_to_correct_type(
                        value_and_datetime_of_features["date"], "date"))

        transformed_data_list = transformer(
            model_feature_table, value_and_datetime_of_patient, model_name)
        if y_data:
            transformed_data_list.append(y_datatime)
        return_dict[patient_id] = transformed_data_list

    return return_dict


def merge_transformed_data(x_data_dict, y_data_dict) -> dict:
    """
    Merge the transformed data to the format that can be used in the model.
    :param args:
    :return:
    """
    return_dict = x_data_dict
    for patient_id, y_data in y_data_dict.items():
        if all([y is None for y in y_data]):
            del return_dict[patient_id]
        else:
            return_dict[patient_id] = return_dict[patient_id] + y_data

    return return_dict


def split_data(df, training_config, y_columns: list) -> (pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame):
    """
    Split the data into training set and testing set.
    :param df:
    :param training_config:
    :param y_columns:
    :return:
    """
    # Split the data into training set and testing set
    if len(y_columns) > 1:
        raise ValueError(
            "The number of y columns is more than 1, which is not supported now.")
    y_col = y_columns[0]
    size = float(training_config['test_size'])
    seed = 87

    train = pd.DataFrame()
    test = pd.DataFrame()
    trainset, testset = train_test_split(df, test_size=size, stratify=df[y_col],
                                         random_state=seed)
    train = pd.concat([train, trainset])
    x_train, y_train = train.drop(y_col, axis=1), train[y_col]
    test = pd.concat([test, testset])
    x_test, y_test = test.drop(y_col, axis=1), test[y_col]

    return x_train, x_test, y_train, y_test


def drop_unuseful_rows(df, null_value_strategy):
    # Drop the rows with too many null values
    return_df = df
    drop_prefix = null_value_strategy["prefix"]
    drop_threshold = int(null_value_strategy["threshold"])
    if drop_prefix == "ge":
        return_df = return_df[return_df.isnull().sum(axis=1) < drop_threshold]
    elif drop_prefix == "gt":
        return_df = return_df[return_df.isnull().sum(axis=1) <= drop_threshold]
    else:
        raise ValueError("The prefix of drop is not supported.")

    return return_df


def model_evaluation(register_model, new_model, x_test, y_test) -> dict:
    """
    Evaluate the performance of the model.
    :param register_model:
    :param new_model:
    :param x_test:
    :param y_test:
    :return: {
        "accuracy": {
            "register_model": {
                "score": 0.9,
                "best_threshold": 0.5
            },
            "new_model": {
                "score": 0.8,
                "best_threshold": 0.7
            },
        },...
    }

    """
    return_dict = {}

    # Determine the included function of the model
    if "predict_proba" in dir(register_model):
        y_prev_pred = register_model.predict_proba(x_test)[:, 1]
    elif "predict" in dir(register_model):
        y_prev_pred = register_model.predict(x_test)

    if "predict_proba" in dir(new_model):
        y_new_pred = new_model.predict_proba(x_test)[:, 1]
    elif "predict" in dir(new_model):
        y_new_pred = new_model.predict(x_test)

    reg_validate_result = evaluating(y_prev_pred, y_test)
    new_validate_result = evaluating(y_new_pred, y_test)

    for key in reg_validate_result.keys():
        return_dict[key] = {
            "register_model": reg_validate_result[key],
            "new_model": new_validate_result[key]
        }

    return return_dict


def evaluating(y_perd, y_actual):
    """
    Evaluate the performance of the model.
    :param y_perd: predicted result
    :param y_actual: answer
    :return:
     {
        "auroc": {"score": , "best_threshold": }
     }
    """
    return_dict = {'auroc': calculate_best_threshold(y_perd, y_actual, "auroc"),
                   'accuracy': calculate_best_threshold(y_perd, y_actual, "accuracy"),
                   'precision': calculate_best_threshold(y_perd, y_actual, "precision"),
                   'recall': calculate_best_threshold(y_perd, y_actual, "recall"),
                   'f1_score': calculate_best_threshold(y_perd, y_actual, "f1_score")}

    return return_dict


def calculate_best_threshold(y_pred, y_actual, method="auroc"):
    return_dict = {}
    if method == "auroc":
        # Calculate the auroc
        score = roc_auc_score(y_actual, y_pred)
        # Find the best threshold
        fpr, tpr, thresholds = roc_curve(y_actual, y_pred)
        # Calculate the best threshold
        best_threshold = thresholds[np.argmax(tpr - fpr)]
    else:
        thresholds = np.linspace(0, 1, 100)  # Define a range of threshold values
        best_threshold = None
        score = -1

        for threshold in thresholds:
            y_result = (y_pred >= threshold).astype(int)  # Convert probabilities to binary predictions
            if method == "f1_score":
                temp_score = f1_score(y_actual, y_result)
            elif method == "precision":
                temp_score = precision_score(y_actual, y_result)
            elif method == "recall":
                temp_score = recall_score(y_actual, y_result)
            elif method == "accuracy":
                temp_score = accuracy_score(y_actual, y_result)
            else:
                raise ValueError("The method is not supported.")

            if temp_score > score:
                score = temp_score
                best_threshold = threshold

    return_dict['best_threshold'] = float(best_threshold)
    return_dict['score'] = round(float(score), 3)
    return return_dict


def drop_trained_data(value_of_data_of_patient, last_trained_filter_operation):
    """
    Drop the data that has been trained, and returns the maximum datetime of the training data.

    """
    return_dict = {}
    max_datetime = None
    for patient_id, value_list in value_of_data_of_patient.items():
        row_datetime = value_list[-1]

        if max_datetime is None:
            max_datetime = row_datetime
        else:
            max_datetime = max(max_datetime, row_datetime)

        if last_trained_filter_operation.validate(row_datetime) is True:
            return_dict[patient_id] = value_list[:-1]

    return return_dict, max_datetime
