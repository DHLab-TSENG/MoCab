from fhirclient.client import FHIRClient
from flask import request, redirect, abort, jsonify
from flask import Blueprint
from base import patient_data_search as ds
from base.object_store import feature_table
from base.object_store import fhir_class_obj
from config import configObject as conf

smart_clientObj: FHIRClient
smart_app = Blueprint('smart_on_fhir', __name__)
table = feature_table


@smart_app.route("/<api>", methods=['GET'])
def smart_api_with_id(api):
    patient_id = request.values.get('id')
    if patient_id is None:
        abort(400, description="Please fill in patient's ID.")

    # if not check_auth():
    #     abort(401, description="SMART Auth is not enabled. Launch MoCab SMART Endpoint in EHR First.")

    patient_data_dict = ds.smart_model_feature_search_with_patient_id(
        patient_id, table.get_model_feature_dict(api))

    return jsonify(patient_data_dict)


@smart_app.route("/launch", methods=['GET'])
def smart_launch():
    # TODO: Change redirect_uri
    global smart_clientObj
    settings = {
        'app_id': 'mocab_app',
        'api_base': request.values.get("iss"),
        'redirect_uri': f"{conf.get('base_urls').get('BACKEND_URL')}{conf.get('base_urls').get('smart_prefix')}/fhir-app",
        'scope': " ".join(["patient/*.read", "launch"])
    }
    smart_clientObj = FHIRClient(settings=settings)

    return redirect(smart_clientObj.authorize_url)


@smart_app.route("/fhir-app", methods=["GET"])
def callback():
    global smart_clientObj
    try:
        smart_clientObj.handle_callback(request.url)
    except Exception as e:
        return f"""<h1>Authorization Error</h1><p>{e}</p><p><a href="/">Start over</a></p>"""
    if check_auth():
        fhir_class_obj.update_client(url=smart_clientObj.server.base_uri,
                                     authorization=f"bearer {smart_clientObj.server.auth.access_token}")
        print(smart_clientObj.__dict__)
        print(smart_clientObj.server.__dict__)
        print(smart_clientObj.server.auth.__dict__)
        return redirect(f"{conf.get('base_urls').get('FRONTEND_URL')}")
    return "Not Authorized"


def check_auth():
    global smart_clientObj
    try:
        return smart_clientObj.ready
    except AttributeError:
        return False
    except NameError:
        return False
