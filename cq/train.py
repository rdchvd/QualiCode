from settings import LARGE_CLASS_DATASET_NAME, LONG_METHOD_DATASET_NAME, GENERAL_SCORE_DATASET_NAME
from smells import create_and_train_smells_model
from general_score import create_and_train_general_score_model

if __name__ == "__main__":
    create_and_train_smells_model("large_class", LARGE_CLASS_DATASET_NAME)
    create_and_train_smells_model("long_method", LONG_METHOD_DATASET_NAME)
    create_and_train_general_score_model(GENERAL_SCORE_DATASET_NAME)
