from flask import Flask
from flask import abort
from flask import jsonify
from flask import request
from flask_cors import CORS
from config import configObject as conf

from cds_hooks import cds_app
from smart_on_fhir import smart_app
from continuous_training import ct_app

mocab_app = Flask(__name__)
mocab_app.register_blueprint(smart_app, url_prefix=conf.get('base_urls').get('smart_prefix'))
mocab_app.register_blueprint(cds_app.server, url_prefix=conf.get('base_urls').get('cds_hooks_prefix'))
mocab_app.register_blueprint(ct_app, url_prefix=conf.get('base_urls').get('continuous_training_prefix'))
CORS(mocab_app)

from base_module import return_model_result
from base_module import verify_data
from base import patient_data_search as ds
from base.object_store import feature_table


# Map the csv into dictionary
table = feature_table


@mocab_app.route('/', methods=['GET'])
def index():
    return "Hello, World!<br/><br/>請在網址列的/後面輸入你要搜尋的病患id即可得出結果<br/>Example: <a " \
           f"href=\"/pima_diabetes?id=test-03121002\">{conf.get('base_urls').get('BACKEND_URL')}/diabetes?id=test-03121002</a> "


@mocab_app.route('/exist_model')
def exist_model():
    return jsonify({"model": feature_table.get_exist_model_name()})


@mocab_app.route('/<api>', methods=['GET'])
def api_with_id(api):
    """
    Description:
        This api gets the request with patient's id and model, then the server would return the model's result
        and patient's data.

    :param api:<base>/<model name>?id=<patient's id>&hour_alive_format
    :return: json object
        {
            "predict_value": <int> or <double>
            "<feature's name>": {
                "date": YYYY-MM-DDThh:mm:ss,
                "value": <boolean> or <int> or <double> or <string> // depends on the data
            }
        }
    """
    # TODO: the hour_alive_time request value
    patient_id = request.values.get('id')
    if patient_id is None:
        abort(400, description="Please fill in patient's ID.")
    hour_alive_time = request.values.get('hour_alive_time')  # None if request has no hour_alive_time parameter

    patient_data_dict = ds.model_feature_search_with_patient_id(
        patient_id, table.get_model_feature_dict(api), data_alive_time=hour_alive_time)
    patient_data_dict["predict_value"] = return_model_result(patient_data_dict, api)
    return jsonify(patient_data_dict)


@mocab_app.route('/<api>/change', methods=['POST'])
# POST method will get the object body from frontend
# POST method will only return predict value(double or integer)
def api_with_post(api):
    """
    Description:
        This api gets the request with patient's data and model, then the server would return the model's result
        and patient's data.

    :param api: POST <base>/<model name>/change
    :return: json object
        {
            "predict_value": <int> or <double>
            "<feature's name>": {
                "date": YYYY-MM-DDThh:mm:ss,
                "value": <boolean> or <int> or <double> or <string> // depends on the data
            }
        }
    """
    patient_data_dict = request.get_json()
    verify_data(patient_data_dict, api)
    patient_data_dict["predict_value"] = return_model_result(patient_data_dict, api)
    return jsonify(patient_data_dict)
