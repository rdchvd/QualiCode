import time

import numpy as np
import csv
from random import random, sample, shuffle
from keras.models import Sequential
from keras.layers import Dense, BatchNormalization
from sklearn.model_selection import train_test_split
from keras.callbacks import EarlyStopping
from sklearn.preprocessing import MinMaxScaler

LARGE_CLASS_DATASET_NAME = "datasets/Python_LargeClassSmell_Dataset.csv"
LONG_METHOD_DATASET_NAME = "datasets/Python_LongMethodSmell_Dataset.csv"

EPOCHS_NUMBER = 100
BATCH_SIZE = 32
TEST_SIZE = 0.2


def process_row(row):
    metrics = list(map(float, row[:-1]))
    result = float(row[-1])
    return metrics, result


def read_and_shuffle_data(dataset_name):
    rows_metrics, rows_results = [], []
    with open(dataset_name, "r") as csvfile:
        reader = csv.reader(csvfile)
        next(reader)
        data_rows = list(reader)
        shuffle(data_rows)

        for row in data_rows:
            metrics, result = process_row(row)
            rows_metrics.append(metrics)
            rows_results.append(result)
    return np.array(rows_metrics), np.array(rows_results)


def create_model_structure(input_dim: int) -> Sequential:
    return Sequential(
        [
            Dense(30, input_dim=input_dim, activation="relu"),
            BatchNormalization(),
            Dense(10, activation="relu"),
            Dense(1, activation="sigmoid"),
        ]
    )


def create_and_train_model(model_type, dataset_name):
    X, y = read_and_shuffle_data(dataset_name)


    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=round(random() * 100)
    )
    model = create_model_structure(X_train.shape[1])
    model.compile(loss="mean_squared_error", optimizer="adam")
    print(f"{X_train=}")
    print(f"{X_train.shape[1]=}")
    print(f"{X_test=}")
    model.fit(X_train, y_train, epochs=EPOCHS_NUMBER, batch_size=BATCH_SIZE, validation_data=(X_test, y_test))

    loss = model.evaluate(X_test, y_test)
    model_name = f"models/{model_type}_l{loss:.2f}_d{time.strftime('%Y%m%d_t%H%M%S')}"
    model.save(model_name)

    print(f"Saved {model_type} model: {model_name}. Loss: {loss:.4f}")


if __name__ == "__main__":
    # todo: fix size issue
    create_and_train_model("large_class", LARGE_CLASS_DATASET_NAME)
    create_and_train_model("long_method", LONG_METHOD_DATASET_NAME)
