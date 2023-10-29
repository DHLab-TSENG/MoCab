from flask import Flask, json, request, Blueprint
from flask_cors import CORS

# flaskApp = Flask(__name__)
flaskApp = Blueprint('cds_hooks', __name__)


def init(app):
    # CORS(flaskApp)

    @flaskApp.route("/")
    def hello_world():
        return "Welcome to CDS Service", 200

    @flaskApp.route('/cds-services')
    def discovery():
        return json.jsonify(app.discovery()), 200

    @flaskApp.route('/cds-services/<id>', methods=['POST'])
    def service(id):
        requestData = request.json
        try:
            response = app.handle_hook(id, requestData)
            body = response.to_dict()
            return json.jsonify(body), response.httpStatusCode
        except:
            return "client error", 400

    return flaskApp
