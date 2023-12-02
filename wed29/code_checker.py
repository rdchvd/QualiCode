from caseconverter import snakecase
import pinecone
import re
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('intfloat/e5-small-v2')
pinecone.init(api_key="6a704b73-f867-4acc-be53-f84113669594", environment="gcp-starter")
index = pinecone.Index("english-words")


def convert_variable_to_snake_case(variable_name):
    return snakecase(variable_name)


def split_by_non_alphabetical(input_string):
    result = []
    current_sequence = ''
    prev_is_alpha = input_string[0].isalpha() if input_string else False

    for char in input_string:
        is_alpha = char.isalpha()

        if is_alpha == prev_is_alpha:
            # If the character type is the same as the previous one, add it to the current sequence
            current_sequence += char
        else:
            # If the character type changes, add the current sequence to the result
            if current_sequence:
                result.append(current_sequence)
                current_sequence = ''

            # Start a new sequence with the current character
            current_sequence = char

        prev_is_alpha = is_alpha

    # Add the last sequence if there is one
    if current_sequence:
        result.append(current_sequence)

    return result


# 🤙
def get_scores(index, words):
    embeddings = model.encode(words, normalize_embeddings=True).tolist()
    scores = []
    words = []
    for embedding in embeddings:
        result = index.query(vector=embedding, top_k=1, include_metadata=True)["matches"]
        if not result:
            continue
        words.append(result[0]["id"])
        if result[0]["score"] > 0.94:
            scores.append(min(max(result[0]["score"], -1), 1))
        else:
            scores.append(0)

    return scores, words


def get_score(var_name):
    snake_var_name = convert_variable_to_snake_case(var_name)
    words = list({i for i in split_by_non_alphabetical(snake_var_name) if len(i) > 1})
    scores, words = get_scores(index, words)
    return sum(scores) / len(scores)


def main():
    print("Average score: ", get_score("amznProductsByLocale123"))


if __name__ == "__main__":
    main()
