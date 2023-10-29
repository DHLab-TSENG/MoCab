import base.cds_hooks_work as cds

from base_module import return_model_result
from base.cds_hooks_validator import model_evaluating
from base.cds_hooks_validator import Card
from base.cds_hooks_validator import card_determine
from base.patient_data_search import model_feature_search_with_patient_id
from base.object_store import feature_table
from base.object_store import fhir_class_obj
from config import configObject as conf
from fhirpy.base.exceptions import ResourceNotFound

cds_app = cds.App()


def model_evaluation(patient_id, encounter_id) -> list:
    """
    Evaluate which models should be automatically calculated in this round.
    :param patient_id:
    :param encounter_id:
    :return:
    """
    fhir_client = fhir_class_obj.client()
    encounter_resource = None
    model_list = []

    # TODO: 之後改掉，取得Resources 的動作統一在search_sets 中執行
    patient_resource = fhir_client.resources("Patient").search(_id=patient_id).limit(1).get()
    if encounter_id != "":
        try:
            encounter_resource = fhir_client.resources("Encounter").search(_id=encounter_id).limit(1).get()
        except ResourceNotFound:
            print("No resource found")

    for model_name in feature_table.get_exist_model_name():
        if model_evaluating(model_name,
                            patient_resource=patient_resource,
                            encounter_resource=encounter_resource):
            model_list.append(model_name)

    return model_list


@cds_app.patient_view("MoCab-CDS-Service", "The patient greeting service greets a patient!", title="Patient Greeter")
def greeting(r: cds.PatientViewRequest, response: cds.Response):
    conf['patient_id'] = r.context.patientId

    try:
        fhir_class_obj.update_client(url=r.fhirServer,
                                     authorization=f"{r.fhirAuthorization.token_type} {r.fhirAuthorization.access_token}")
    except Exception as e:
        raise Exception(e)

    # Add some if-else statement of models' using situation.
    calculated_list = model_evaluation(r.context.patientId, r.context.encounterId)

    # iterate all require models
    for model_name in calculated_list:
        """
            1. 首先是要確認病患ID在資料庫中的資料集是否足夠，所以這時候會去試探Server看是否有數據
            2. 確認有資料後，就會將數據丟入Model中進行預測
            3. 預測完成後，根據Model Score判斷應該要回傳info card 或是 warning card (TODO: 需要一個表格去填寫何時使用warning card)
            4. 回傳Warning Card
        """
        try:
            patient_data_dictionary = model_feature_search_with_patient_id(r.context.patientId,
                                                                           feature_table.get_model_feature_dict(
                                                                               model_name))
        except (ResourceNotFound, KeyError) as e:
            # TODO: What to do if resources are not found in the server?
            print(e)
            continue

        try:
            patient_data_dictionary["predict_value"] = return_model_result(patient_data_dictionary, model_name)
        except KeyError as e:
            print(e)
            continue
        except Exception as e:
            print(e)
            continue

        card = generate_cds_card(r.context.patientId, patient_data_dictionary, model_name)
        response.add_card(card)
    response.httpStatusCode = 200


def generate_cds_card(patient_id, patient_data_dictionary, model_name) -> cds.Card:  # Model generate card.
    card_used = card_determine(patient_data_dictionary, model_name)

    model_name = "".join([i if i.isalnum() else " " for i in model_name])
    source = cds.Source(label="MoCab CDS Service",
                        url="https://www.mo-cab.dev",
                        icon="https://i.imgur.com/sFUFOyO.png")
    # suggestions = [cds.Suggestion(label="Suggestions", isRecommended=True)]
    if card_used is Card.CRITICAL:
        summary = f"Patient {patient_id} has a high risk of \"{model_name}\".\n"
        detail = f"{model_name} model captures a high risk. "
    elif card_used is Card.WARNING:
        summary = f"Patient {patient_id} has a warning of \"{model_name}\".\n"
        detail = f"{model_name} model captures a warning. "
    elif card_used is Card.INFO:
        summary = f"Patient {patient_id} looks fine on \"{model_name}\".\n"
        detail = f"Looks fine on {model_name}. "
    else:
        raise Exception(f"No such card: {card_used}.")
    detail += f"""Model Score: {round(patient_data_dictionary['predict_value'], 2)}  
    More detail..."""

    card = getattr(cds.Card, card_used.value)(summary, source, detail=detail)
    card.add_link(cds.Link.smart(
        "MoCab-App",
        f"{conf.get('base_urls').get('BACKEND_URL')}{conf.get('base_urls').get('smart_prefix')}/launch"
    ))
    return card
