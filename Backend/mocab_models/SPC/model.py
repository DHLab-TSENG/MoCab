import yaml
import pandas as pd
import tensorflow as tf

from joblib import dump, load
from sklearn.preprocessing import OneHotEncoder
from keras import metrics
from tensorflow.keras.optimizers.legacy import Adam


def config(base_path):
    """
    Function config會設定model的參數
    """
    with open(f'{base_path}/config.yaml', 'r') as f:
        config = yaml.load(f, Loader=yaml.Loader)
    return config


def encode(x, y, base_path):
    """
    Function encode will transform data into model preferred category
    """
    try:
        enc = load(f'{base_path}/encoder.joblib')
    except FileNotFoundError:
        raise FileNotFoundError("Encoder not found")

    column_enc = list(enc.feature_names_in_)
    if type(x) == list:
        df = pd.DataFrame(columns=column_enc)
        df.loc[0] = x
    else:
        df = x
    x_enc = enc.transform(df.astype(str))
    x_enc = pd.DataFrame(x_enc.toarray(), columns=enc.get_feature_names_out())

    return x_enc, y


def train(x_train, y_train, base_path):
    conf = config(base_path)
    METRICS = [
        metrics.Precision(thresholds=conf['set_thres']),
        metrics.Recall(thresholds=conf['set_thres']),
        metrics.AUC()
    ]

    # Load and compile Keras model
    opt_adam = Adam(learning_rate=conf['lr_rate'])
    model = tf.keras.models.load_model(f"{base_path}/register_model")
    model.compile(optimizer=opt_adam, loss=tf.losses.BinaryFocalCrossentropy(gamma=2.0), metrics=METRICS)

    model.fit(x_train, y_train,
              batch_size=16, epochs=conf['epoch'], verbose=0)

    model.save(f"{base_path}/new_model")

    return True


def get_model(model_type, base_path):
    if model_type == 'register':
        return tf.keras.models.load_model(f"{base_path}/register_model")
    elif model_type == 'new':
        return tf.keras.models.load_model(f"{base_path}/new_model")
    else:
        return None


def predict(data, base_path, model_type="register"):
    model = tf.keras.models.load_model(f"{base_path}/{model_type}_model")
    result = model.predict(data, verbose=0)
    return float(result[0][0])
