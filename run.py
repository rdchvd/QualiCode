from tensorflow import keras
import numpy as np
from csv_utils import remove_invalid_rows, get_file_contents, change_dataset_results
from metrics import MetricCalculator
import ast

test_paths = [
    "draft.py",
    # "good_code.py",
]
RESULTS_MAX = 2000


def extract_fragments(source, node, fragments):
    if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
        fragments.append({
            "fragment": ast.get_source_segment(source, node),
            "fragment_type": type(node)
        })
    for child_node in ast.iter_child_nodes(node):
        extract_fragments(source, child_node, fragments)
    return fragments


def get_model_input(metrics_dict):
    return np.array([
        metrics_dict["_loc"],
        metrics_dict["complexity"],
        metrics_dict["_too"],
        metrics_dict["volume"],
        metrics_dict["_pl"],
        metrics_dict["difficulty"],
        metrics_dict["_i"],
        metrics_dict["effort"],
        metrics_dict["bugs"],
        metrics_dict["time"],
        metrics_dict["total_lines"],
        metrics_dict["comments"],
        metrics_dict["blanks"],
        metrics_dict["unique_operators"],
        metrics_dict["unique_operands"],
        metrics_dict["total_operators"],
        metrics_dict["total_operands"],

    ])


def test_code_quality():
    test_files_contents = get_file_contents(test_paths)
    saved_model_path = "main-l_0.0120231106-225925/"
    loaded_model = keras.models.load_model(saved_model_path, compile=False)

    for code in test_files_contents:
        metrics_results = []
        meh = []
        tree = ast.parse(code)
        fragments = extract_fragments(code, tree, [])
        for code_fragment in fragments:
            calculated_code = MetricCalculator(code_fragment)
            metrics_results.append(calculated_code.get_metrics_dict())

            meh.append(
                calculated_code.maintainability
            )

        model_outputs = loaded_model.predict(np.array([get_model_input(x) for x in metrics_results]))
        scores = [round(x[0]) for x in model_outputs]
        for idx, score in enumerate(scores):
            print("Test file:", fragments[idx]["fragment"])
            print("Metrics:", metrics_results[idx])
            print("My score:", meh[idx])
            print("Prediction:", score, end="\n\n*****\n\n")


if __name__ == "__main__":
    test_code_quality()
