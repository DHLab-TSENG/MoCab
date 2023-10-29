import pytest
from base.route_converter import get_by_path
from base.route_converter import parse_route

get_by_path_data = [
    ({"key": "value"}, ["key"], "value"),
    ({"key": [{"nkey": "nvalue"}]}, ["key", 0, "nkey"], "nvalue"),
    ({"key": [{"test": "test0", "nkey": "zero"}, {"test": "test1", "nkey": "one"}]},
     ["key", {"test": "test1"}, "nkey"], "one"),
    ({"test2": [{'a': {"b": [{"c": "test1"}]}, "result": {"number": "one"}},
                {'a': {"b": [{"c": "test2"}]}, "result": {"number": "two"}}]},
     ["test2", {"a": ["b", {"c": 'test2'}]}, "result", 'number'], "two"),
    ({"a": {"b": None}}, ["a", "b"], None),
    ({"key": [{"test": "test0", "nkey": "zero", "skey": "zero"}, {"test": "test1", "nkey": "one", "skey": "zero"}]},
         ["key", {"skey": "zero", "test": "test1"}, "nkey"], "one")
]

get_by_path_data_default = [
    ({'a': 1}, ['b'], 0, 0),
    ({'a': {'b': None}}, ['a', 'b', 'c'], 0, 0),
]

parse_route_data = [
    ('b.{c:"test2"}', ['b', {'c': 'test2'}]),
    ('test2.{a:b.{c:"test2"}}.result.number',
     ['test2', {'a': ['b', {'c': 'test2'}]}, 'result', 'number']),
    ('class.code', ['class', 'code']),
    ('component.coding.{code:"4323-3"}.display', ['component', 'coding', {'code': '4323-3'}, 'display']),
    ('component.coding.{code:"4323-3"}.0.display',
     ['component', 'coding', {'code': '4323-3'}, 0, 'display']),
    ('component.coding.{code:"4323-3",system: "http://test.com"}.0.display',
     ['component', 'coding', {'code': '4323-3', 'system': 'http://test.com'}, 0, 'display']),
    ('bodySite.{coding:{system: "https://www.hpa.gov.tw/",code:"0"}}.coding.0.display',
     ['bodySite', {'coding': {'system': 'https://www.hpa.gov.tw/', 'code': '0'}}, 'coding', 0, 'display'])
]


@pytest.mark.parametrize("input_dict, path, default, expected_output", get_by_path_data_default)
def test_get_by_path_with_default(input_dict, path, expected_output, default):
    assert get_by_path(input_dict, path, default) == expected_output


@pytest.mark.parametrize("input_dict, path, expected_output", get_by_path_data)
def test_get_by_path(input_dict, path, expected_output):
    assert get_by_path(input_dict, path) == expected_output


@pytest.mark.parametrize("input_string, expected_output", parse_route_data)
def test_parse_route(input_string, expected_output):
    assert parse_route(input_string) == expected_output


@pytest.fixture
def resource():
    return {
        "resourceType": "Procedure",
        "id": "example",
        "status": "completed",
        "statusReason": {
            "coding": [
                {
                    "system": "https://www.hpa.gov.tw/",
                    "code": "1",
                    "display": "原發部位未手術原因"
                }
            ],
            "text": "原發部位未手術原因"
        },
        "category": {
            "coding": [
                {
                    "system": "https://www.hpa.gov.tw/",
                    "code": "2",
                    "display": "微創手術"
                }
            ],
            "text": "微創手術"
        },
        "code": {
            "coding": [
                {
                    "system": "https://www.hpa.gov.tw/",
                    "code": "50",
                    "display": "申報醫院原發部位手術方式"
                }
            ],
            "text": "申報醫院原發部位手術方式"
        },
        "subject": {
            "reference": "Patient/example"
        },
        "performedDateTime": "2018-02-23",
        "bodySite": [
            {
                "coding": [
                    {
                        "system": "https://www.hpa.gov.tw/",
                        "code": "0",
                        "display": "原發部位手術邊緣"
                    }
                ]
            },
            {
                "coding": [
                    {
                        "system": "https://www.hpa.gov.tw/",
                        "code": "999",
                        "display": "原發部位手術切緣距離"
                    }
                ]
            }
        ]
    }


@pytest.mark.parametrize("route, expected_output", [
    ('bodySite.{coding:{system: "https://www.hpa.gov.tw/",code:"0"}}.coding.0.display', "原發部位手術邊緣"),
    ('bodySite.{coding:{system: "https://www.hpa.gov.tw/",code:"999"}}.coding.0.display',
     "原發部位手術切緣距離"),
])
def test_regression(resource, route, expected_output):
    assert get_by_path(resource, parse_route(route)) == expected_output
