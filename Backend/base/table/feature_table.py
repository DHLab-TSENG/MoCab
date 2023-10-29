import csv
from base.lib import transform_to_correct_type, TimeObject


class _FeatureTable:
    def __init__(self, feature_table_position="./config/features.csv"):
        # TODO: 可以改成Object，以方便後續讀取資料
        self.table = self.__create_table(feature_table_position)

    @classmethod
    def __create_table(cls, feature_table_position):
        table = {}
        special_field_sets = ('model', "feature", "code", "code_system", "data_alive_time", "default_value"
                              , "value_route", "datetime_route")
        with open(feature_table_position, newline='') as feature_table_file:
            rows = csv.DictReader(feature_table_file)
            for row in rows:
                # 新建以model name 為key 的Dictionary value
                if row['model'] not in table:
                    table[row['model']] = {}
                # 在model name 的Dictionary 裡新建一個以feature name 為key 的Dictionary value
                if row['feature'] not in table[row['model']]:
                    table[row['model']][row['feature']] = {}

                temp_table = table[row['model']][row['feature']]

                # 處理code 的變數內容，如果有code system 就再新增進去
                code = row['code']
                if row['code_system'] != '':
                    code = "{}|{}".format(row['code_system'], row['code'])

                # 如果code 變數內沒內容
                if code == '' and row["type_of_data"] != "patient":
                    raise FeatureCodeIsEmpty(row['feature'])

                # Feature 有兩種以上的code
                if 'code' in temp_table:
                    temp_table['code'] = temp_table['code'] + ",{}".format(code)
                else:
                    temp_table['code'] = code

                # 取得距今多久以內的資料
                temp_table['data_alive_time'] = TimeObject(row['data_alive_time']) if row['data_alive_time'] != '' \
                    else None

                temp_table['default_value'] = None if row['default_value'] == '' \
                    else transform_to_correct_type(row['default_value'])

                # 選擇Value and Datetime
                temp_table['value_route'] = row['value_route'].split('&') if row['value_route'] != '' else None
                temp_table['datetime_route'] = row['datetime_route'].split('&') if row['datetime_route'] != '' else None

                # 剩餘的key value就用迴圈建立，因為沒什麼特別的了
                for key, value in row.items():
                    if key not in special_field_sets:
                        temp_table[key] = value

            return table

    def get_model_feature_dict(self, model_name):
        if model_name not in self.table:
            raise KeyError(f"Model '{model_name}' is not exist in the feature table.")

        return self.table[model_name]

    def get_exist_model_name(self) -> list:
        return [i for i in self.table.keys()]


if __name__ == '__main__':
    from exceptions import FeatureCodeIsEmpty

    test_table = _FeatureTable("../config/features.csv")
    print(test_table)
    pass
