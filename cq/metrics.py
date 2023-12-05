from statistics import mean
from typing import Optional, Dict

from radon.complexity import cc_visit
from radon.raw import analyze
from radon.metrics import h_visit, mi_visit


class MetricCalculator:

    def __init__(self, code: Optional[Dict[str, type]] = None):
        self.code = code["fragment"]
        self.code_type = code["fragment_type"]
        self.set_metrics_for_code()

    def set_metrics_for_code(self):
        self.mccabe_metric = cc_visit(self.code)
        self.halstead_metric = h_visit(self.code)
        self.maintainability = mi_visit(code=self.code, multi=False)
        self.raw_self = analyze(self.code)

    def get_metrics_dict(self):
        return dict(
            _loc=self.calculate_lines_of_code(),
            complexity=self.calculate_complexity(),
            _too=self.calculate_total_operand_operators(),
            volume=self.calculate_volume(),
            _pl=self.calculate_program_length(),
            difficulty=self.calculate_difficulty(),
            _i=self.calculate_intelligence(),
            effort=self.calculate_effort(),
            bugs=self.calculate_bugs(),
            time=self.calculate_time(),
            total_lines=self.calculate_total_lines(),
            comments=self.calculate_comments(),
            blanks=self.calculate_blanks(),
            unique_operators=self.calculate_unique_operators(),
            unique_operands=self.calculate_unique_operands(),
            total_operators=self.calculate_total_operators(),
            total_operands=self.calculate_total_operands(),
        )

    def calculate_lines_of_code(self) -> int:
        """Calculates the lines of code."""
        return self.raw_self.sloc

    def calculate_logical_lines_of_code(self) -> int:
        """Calculates the lines of code."""
        return self.raw_self.lloc

    def calculate_total_lines_of_code(self) -> int:
        """Calculates the lines of code."""
        return self.raw_self.loc

    def calculate_complexity(self) -> float:
        """Calculates the McCabe complexity of the code."""
        complexities = [
            snippet.complexity for snippet in self.mccabe_metric if not getattr(snippet, "is_method", False)
        ]
        return mean(complexities)

    def calculate_total_operand_operators(self) -> int:
        """Calculates the lines of code."""
        return self.halstead_metric.total.N1 + self.halstead_metric.total.N2

    def calculate_volume(self) -> int:
        """Calculates the lines of code."""
        return self.halstead_metric.total.volume

    def calculate_program_length(self) -> int:
        """Calculates the lines of code."""
        return self.halstead_metric.total.calculated_length

    def calculate_difficulty(self) -> int:
        """Calculates the lines of code."""
        return self.halstead_metric.total.difficulty if self.halstead_metric.total.difficulty != 0 else 1

    def calculate_intelligence(self) -> int:
        """Calculates the lines of code."""
        return self.halstead_metric.total.volume / self.calculate_difficulty()

    def calculate_effort(self) -> int:
        """Calculates the lines of code."""
        return self.halstead_metric.total.effort

    def calculate_bugs(self) -> int:
        """Calculates the lines of code."""
        return self.halstead_metric.total.bugs

    def calculate_time(self) -> int:
        """Calculates the lines of code."""
        return self.halstead_metric.total.time

    def calculate_total_lines(self) -> int:
        """Calculates the lines of code."""
        return self.raw_self.loc

    def calculate_comments(self) -> int:
        """Calculates the lines of code."""
        return self.raw_self.comments

    def calculate_single_comments(self) -> int:
        """Calculates the lines of code."""
        return self.raw_self.single_comments

    def calculate_multi_comments(self) -> int:
        """Calculates the lines of code."""
        return self.raw_self.multi

    def calculate_blanks(self) -> int:
        """Calculates the lines of code."""
        return self.raw_self.blank

    def calculate_unique_operators(self) -> int:
        """Calculates the lines of code."""
        return self.halstead_metric.total.h1

    def calculate_unique_operands(self) -> int:
        """Calculates the lines of code."""
        return self.halstead_metric.total.h2

    def calculate_total_operators(self) -> int:
        """Calculates the lines of code."""
        return self.halstead_metric.total.N1

    def calculate_vocabulary(self) -> int:
        """Calculates the lines of code."""
        return self.halstead_metric.total.h1 + self.halstead_metric.total.h2

    def calculate_length(self) -> int:
        """Calculates the lines of code."""
        return self.halstead_metric.total.N1 + self.halstead_metric.total.N2

    def calculate_calculated_length(self) -> int:
        """Calculates the lines of code."""
        return self.halstead_metric.total.length

    def calculate_total_operands(self) -> int:
        """Calculates the lines of code."""
        return self.halstead_metric.total.N2
