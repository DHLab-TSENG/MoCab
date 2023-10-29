import pytest

from base.object_store import feature_table
from base.patient_data_search import model_feature_search_with_patient_id


@pytest.mark.parametrize("patient_id, model_name, expected_output", [(
            "test-03121002",
            "pima_diabetes", {
                'glucose': {'date': '2019-11-12T00:00', 'value': 153},
                'diastolic_blood_pressure': {'date': '2019-12-12T00:00', 'value': 70},
                'insulin': {'date': '2019-11-20T00:00', 'value': 0.6},
                'weight': {'date': '2018-03-22T00:00', 'value': 69},
                'height': {'date': '2020-11-23T00:00', 'value': 176},
                'pregnancies': {'date': None, 'value': 6},
                'skinthickness': {'date': None, 'value': 35},
                'diabetespedigreefunction': {'date': None, 'value': 0.627},
                'hypertension': {'date': '2016-03-17T00:00', 'value': True},
                'age': {'date': '2023-05-18T00:00', 'value': 25}
            }
            ), (
            "test-03121002",
            "qCSI", {
                'respiratory_rate': {'date': '2020-09-21T00:00', 'value': 18},
                'spo2': {'date': '2020-12-15T00:00', 'value': 99.0},
                'o2_flow_rate': {'date': '2021-09-01T00:00', 'value': 3}
            }
        )]
     )
def test_model_feature_search_with_patient_id(patient_id, model_name, expected_output):
    features__table = feature_table
    patient__id = patient_id
    feature__table = features__table.get_model_feature_dict(model_name)

    assert model_feature_search_with_patient_id(patient__id, feature__table) == expected_output
