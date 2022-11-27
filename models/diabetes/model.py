import joblib


def predict(data: list):
    x = list()
    temp = data
    loaded_model = joblib.load("./models/diabetes/finalized_model.sav")
    x.append(temp)
    result = loaded_model.predict_proba(x)
    return result[:, 1][0]
