from datetime import datetime


class TimeDebug:
    start_time, end_time, result_time = None, None, None
    function_name = ""


    def __init__(self, function_name):
        self.function_name = function_name
        self.start()
        self.debug_data = []

    def start(self):
        print(f"Started {self.function_name}")
        self.start_time = datetime.now()

    def end(self):
        self.end_time = datetime.now()
        print(f"Finished {self.function_name}")
        self.result_time = self.end_time - self.start_time
        self.get_results()
        self.debug_data.append([self.result_time, self.function_name])

    def get_results(self):
        print(f'{"-" * 20} ** RESULTS ** {"-" * 20}')
        print(
            f"RESULT ({self.function_name})\nseconds: {self.result_time.seconds} \nmicroseconds:{self.result_time.microseconds}")
        print("_" * 50)

    @classmethod
    def sum_results(cls):
        debug_data_sum = sum([result_time.microseconds for result_time, function_name in cls.debug_data])
        print("_" * 50)
        print(f"{debug_data_sum=}")

    def print_sorted_results(self):
        print("_" * 50)
        print(sorted(self.debug_data, key=lambda x: x[0], reverse=True))
        print("_" * 50)

    @classmethod
    def clear_debug_data(cls):
        cls.debug_data = []
