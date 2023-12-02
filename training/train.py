import time

import numpy as np
import csv
from random import random, sample, shuffle
from keras.models import Sequential
from keras.layers import Dense, BatchNormalization
from sklearn.model_selection import train_test_split
from keras.callbacks import EarlyStopping
from sklearn.preprocessing import MinMaxScaler

scaler = MinMaxScaler()
# Define the Early Stopping callback
early_stopping = EarlyStopping(monitor="val_loss",  # Monitor validation loss
                               min_delta=0.1,  # Minimum change to qualify as an improvement
                               patience=10,  # Number of epochs with no improvement after which training will be stopped
                               verbose=1,  # Print messages about Early Stopping progress
                               restore_best_weights=False)  # Restore model weights from the epoch with the best value of the monitored quantity

# Load your dataset here as X (input features) and y (output/target)
# For example:
# X = np.array([[metric1, metric2, ..., metric13], ...])  # Input features
# y = np.array([score1, score2, ..., scoreN])  # Output/target

X = []
y = []

dataset_name = "datasets/daryna/training_data"
# dataset_name = "datasets/training_data_trunc_rev"
method = "main"
# method = "diff"
# method = "mccabe"
epochs = 100

with open(f"{dataset_name}_{method}.csv", "r") as csvfile:
    reader = csv.reader(csvfile)
    next(reader)
    data_rows = list(reader)
    shuffle(data_rows)
    for row in data_rows:
        # Split the row into 14 parts and extract metrics and result
        metrics = list(map(float, row[:17]))  # Extract first 13 parts as metrics
        print()
        result = float(row[-1])  # Extract the last part as result

        X.append(metrics)
        y.append(result)

# Convert lists to numpy arrays for better compatibility with Keras
# X = np.array(scaler.fit_transform(X, y))

X = np.array(X)
y = np.array(y)

# Split the dataset into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=round(random() * 100))

model = Sequential()

# model.add(Dense(32, input_dim=X_train.shape[1], activation="relu"))
# model.add(BatchNormalization())
# model.add(Dense(16, activation="relu"))
# model.add(Dense(1, activation="sigmoid"))
model.add(Dense(30, input_dim=X_train.shape[1], activation="relu"))
# model.add(Dense(300, activation="relu"))
# model.add(Dense(60, activation="relu"))
model.add(BatchNormalization())
model.add(Dense(10, activation="relu"))
model.add(Dense(1, activation="sigmoid"))

# Compile the model
model.compile(loss="mean_squared_error", optimizer="adam")

# Train the model
model.fit(X_train, y_train, epochs=epochs, batch_size=32, validation_data=(X_test, y_test),
          #    callbacks=[early_stopping]
          )

# Evaluate the model on the test set
loss = model.evaluate(X_test, y_test)
model_name = f"models/{method}-l_{loss:.2f}{time.strftime('%Y%m%d-%H%M%S')}"
model.save(model_name)

print("Saved model:", model_name)

print("Mean Squared Error on Test Set:", loss)
