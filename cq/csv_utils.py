from random import shuffle
import csv

from cq.metrics import MetricCalculator


def get_file_contents(file_paths):
    files_contents = []
    for file_path in file_paths:
        with open(file_path, "r") as f:
            files_contents.append(f.read())
    return files_contents


def get_normalized_dataset(csv_reader, max_number_of_rows):
    false_results, true_results, false_null_results, true_null_results, rows = [], [], [], [], []
    for row in csv_reader:
        if float(row["_too"]) == 0:
            if row["result"] == "false":
                false_null_results.append(row)
            else:
                true_null_results.append(row)
            continue

        if row["result"] == "false":
            false_results.append(row)
        else:
            true_results.append(row)
    shuffle(false_results)
    shuffle(true_results)
    shuffle(false_null_results)
    shuffle(true_null_results)

    rows.extend(false_results[:max_number_of_rows])
    rows.extend(true_results[:max_number_of_rows])
    rows.extend(false_null_results[:max_number_of_rows - len(false_results)])
    rows.extend(true_null_results[:max_number_of_rows - len(true_results)])

    shuffle(rows)
    return rows


def remove_invalid_rows(max_number_of_rows):
    # Open the input and output CSV files
    with open("training/datasets/training_data_raw.csv", "r", newline="") as input_file, open(
            "training/datasets/training_data_raw_cut.csv", "w", newline="") as output_file:
        csv_reader = csv.DictReader(input_file)
        fieldnames = csv_reader.fieldnames
        csv_writer = csv.DictWriter(output_file, fieldnames=fieldnames)

        csv_writer.writeheader()

        rows = get_normalized_dataset(csv_reader, max_number_of_rows)

        for row in rows:
            csv_writer.writerow(row)


def change_dataset_results():
    # Open the input and output CSV files
    with open("training/datasets/training_data_raw_cut.csv", "r", newline="") as input_file, open(
            "training/datasets/training_data_main.csv", "w", newline="") as output_file:
        csv_reader = csv.DictReader(input_file)
        fieldnames = csv_reader.fieldnames
        print()
        csv_writer = csv.DictWriter(output_file, fieldnames=fieldnames)

        csv_writer.writeheader()
        rows = []
        for row in csv_reader:
            effort = float(row["effort"])
            halstead_volume = float(row["volume"])
            complexity = int(row["complexity"])
            sloc = int(row["total_lines"])
            comments = int(row["comments"])
            row['result'] = round(MetricCalculator().calculate_code_quality_by_metrics(
                effort, halstead_volume, complexity, sloc, comments
            ), 4)
            rows.append(row)

        for row in rows:
            csv_writer.writerow(row)
