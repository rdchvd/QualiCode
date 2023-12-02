import os
import re
import keras
import tensorflow
import numpy as np
from csv_utils import get_file_contents
from metrics import MetricCalculator
from wed29.code_checker import get_score as get_naming_score

from smells.code_extractor import extract_classes, extract_functions

LARGE_CLASS_MODEL_PATH = "models/large_class_l0.10_d20231202_t163418"
LONG_METHOD_MODEL_PATH = "models/long_method_l0.04_d20231202_t163426"

test_paths = [
    "test_data/draft.py",
    # "good_code.py",
]


def extract_entity_name(entity_string, entity_type):
    pattern = r"def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(" if entity_type == 'function' else r"class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*(?:\(|:)"
    match = re.match(pattern, entity_string)
    if match:
        return match.group(1)
    else:
        return None


def get_model_input(code_fragment):
    calculator = MetricCalculator(code_fragment)

    input_metrics = [
        calculator.calculate_total_lines_of_code(),
        calculator.calculate_logical_lines_of_code(),
        calculator.calculate_lines_of_code(),
        calculator.calculate_comments(),
        calculator.calculate_single_comments(),
        calculator.calculate_multi_comments(),
        calculator.calculate_blanks(),
        calculator.calculate_unique_operators(),
        calculator.calculate_unique_operands(),
        calculator.calculate_total_operators(),
        calculator.calculate_total_operands(),
        calculator.calculate_vocabulary(),
        calculator.calculate_length(),
        calculator.calculate_calculated_length(),
        calculator.calculate_volume(),
        calculator.calculate_difficulty(),
        calculator.calculate_effort(),
        calculator.calculate_time(),
        calculator.calculate_bugs(),
    ]
    return np.array(input_metrics).reshape(1, -1)


def get_model_output(input_metrics, saved_model_path):
    loaded_model = keras.models.load_model(saved_model_path, compile=False)

    model_outputs = loaded_model.predict(input_metrics)
    scores = [round(x[0]) for x in model_outputs]
    return scores


def find_model_scores(code_fragments, model_path, entity_type):
    for code_fragment in code_fragments:
        input_metrics = get_model_input(code_fragment)
        entity_name = extract_entity_name(code_fragment['fragment'], entity_type)
        print(entity_name)
        output = get_model_output(input_metrics, model_path)[0]
        name_score = round(get_naming_score(entity_name) * 10)
        print(
            f"Entity type: {entity_type}\nName: {entity_name}\nQuality score: {1 - output}/1\nNaming score: {name_score}/10",
            end="\n**********\n\n")


def find_classes_scores(code):
    find_model_scores(extract_classes(code), LARGE_CLASS_MODEL_PATH, "class")


def find_functions_scores(code):
    find_model_scores(extract_functions(code), LONG_METHOD_MODEL_PATH, "function")


def convert_models():
    loaded_model = keras.models.load_model(LARGE_CLASS_MODEL_PATH, compile=False)
    tensorflow.saved_model.save(loaded_model, ".".join(LARGE_CLASS_MODEL_PATH.split('.')[:2]))
    loaded_model = keras.models.load_model(LONG_METHOD_MODEL_PATH, compile=False)
    tensorflow.saved_model.save(loaded_model, ".".join(LONG_METHOD_MODEL_PATH.split('.')[:2]))


if __name__ == "__main__":
    for source_code in get_file_contents(test_paths):
        find_classes_scores(source_code)
        find_functions_scores(source_code)
