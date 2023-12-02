from itertools import zip_longest

import nltk
from nltk.corpus import words
import pinecone
from datetime import datetime
from sentence_transformers import SentenceTransformer
from more_itertools import chunked

from wed29.csv_utils import get_unique_english_words

BATCH_SIZE = 2500

model = SentenceTransformer("intfloat/e5-small-v2")
nltk.download("words")


def process_chunks(index, words_list, batch_size=1000):
    success_counter = 0
    fail_counter = 0
    words_list_length = len(words_list)
    for words_chunk in chunked(words_list, batch_size):
        vectors_with_data = list(vectorize_words(words_chunk))
        try:
            index.upsert(vectors=vectors_with_data, batch_size=500)
            print(f"{len(vectors_with_data)} vectors created")
            save_handled_words_in_other_file(words_chunk)
            success_counter += BATCH_SIZE
            print(f"{success_counter}/{words_list_length} words saved")
        except Exception as e:
            print("error while upserting vectors: ", e)
            fail_counter += BATCH_SIZE
            save_non_handled_words_in_other_file(words_chunk)
            print(f"{fail_counter}/{words_list_length} words weren't saved")
        finally:
            print(f"total {success_counter + fail_counter}/{words_list_length} words handled")


def vectorize_words(words_list):
    vectors = model.encode(words_list, normalize_embeddings=True)
    created = {"created_at": datetime.now().isoformat()}
    vectors_with_data = zip_longest(words_list, vectors.tolist(), [created], fillvalue=created)
    return vectors_with_data


def get_bad_english_words():
    words_list = words.words()
    return list({word.lower() for word in words_list if word.isalpha()})


def save_handled_words_in_other_file(word_list):
    with open("wed29/handled_words.txt", "a") as f:
        for word in word_list:
            f.writelines(f"{word}\n")


def save_non_handled_words_in_other_file(word_list):
    with open("wed29/non_handled_words.csv", "a") as f:
        for word in word_list:
            f.writelines(f"{word}\n")


def delete_words(index, words_list):
    for words_chunk in chunked(words_list, 1000):
        index.delete(words_chunk)


def main():
    pinecone.init(api_key="6a704b73-f867-4acc-be53-f84113669594", environment="gcp-starter")
    # words_list = get_unique_english_words()
    index = pinecone.Index("english-words")

    words_list = get_unique_english_words()
    # delete_words(index, words_list)
    print(f"{len(words_list)} unique words loaded")
    #
    process_chunks(index, words_list, batch_size=BATCH_SIZE)


if __name__ == "__main__":
    main()
