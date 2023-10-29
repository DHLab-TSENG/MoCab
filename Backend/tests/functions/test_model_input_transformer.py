import pytest
from base.model_input_transformer import transformer
from base.object_store import model_feature_table

test_list = [(
    {
        "sea": {
            "date": "2016-12-24T00:00:00",
            "value": True
        },
        "wbc": {
            "date": "2016-12-24T00:00:00",
            "value": 4400
        },
        "crp": {
            "date": "2016-12-24T00:00:00",
            "value": 0.5
        },
        "seg": {
            "date": "2016-12-24T00:00:00",
            "value": 50.7
        },
        "band": {
            "date": "2016-12-24T00:00:00",
            "value": 0
        }
    }, 'NSTI', [1, 4400, 0.5, 50.7, 0]), (
    {
        "respiratory_rate": {
            "date": "2022-01-19T11:53",
            "value": 25
        },
        "o2_flow_rate": {
            "date": "2022-01-19T11:53",
            "value": 3
        },
        "fio2": "",
        "spo2": {
            "date": "2022-01-19T11:53",
            "value": 90
        }
    }, "qCSI", [1, 2, 4]), (
    {
        "respiratory_rate": {
            "date": "2022-01-19T11:53",
            "value": 25
        },
        "o2_flow_rate": {
            "date": "2022-01-19T11:53",
            "value": "oxygen therapy-nonrebreathing mask 100%"
        },
        "fio2": "",
        "spo2": {
            "date": "2022-01-19T11:53",
            "value": 90
        }
    }, "qCSI", [1, 2, "oxygen therapy-nonrebreathing mask 100%"]), (
    {
        "age": {
            "date": "2022-11-27",
            "value": 25
        },
        "diabetespedigreefunction": {
            "date": None,
            "value": 0.627
        },
        "diastolic_blood_pressure": {
            "date": "2019-12-12T00:00",
            "value": 70
        },
        "glucose": {
            "date": "2019-11-12T00:00",
            "value": 153
        },
        "height": {
            "date": "2020-11-23T00:00",
            "value": 176
        },
        "insulin": {
            "date": "2019-11-20T00:00",
            "value": 0.6
        },
        "predict_value": 0.08948717441012251,
        "pregnancies": {
            "date": None,
            "value": 6
        },
        "skinthickness": {
            "date": None,
            "value": 35
        },
        "weight": {
            "date": "2018-03-22T00:00",
            "value": 69
        }
    }, 'pima_diabetes', [6, 153, 70, 35, 0.6, 22.275309917355372, 0.627, 25]), (
    {
        "age": {
            "date": "2022-11-27",
            "value": 25
        },
        "diabetespedigreefunction": {
            "date": None,
            "value": 0.627
        },
        "diastolic_blood_pressure": {
            "date": None,
            "value": None
        },
        "glucose": {
            "date": "2019-11-12T00:00",
            "value": 153
        },
        "height": {
            "date": "2020-11-23T00:00",
            "value": 176
        },
        "insulin": {
            "date": "2019-11-20T00:00",
            "value": 0.6
        },
        "predict_value": 0.08948717441012251,
        "pregnancies": {
            "date": None,
            "value": 6
        },
        "skinthickness": {
            "date": None,
            "value": 35
        },
        "weight": {
            "date": "2018-03-22T00:00",
            "value": 69
        }
    }, 'pima_diabetes', [6, 153, None, 35, 0.6, 22.275309917355372, 0.627, 25])]


@pytest.mark.parametrize("test_input, test_model, expected", test_list)
def test_transformer(test_input, test_model, expected):
    assert transformer(model_feature_table, test_input, test_model) == expected
