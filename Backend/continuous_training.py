import threading
import time

import pandas as pd
import random
import string
from datetime import datetime
from config import configObject as conf
from collections import OrderedDict
from flask import Blueprint, jsonify
from requests import HTTPError, ConnectionError
from base_module import encode_model_data_set
from base_module import train_model
from base_module import get_machine_learning_model
from base_module import choose_model
from base.lib import transform_to_correct_type
from base.continuous_training_processor import \
    combine_training_and_predicting_feature_table, \
    separate_patients, \
    allocate_feature_resources, \
    extract_value_and_datetime, \
    resources_filter, \
    transform_data, \
    merge_transformed_data, \
    drop_unuseful_rows, \
    split_data, \
    imputation_stategy, \
    model_evaluation, \
    drop_trained_data
from base.object_store import \
    training_sets_table, \
    bulk_server, \
    feature_table, \
    training_feature_table, \
    model_feature_table, \
    training_model_feature_table, \
    training_status_table

ct_app = Blueprint('con_train', __name__)
lock = threading.Lock()
process_status = {}


class MyThread(threading.Thread):
    def __init__(self, func, args=()):
        super(MyThread, self).__init__()
        self.result = None
        self.func = func
        self.args = args

    def run(self):
        time.sleep(2)
        self.result = self.func(*self.args)

    def get_result(self):
        threading.Thread.join(self)
        try:
            return self.result
        except Exception:
            return None


def generate_callback_url(process_id):
    # Generate a random callback URL for the client
    base_url = conf.get("base_urls").get("BACKEND_URL")
    ct_prefix = conf.get("base_urls").get("continuous_training_prefix")
    if base_url[-1] == "/":
        base_url = base_url[:-1]
    return base_url + ct_prefix + '/process/' + process_id


@ct_app.route("/<api>", methods=['GET'])
def continuous_training_process(api):
    process_id = ''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=12))
    process = MyThread(training_process, args=(api,))
    process.start()

    process_status_msg = "In-Progress"
    # Update the training status table with process_id
    process_status[process_id] = process_status_msg
    # To ensure the order of the model in the process_status table are LIFO, we use OrderedDict.
    if api not in process_status:
        process_status[api] = OrderedDict()
    # Update the training status table with model_name->process_id
    process_status[api].update({process_id: process_status_msg})
    thread = threading.Thread(target=update_status, kwargs={'process_id': process_id,
                                                            'start_thread': process})
    thread.start()

    print(f"Continuous training process for {api} starts. "
          f"Progress url: {generate_callback_url(process_id)}")

    return jsonify({"message": "Training process is running in the background.",
                    "callback_url": generate_callback_url(process_id)
                    }), 202


def update_status(process_id, start_thread: MyThread):
    result = start_thread.get_result()
    if result is None:
        result = {"message": "Training process failed. Check the log for more details."}
    else:
        model_name = result.get("model")

    """
        What I thought is that we can use the process_id as the key to update the training status table.
        And the reason why I stored the result by process_id and model_name->process_id is for the performance.
        
        If we only use model_name->process_id as the key, we need to traverse each model_name to find the
        corresponding process_id. But if we use process_id as the key, we can directly find the corresponding.
    """
    # Update the training status table with process_id
    process_status[process_id] = result

    # Update the training status table with model_name
    process_status[model_name][process_id] = result


@ct_app.route("/process/<process_id>", methods=['GET'])
def check_status(process_id):
    if process_id in process_status:
        if process_status[process_id] == "In-Progress":
            return jsonify(process_status[process_id]), 202
        return jsonify(process_status[process_id]), 200
    else:
        return jsonify({"message": "No such process."}), 404


