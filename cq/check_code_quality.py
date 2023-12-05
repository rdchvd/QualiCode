from cq.csv_utils import get_file_contents
from cq.settings import LARGE_CLASS_MODEL_PATH, LONG_METHOD_MODEL_PATH
from cq.naming import NamingCodeChecker
from cq.smells import SmellCodeChecker
from cq.code_extractor import CodeExtractor
from cq.general_score import CodeChecker


def find_quality_scores(code_fragment, model_path, entity_type):
    score_dict = {}
    smell_checker = SmellCodeChecker(code_fragment)
    smells_input_metrics = smell_checker.get_model_input()
    smells_score = smell_checker.get_model_output(smells_input_metrics, model_path)[0]
    score_dict["smell"] = smell_checker.get_smell_from_score(smells_score, entity_type)

    entity_name = CodeExtractor.extract_entity_name(code_fragment['fragment'], entity_type)
    score_dict["entity_name"] = entity_name
    name_score = round(NamingCodeChecker().get_name_score(entity_name) * 10)
    score_dict["name_score"] = name_score

    general_score, maintainability = CodeChecker(code_fragment).get_general_quality_score(name_score, smells_score)
    score_dict["general_score"] = general_score
    score_dict["maintainability"] = maintainability
    return score_dict


def print_quality_scores(code_fragments, model_path, entity_type):
    for code_fragment in code_fragments:
        score_dict = find_quality_scores(code_fragment, model_path, entity_type)

        print(f"Name: {score_dict['entity_name']}")
        print("-----------------------")
        print(f"Entity type:            {entity_type}")
        print(f"Maintainability:        {round(score_dict['maintainability'] / 10, 1)}/10")
        print(f"Smell Found:            {score_dict['smell']}")
        print(f"Naming score:           {score_dict['name_score']}/10")
        print(f"General Quality score:  {score_dict['general_score']}/10")
        print("\n\n")


def check_files_code_quality(file_paths):
    for source_code in get_file_contents(list(file_paths)):
        extractor = CodeExtractor(source_code)
        print_quality_scores(extractor.extract_classes(), LARGE_CLASS_MODEL_PATH, "class")
        print_quality_scores(extractor.extract_functions(), LONG_METHOD_MODEL_PATH, "function")
