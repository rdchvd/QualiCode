import csv
from typing import List


def read_first_column_from_csv_to_the_list_of_words(csv_file_path: str) -> List[str]:
    with open(csv_file_path, "r") as f:
        reader = csv.reader(f, delimiter=";")
        return [row[0] for row in reader]


def cut_off_words_with_less_than_n_length(words: List[str], n: int) -> List[str]:
    return [word for word in words if word and len(word) >= n and word.isalpha()]


def get_english_dictionary():
    words = read_first_column_from_csv_to_the_list_of_words("non_handled_words.csv")

    words = cut_off_words_with_less_than_n_length(words, 1)

    return list(set(words[:30000]))


if __name__ == "__main__":
    get_english_dictionary()