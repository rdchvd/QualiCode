import ast
from ast import ClassDef, FunctionDef, AsyncFunctionDef, get_source_segment, iter_child_nodes, AST
from typing import List, Dict, Tuple
import re


class CodeExtractor:

    def __init__(self, source_code: str):
        self.source_code = source_code
        self.root_node = ast.parse(source_code)

    def extract_fragments(self, ast_node: AST, types_to_find: Tuple, list_of_fragments: List = None,) -> List[Dict[str, str]]:

        if list_of_fragments is None:
            list_of_fragments = []

        if isinstance(ast_node, types_to_find):
            list_of_fragments.append(
                {
                    "fragment": get_source_segment(self.source_code, ast_node),
                    "fragment_type": type(ast_node)
                }
            )

        for child_node in iter_child_nodes(ast_node):
            self.extract_fragments(child_node, types_to_find, list_of_fragments)

        return list_of_fragments

    def extract_classes(self) -> List[Dict[str, str]]:
        return self.extract_fragments(self.root_node, (ClassDef,))

    def extract_functions(self) -> List[Dict[str, str]]:
        return self.extract_fragments(self.root_node, (FunctionDef, AsyncFunctionDef))

    def extract_entities(self) -> List[Dict[str, str]]:
        return self.extract_fragments(self.root_node, (FunctionDef, AsyncFunctionDef, ClassDef))

    @staticmethod
    def extract_entity_name(entity_string, entity_type):
        if entity_type == "function":
            pattern = r"def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\("
        else:
            pattern = r"class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*(?:\(|:)"
        match = re.match(pattern, entity_string)
        if match:
            return match.group(1)
