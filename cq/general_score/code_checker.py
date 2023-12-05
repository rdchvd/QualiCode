from tensorflow import keras
import numpy as np
from cq.metrics import MetricCalculator
from cq.settings import GENERAL_SCORE_MODEL_PATH


class CodeChecker:
    def __init__(self, code_fragment):
        self.code_fragment = code_fragment

        calculated_code = MetricCalculator(code_fragment)
        self.maintainability = calculated_code.maintainability
        self.metrics_results = [calculated_code.get_metrics_dict()]

        self.model = keras.models.load_model(GENERAL_SCORE_MODEL_PATH, compile=False)

    @staticmethod
    def get_model_input(metrics_dict):
        return np.array([
            metrics_dict["complexity"],
            metrics_dict["volume"],
            metrics_dict["difficulty"],
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

    def get_general_quality_score(self, naming_score, smells_score):
        model_outputs = self.model.predict(np.array([self.get_model_input(x) for x in self.metrics_results]))
        # scores = [x for x in model_outputs]
        score = self.maintainability * 0.08 + naming_score * 0.2
        if smells_score:
            score = score - smells_score * 0.2
        return round(score, 1), self.maintainability
