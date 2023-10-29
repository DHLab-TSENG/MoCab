import pytest
from base.object_store import fhir_resources_route


@pytest.mark.parametrize("route_name, expected_output", [
    ("lymph_invaded_amount", {
        "condition_name": "lymph_invaded_amount",
        "resource_type": "Observation",
        "methods": [
            "component",
            {
                "code": [
                    "coding",
                    {
                        "code": "NPOSIT"
                    }
                ]
            },
            "valueQuantity",
            "value"
        ]
    })
])
def test_get_route_dict(route_name, expected_output):
    result_dict = fhir_resources_route.get_route_dict(route_name)
    assert result_dict == expected_output


def test_get_route_dict_exception():
    with pytest.raises(KeyError, match="Rule is not exist in the resource.route."):
        assert fhir_resources_route.get_route_dict("not_exist")


def test_get_rule_dict():
    assert True
