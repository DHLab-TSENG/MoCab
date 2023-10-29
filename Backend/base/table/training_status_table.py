"""
This module is used to create a table to store the training status of each model.
Be noticed that each model would only have one training status. That means if there are more than one training
record for a model, only the latest one would be recorded.
"""

import csv
from dataclasses import dataclass
from datetime import datetime
from base.lib import transform_to_correct_type, FilterOperation


@dataclass
class StatusObject:
    model: str = None
    last_training_time: datetime = None
    last_training_data_time: datetime = None
    numbers_of_patients: int = None
    old_model_evaluate: float = None
    new_model_evaluate: float = None
    register_model: str = None
    threshold: float = None


class _TrainingStatusTable:
    def __init__(self, table_position="./config/continuous_training/training_status.csv"):
        self.table_position = table_position
        self.table = self.__create_table(table_position)

    def __create_table(self, table_position) -> dict:
        return_dict = {}
        with open(table_position, newline='') as training_sets_table:
            rows = csv.DictReader(training_sets_table)

            for row in rows:
                row["last_training_time"] = transform_to_correct_type(
                    row["last_training_time"], "date")
                row["last_training_data_time"] = transform_to_correct_type(
                    row["last_training_data_time"], "date")
                new_statusobj = StatusObject(**row)
                if row["model"] not in return_dict:
                    return_dict[row["model"]] = new_statusobj

                if new_statusobj.last_training_time > return_dict[row["model"]].last_training_time:
                    # 如果新的資料比舊的還要新，則更新
                    return_dict[row["model"]] = new_statusobj

        return return_dict

    def get_status(self, model_name: str) -> StatusObject:
        return self.table[model_name]

    def get_last_training_data_filter_operation(self, model_name: str) -> FilterOperation:
        last_training_data_time = self.table[model_name].last_training_data_time
        return FilterOperation(type="date", prefix="gt", threshold=last_training_data_time)

    def update_data_in_csv(self):
        table_position = self.table_position
        return_dict = self.table
        with open(table_position, newline='') as training_status_table:
            rows = csv.DictReader(training_status_table)

            for row in rows:
                row["last_training_time"] = transform_to_correct_type(
                    row["last_training_time"], "date")
                row["last_training_data_time"] = transform_to_correct_type(
                    row["last_training_data_time"], "date")
                new_statusobj = StatusObject(**row)
                if row["model"] not in return_dict:
                    return_dict[row["model"]] = new_statusobj

                if new_statusobj.last_training_time > return_dict[row["model"]].last_training_time:
                    # 如果新的資料比舊的還要新，則更新
                    return_dict[row["model"]] = new_statusobj

    def write_new_data_into_csv(self, dict_data: dict):
        with open(self.table_position, 'a', newline='') as csvfile:
            fieldnames = [
                'model',
                'last_training_time',
                'last_training_data_time',
                "numbers_of_patients",
                'old_model_evaluate',
                'new_model_evaluate',
                'register_model',
                "threshold"
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writerow(dict_data)
            self.update_data_in_csv()
