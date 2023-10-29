import operator
import enum
from base import search_sets
from fhirpy.lib import SyncFHIRResource
from base.object_store import fhir_resources_route, cds_hooks_config_table
from base.route_converter import get_by_path


class Card(enum.Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


def validate_condition(value, transfer) -> bool:
    """
     validate whether the value is matching the condition
    :param value: String, Value of patient
    :param transfer: Dict, Condition and value that are ready to be compared.
    :return:
    """
    return getattr(operator, transfer['prefix'])(value, transfer['condition'])


def extract_resource(resource_type: str, fhir_resource: SyncFHIRResource, extract_methods: list):
    """
    Extract value from fhir resource
    :param resource_type: Patient or Encounter
    :param fhir_resource: SyncFHIRResource
    :param extract_methods: list, series of extract_methods. Including key of resource, or function
    :return: int, bool, str, float
    """
    if "()" in extract_methods[-1]:
        resource_obj = getattr(search_sets, resource_type)
        value = getattr(resource_obj, extract_methods[-1].replace("()", ""))(fhir_resource)
    else:
        value = get_by_path(fhir_resource, extract_methods)

    return value


def validation(value, **kwargs):
    return getattr(operator, kwargs['prefix'])(value, kwargs['condition'])


def model_evaluating(model_name: str,
                     patient_resource: SyncFHIRResource,
                     encounter_resource: SyncFHIRResource) -> bool:
    try:
        cds_hooks_config = cds_hooks_config_table.get_cds_hooks_table_dict(model_name)
    except KeyError:
        return False

    # If the condition is empty, always calculate it.
    if len(cds_hooks_config["condition"]) == 0:
        return True
    # Iterate all the conditions
    for key, value_list in cds_hooks_config["condition"].items():
        # First, extract the value inside the fhir resources
        route = fhir_resources_route.get_route_dict(key)
        value = None

        # TODO: Not dynamic.
        if route['resource_type'] == "Patient":
            if patient_resource is None:
                return False
            value = extract_resource(route['resource_type'], patient_resource, route['methods'])
        elif route['resource_type'] == "Encounter":
            if encounter_resource is None:
                return False
            value = extract_resource(route['resource_type'], encounter_resource, route['methods'])

        # Compare the value with conditions. If value doesn't match conditions, return False instead.
        for transformer in value_list:
            valid = validation(value, **transformer)
            if not valid:
                return False
    return True


def match_conditions(value, value_list) -> bool:
    for transformer in value_list:
        valid = validation(value, **transformer)
        if not valid:
            return False
    return True


def card_determine(patient_data_dictionary, model_name) -> Card or None:
    cds_hooks_config = cds_hooks_config_table.get_cds_hooks_table_dict(model_name)
    for card in [card_type.value for card_type in Card]:
        if match_conditions(patient_data_dictionary['predict_value'], cds_hooks_config[f'{card}_range']):
            print(f"Card Type: {card}")
            return getattr(Card, card.upper())
    return None