def training_process(model_name):
    # Lock the thread
    lock.acquire(timeout=1200)

    # Get the training set from the training_sets_table
    training_sets = training_sets_table.get_training_set(model_name)

    # Add exception for error 404
    # And retry the provision process for 3 times if any other error occurs
    bulk_error_times = 0
    try:
        bulk_server.content = "http://ming-desktop.ddns.net:8193/fhir/$export-poll-status?_jobId=99b638cb-4803-457d-aeb5-76924c7c267f"
        bulk_server.provision()
    except HTTPError:
        print("Connection error. Trying to generate a new bulk request")
        bulk_server.content = None
        bulk_server.provision()
        print(bulk_server.content)

    # Get the data from the bulk server
    try:
        ndj = bulk_server.iter_ndjson_dict()
    except ConnectionError:
        # Sometimes the connection will be refused, so we need to try again
        print("Encounters an error, trying to reconnect.")
        try:
            ndj = bulk_server.iter_ndjson_dict()
        except ConnectionError:
            # If the connection is still refused, we will try to generate a new bulk request
            print("Connection error. Trying to generate a new bulk request")
            bulk_server.content = None
            bulk_server.provision()
            print(bulk_server.content)
            ndj = bulk_server.iter_ndjson_dict()

    """
    Differences between code_dict and predict_and_training_feature_tables is:
    code_dict combines the training and predicting feature tables with Resource type. It takes the resource type as the
    key. While predict_and_training_feature_tables combines the training and predicting feature tables with feature.
    It takes the feature as the key, and is more useful in the later process.
    """
    code_dict = combine_training_and_predicting_feature_table(model_name)
    data_with_separated_patient = separate_patients(ndj)
    data_with_separated_patient = allocate_feature_resources(
        data_with_separated_patient, code_dict)

    # Extract the value and datetime from the resources.
    predict_feature_table = feature_table.get_model_feature_dict(model_name)
    train_feature_table = training_feature_table.get_model_feature_dict(model_name)
    predict_and_train_feature_tables = predict_feature_table | train_feature_table
    value_and_datetime_of_patients = extract_value_and_datetime(
        data_with_separated_patient, predict_and_train_feature_tables)

    # Drop the resources that are not needed.
    x_value_and_datetime_of_patients_after_filter, y_value_and_datetime_of_patients_after_filter = resources_filter(
        value_and_datetime_of_patients,
        predict_feature_table,
        train_feature_table,
        training_sets.data_filter
    )

    # translate the value from the value_and_datetime_of_patients_after_filter
    transformed_x_data_of_patients = transform_data(model_feature_table,
                                                    x_value_and_datetime_of_patients_after_filter,
                                                    model_name)
    transformed_y_data_of_patients = transform_data(training_model_feature_table,
                                                    y_value_and_datetime_of_patients_after_filter,
                                                    model_name, y_data=True)



    transformed_training_data = merge_transformed_data(transformed_x_data_of_patients,
                                                       transformed_y_data_of_patients)

    # Drop the rows that have been trained before. By checking the time of the y data.
    transformed_training_data, max_training_data_time = drop_trained_data(transformed_training_data,
                                                                          training_status_table.get_last_training_data_filter_operation(
                                                                              model_name))

    # Time for some dataframe works
    column = model_feature_table.get_model_feature_column(model_name) \
             + training_model_feature_table.get_model_feature_column(model_name)
    df = pd.DataFrame.from_dict(transformed_training_data, orient="index")
    numbers_of_patients = len(df.index)

    # Check if the dataframe is empty
    if numbers_of_patients == 0:
        return_dict = {
            "model": model_name,
            "last_training_time": str(datetime.now()),
            "last_training_data_time": str(transform_to_correct_type(training_status_table.get_last_training_data_filter_operation(
                model_name).threshold, "date")),
            "numbers_of_patients": numbers_of_patients,
            "old_model_evaluate": 0,
            "new_model_evaluate": 0,
            "register_model": "register",
            "threshold": 0
        }
        training_status_table.write_new_data_into_csv(return_dict)
        lock.release()
        return return_dict

    # Columns would be added after checking the dataframe is not empty
    df.columns = column

    # First is to drop the rows that matches the condition we've set in the training_sets_table.
    df = drop_unuseful_rows(df, training_sets.null_value_strategy["drop"])

    # Then split the data into X,Y training set and X,Y testing set.
    x_training_df, x_testing_df, y_train_df, y_test_df \
        = split_data(df,
                     training_sets.training_config,
                     training_model_feature_table.get_model_feature_column(model_name))
    x_train_imp, x_test_imp = imputation_stategy(x_training_df, training_sets.null_value_strategy.copy()), \
        imputation_stategy(
            x_testing_df, training_sets.null_value_strategy.copy())

    # Encode the data

    x_train_encoded, y_train_encoded = encode_model_data_set(
        x_train_imp, y_train_df, model_name)
    x_test_encoded, y_test_encoded = encode_model_data_set(
        x_test_imp, y_test_df, model_name)

    # Train the model
    train_model(x_train_encoded, y_train_encoded, model_name)

    # Evaluate the model
    register_model = get_machine_learning_model("register", model_name)
    new_model = get_machine_learning_model("new", model_name)
    evaluate = model_evaluation(
        register_model, new_model, x_test_encoded, y_test_encoded)

    # Save the model
    validate_method = training_sets.training_config["validate_method"]
    evaluate_result = {
        "register_model": evaluate[validate_method]['register_model']["score"],
        "new_model": evaluate[validate_method]['new_model']["score"],
    }
    threshold = {
        "register": evaluate[validate_method]['register_model']["best_threshold"],
        "new": evaluate[validate_method]['new_model']["best_threshold"],
    }

    if evaluate_result['register_model'] > evaluate_result['new_model']:
        chosed_model = "register"
    else:
        chosed_model = "new"
    choose_model(model_name, chosed_model)

    if chosed_model == "new":
        last_training_time = max_training_data_time
    else:
        last_training_time = transform_to_correct_type(training_status_table.get_last_training_data_filter_operation(
            model_name).threshold, "date")

    return_dict = {
        "model": model_name,
        "last_training_time": str(datetime.now()),
        "last_training_data_time": str(last_training_time),
        "numbers_of_patients": numbers_of_patients,
        "old_model_evaluate": evaluate_result['register_model'],
        "new_model_evaluate": evaluate_result['new_model'],
        "register_model": chosed_model,
        "threshold": threshold[f'{chosed_model}']
    }

    training_status_table.write_new_data_into_csv(return_dict)

    # Release the lock
    lock.release()

    return_dict["evaluate"] = evaluate

    return return_dict


if __name__ == "__main__":
    print("starting...")
    print(training_process("SPC"))
    print("ending...")
    pass
