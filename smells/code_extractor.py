import ast
from ast import ClassDef, FunctionDef, AsyncFunctionDef, get_source_segment, iter_child_nodes, AST
from typing import List, Dict, Tuple


def extract_fragments(
        source_code: str, ast_node: AST, types_to_find: Tuple, list_of_fragments: List = None,
) -> List[Dict[str, str]]:
    if list_of_fragments is None:
        list_of_fragments = []
    if isinstance(ast_node, types_to_find):
        list_of_fragments.append(
            {
                "fragment": get_source_segment(source_code, ast_node),
                "fragment_type": type(ast_node)
            }
        )
    for child_node in iter_child_nodes(ast_node):
        extract_fragments(source_code, child_node, types_to_find, list_of_fragments)
    return list_of_fragments


def extract_classes(source_code: str) -> List[Dict[str, str]]:
    ast_node = ast.parse(source_code)
    return extract_fragments(source_code, ast_node, (ClassDef,))


def extract_functions(source_code: str) -> List[Dict[str, str]]:
    ast_node = ast.parse(source_code)
    return extract_fragments(source_code, ast_node, (FunctionDef, AsyncFunctionDef))
