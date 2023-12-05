import time
from typing import List, Tuple

import numpy as np
import csv
from random import random, shuffle
from keras.models import Sequential
from keras.layers import Dense, BatchNormalization
from sklearn.model_selection import train_test_split

from cq.settings import TEST_SIZE, EPOCHS_NUMBER, BATCH_SIZE, LARGE_CLASS_DATASET_NAME, LONG_METHOD_DATASET_NAME


def process_row(row: List) -> Tuple:
    """
    Convert a row from the dataset to a tuple of metrics and result.

    :param row: a row from the dataset
    :return: a tuple of metrics list and result
    """
    metrics = list(map(float, row[:-1]))
    result = float(row[-1])
    return metrics, result


def read_and_shuffle_data(dataset_name: str) -> Tuple[np.ndarray, np.ndarray]:
    """
    Read the dataset and shuffle the rows.
    :param dataset_name: the name of the dataset
    :return: a tuple of metrics and results
    """
    rows_metrics, rows_results = [], []
    with open(dataset_name, "r") as csvfile:
        reader = csv.reader(csvfile)
        # remove header
        next(reader)
        data_rows = list(reader)[:400]
        shuffle(data_rows)

        for row in data_rows:
            metrics, result = process_row(row)
            rows_metrics.append(metrics)
            rows_results.append(result)
    return np.array(rows_metrics), np.array(rows_results)


def create_model_structure(input_dim: int) -> Sequential:
    """
    Create a model structure.
    :param input_dim: the number of input dimensions
    :return: a model
    """
    return Sequential(
        [
            Dense(30, input_dim=input_dim, activation="relu"),
            BatchNormalization(),
            Dense(10, activation="relu"),
            Dense(1, activation="sigmoid"),
        ]
    )


def create_and_train_model(model_type: str, dataset_name: str) -> None:
    """
    Create and train a model.
    :param model_type: additional part of the model name
    :param dataset_name: the name of the dataset to train the model
    """
    X, y = read_and_shuffle_data(dataset_name)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=round(random() * 100)
    )
    model = create_model_structure(X_train.shape[1])
    model.compile(loss="mean_squared_error", optimizer="adam")
    model.fit(X_train, y_train, epochs=EPOCHS_NUMBER, batch_size=BATCH_SIZE, validation_data=(X_test, y_test))

    loss = model.evaluate(X_test, y_test)
    model_name = f"smells/models/{model_type}_l{loss:.2f}_d{time.strftime('%Y%m%d_t%H%M%S')}"
    model.save(model_name)

    print(f"Saved {model_type} model: {model_name}. Loss: {loss:.4f}")


if __name__ == "__main__":
    create_and_train_model("large_class", LARGE_CLASS_DATASET_NAME)
    create_and_train_model("long_method", LONG_METHOD_DATASET_NAME)
