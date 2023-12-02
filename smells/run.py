from tensorflow import keras
import numpy as np
from csv_utils import get_file_contents
from metrics import MetricCalculator
import ast

from smells.code_extractor import extract_classes, extract_functions

LARGE_CLASS_MODEL_PATH = "models/large_class_l_0.0420231130-110432/"
LONG_METHOD_MODEL_PATH = "models/long_method_l0.04_d20231130_t111129/"

test_paths = [
    "test_data/draft.py",
    # "good_code.py",
]


def get_model_input(code_fragment):
    calculator = MetricCalculator(code_fragment)
    print(f"{code_fragment=}")
    aaa = [
        [calculator.calculate_total_lines_of_code()],
        [calculator.calculate_logical_lines_of_code()],
        [calculator.calculate_lines_of_code()],
        [calculator.calculate_comments()],
        [calculator.calculate_single_comments()],
        [calculator.calculate_multi_comments()],
        [calculator.calculate_blanks()],
        [calculator.calculate_unique_operators()],
        [calculator.calculate_unique_operands()],
        [calculator.calculate_total_operators()],
        [calculator.calculate_total_operands()],
        [calculator.calculate_vocabulary()],
        [calculator.calculate_length()],
        [calculator.calculate_calculated_length()],
        [calculator.calculate_volume()],
        [calculator.calculate_difficulty()],
        [calculator.calculate_effort()],
        [calculator.calculate_time()],
        [calculator.calculate_bugs()],
    ]
    print(f"{aaa=}")
    return np.array(aaa)


def get_model_output(input_metrics, saved_model_path):
    loaded_model = keras.models.load_model(saved_model_path, compile=False)

    model_outputs = loaded_model.predict(input_metrics)
    scores = [round(x[0]) for x in model_outputs]
    print(f"{scores=}")


def find_model_scores(code_fragments, model_path):
    for code_fragment in code_fragments:
        input_metrics = get_model_input(code_fragment)
        print(f"{input_metrics=}")
        get_model_output(input_metrics, model_path)


def find_classes_scores(code):
    find_model_scores(extract_classes(code), LARGE_CLASS_MODEL_PATH)


def find_functions_scores(code):
    find_model_scores(extract_functions(code), LONG_METHOD_MODEL_PATH)


if __name__ == "__main__":
    for source_code in get_file_contents(test_paths):
        # find_classes_scores(source_code)
        find_functions_scores(source_code)
