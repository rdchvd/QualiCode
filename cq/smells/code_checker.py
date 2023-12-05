import keras
import numpy as np
from cq.metrics import MetricCalculator
from cq.settings import LARGE_CLASS_MODEL_PATH, LONG_METHOD_MODEL_PATH


class SmellCodeChecker:
    def __init__(self, code_fragment):
        self.code_fragment = code_fragment

    def get_model_input(self):
        calculator = MetricCalculator(self.code_fragment)

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

    @staticmethod
    def get_smell_from_score(score: int, entity_type: str) -> str:
        if score:
            if entity_type == "function":
                return "Long Method"
            return "Large Class"
        return "No"

    @staticmethod
    def get_model_output(input_metrics: np.ndarray, saved_model_path: str):
        loaded_model = keras.models.load_model(saved_model_path, compile=False)
        scores = [round(x[0]) for x in loaded_model.predict(input_metrics)]
        return scores

    def get_large_class_score(self):
        smells_input_metrics = self.get_model_input()
        return self.get_model_output(smells_input_metrics, LARGE_CLASS_MODEL_PATH)[0]

    def get_long_method_score(self):
        smells_input_metrics = self.get_model_input()
        return self.get_model_output(smells_input_metrics, LONG_METHOD_MODEL_PATH)[0]