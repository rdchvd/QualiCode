from itertools import zip_longest
from typing import List, Tuple

import pinecone
from datetime import datetime

from more_itertools import chunked

from cq.naming.dictionary import get_english_dictionary
from cq.naming.vectorizer import VectorizerModel
from cq.settings import PINECONE_API_KEY


class PineconeWriter:
    BATCH_SIZE = 500
    HANDLED_WORDS_FILE_NAME = "handled_words.csv"
    NON_HANDLED_WORDS_FILE = "non_handled_words.csv"

    def __init__(self):
        pinecone.init(api_key=PINECONE_API_KEY, environment="gcp-starter")
        self.index = pinecone.Index("english-words")
        self.words = get_english_dictionary()

    def upload_words(self):
        """Upload words to pinecone index """
        success_counter, fail_counter = 0, 0
        words_list_length = len(self.words)

        for words_chunk in chunked(self.words, self.BATCH_SIZE):
            vectors_with_data = list(self.vectorize_words(words_chunk))
            try:
                self.index.upsert(vectors=vectors_with_data)
                self.write_words_to_file(self.HANDLED_WORDS_FILE_NAME, words_chunk)
                success_counter += self.BATCH_SIZE
                print(f"{success_counter}/{words_list_length} words were saved.")

            except Exception as e:
                print(f"Error while uploading words chuck: {e}")
                fail_counter += self.BATCH_SIZE
                self.write_words_to_file(self.NON_HANDLED_WORDS_FILE, words_chunk)
                print(f"{fail_counter}/{words_list_length} words weren't saved.")

            finally:
                print(f"Total {success_counter + fail_counter}/{words_list_length} words were handled.")

    @staticmethod
    def vectorize_words(words: List[str]) -> List[Tuple]:
        """
        Vectorize words with SentenceTransformer
        :param words: list of words
        :return: list of tuples with word, vector and metadata
        """
        vectors = VectorizerModel.encode(words, normalize_embeddings=True)
        created = {"created_at": datetime.now().isoformat()}
        vectors_with_data = zip_longest(words, vectors.tolist(), [created], fillvalue=created)
        return vectors_with_data

    @staticmethod
    def write_words_to_file(file_name: str, word_list: List[str]):
        """
        Write words to file
        :param file_name: name of file to write words
        :param word_list: list of words to write
        """
        with open(file_name, "a") as f:
            for word in word_list:
                f.writelines(f"{word}\n")

    def delete_words(self, words: List[str]):
        """
        Delete words from pinecone index
        :param words: list of words to delete
        """
        for words_chunk in chunked(words, self.BATCH_SIZE):
            self.index.delete(words_chunk)
