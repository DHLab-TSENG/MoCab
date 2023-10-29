import joblib


def predict(data: list, base_path, model_type="register"):
    # @data comes from two places, one is from diabetes_predict(), the other is from flask(not sure where yet).
    # data allows two kind of value set, one is dictionary(the value returned from get_resources()),
    #   another is value(the value comes from frontend)
    # Put all the values into temp and get ready to predict
    x = list()
    # fixed variable: pregnancies=6, skinthickness=35, diabetespedigreefunction=0.627
    # controlled variable: glucose, diastolic blood pressure, insulin, height, weight, age

    temp = data
    loaded_model = joblib.load(f"{base_path}/{model_type}_model")
    x.append(temp)
    result = loaded_model.predict_proba(x)
    # result = [no's probability, yes's probability]
    # return negative's probability
    return result[:, 1][0]
