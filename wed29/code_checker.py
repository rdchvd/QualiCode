from caseconverter import snakecase
import pinecone
import re
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('intfloat/e5-small-v2')


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
def getScores(index, words):
    embeddings = model.encode(words, normalize_embeddings=True).tolist()
    scores = []
    words = []
    for embedding in embeddings:
        result = index.query(vector=embedding, top_k=1, include_metadata=True)["matches"]
        if not result:
            continue
        words.append(result[0]["id"])
        # scores.append(min(max(result[0]["score"], -1), 1))
        if result[0]["score"] > 0.94:
            scores.append(result[0]["score"])
        else:
            scores.append(0)

    return scores, words


def main():
    pinecone.init(api_key="6a704b73-f867-4acc-be53-f84113669594", environment="gcp-starter")
    # words_list = get_unique_english_words()
    index = pinecone.Index("english-words")
    varName = "amznProductsByLocale123"
    # varName = "someVariable1232"
    snakeVarName = convert_variable_to_snake_case(varName)
    words = list({i for i in split_by_non_alphabetical(snakeVarName) if len(i) > 1})
    scores, words = getScores(index, words)
    print(words, scores)
    print("Average score: ", sum(scores) / len(scores))


if __name__ == "__main__":
    main()
