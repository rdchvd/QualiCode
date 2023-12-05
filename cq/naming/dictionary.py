import csv
from typing import List

from cq.settings import NAMING_DATASET_NAME


def read_csv_to_the_list_of_words(csv_file_path: str) -> List[str]:
    """
    Read csv file and return list of words
    :param csv_file_path: path to csv file
    :return: list of words
    """
    with open(csv_file_path, "r") as f:
        reader = csv.reader(f, delimiter=";")
        return [row[0] for row in reader]


def cut_off_words_with_length(words: List[str], cut_off_length: int) -> List[str]:
    """
    Cut off words with length less than cut_off_length
    :param words: list of words
    :param cut_off_length: length of words to remove from list
    :return: list of words with length more than cut_off_length
    """
    return [word for word in words if word and len(word) >= cut_off_length and word.isalpha()]


def get_english_dictionary():
    """
    Get list of english words
    :return: list of english words
    """
    words = read_csv_to_the_list_of_words(NAMING_DATASET_NAME)

    words = cut_off_words_with_length(words, 1)

    return list(set(words[:30000]))


if __name__ == "__main__":
    get_english_dictionary()
