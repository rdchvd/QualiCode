from typing import List

from caseconverter import snakecase
import pinecone
from sentence_transformers import SentenceTransformer

from cq.settings import PINECONE_API_KEY


class NamingCodeChecker:
    def __init__(self, names: List[str] = None):
        pinecone.init(api_key=PINECONE_API_KEY, environment="gcp-starter")
        self.index = pinecone.Index("english-words")
        self.model = SentenceTransformer("intfloat/e5-small-v2")
        if names:
            self.names = names

    def check_names_scores(self):
        return [self.get_name_score(name) for name in self.names]

    @staticmethod
    def split_name_by_non_alphabetical_symbols(input_string):
        """Split a string into sequences of alphabetical and non-alphabetical characters."""
        if not input_string:
            return []

        result = []
        current_sequence = ""
        is_previous_alpha = input_string[0].isalpha()

        for char in input_string:
            is_alpha = char.isalpha()

            if is_alpha == is_previous_alpha:
                # if the character type is an alphabetical character, add it to the current sequence
                current_sequence += char
            else:
                # if the character type changes, add the current sequence to the result
                if current_sequence:
                    result.append(current_sequence)

                # start a new sequence with the current character
                current_sequence = char

            is_previous_alpha = is_alpha

        # add the last sequence if there is one
        if current_sequence:
            result.append(current_sequence)

        return result

    def search_similar_to_embedding(self, embedding):
        return self.index.query(vector=embedding, top_k=1, include_metadata=True)["matches"]

    def make_embedding(self, words):
        return self.model.encode(words, normalize_embeddings=True).tolist()

    def get_scores_for_inner_words(self, words: List[str]):
        embeddings = self.make_embedding(words)
        scores = []

        for embedding in embeddings:
            search_result = self.search_similar_to_embedding(embedding)

            if not search_result:
                continue

            if search_result[0]["score"] > 0.94:
                scores.append(min(max(search_result[0]["score"], -1), 1))
            else:
                scores.append(0)

        return scores

    def get_name_score(self, name: str) -> float:
        inner_words = self.split_name_by_non_alphabetical_symbols(snakecase(name))
        unique_inner_words = list({word for word in inner_words if len(word) > 1})
        scores = self.get_scores_for_inner_words(unique_inner_words)
        return sum(scores) / len(scores)
