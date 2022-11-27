import joblib


def predict(data: list):
    model_path = "YOUR_MODEL_PATH_HERE"  # path: "./models/{folder name}/{file name of the exported file.}"
    x = list()
    temp = data
    loaded_model = joblib.load(model_path)
    x.append(temp)
    result = loaded_model.predict_proba(x)
    return result[:, 1][0]
