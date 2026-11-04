import re
from typing import List, Optional, Tuple
import tree_sitter_languages
from tree_sitter import Node, Tree
from app.models.dependency import DependencyType


class ExtractedDependency:
    """Represents a static call, import or inheritance relationship."""
    def __init__(
        self,
        caller_name: str,
        caller_file_path: str,
        caller_line: int,
        callee_name: str,
        dependency_type: DependencyType = DependencyType.CALL,
    ):
        self.caller_name = caller_name
        self.caller_file_path = caller_file_path
        self.caller_line = caller_line
        self.callee_name = callee_name
        self.dependency_type = dependency_type


class CallGraphExtractor:
    """Extracts function-to-function call graphs and import dependencies via static AST analysis."""

    @classmethod
    def extract_dependencies(
        cls,
        code: str,
        language: str,
        file_path: str,
    ) -> List[ExtractedDependency]:
        """Parse source code and extract all outgoing calls and imports."""
        if language not in ("python", "javascript", "typescript", "go", "java"):
            return []

        try:
            parser = tree_sitter_languages.get_parser(language)
            tree: Tree = parser.parse(code.encode("utf-8"))
        except Exception:
            return []

        lines = code.splitlines()
        dependencies: List[ExtractedDependency] = []

        cls._traverse_for_calls(
            tree.root_node,
            lines,
            language,
            file_path,
            current_caller=f"module:{file_path}",
            deps=dependencies,
        )
        return dependencies

    @classmethod
    def _traverse_for_calls(
        cls,
        node: Node,
        lines: List[str],
        language: str,
        file_path: str,
        current_caller: str,
        deps: List[ExtractedDependency],
    ) -> None:
        """Recursive walker tracking current enclosing function and finding invocations."""
        node_type = node.type

        # Track enclosing function / method
        new_caller = current_caller
        if language == "python" and node_type in ("function_definition", "async_function_definition"):
            name_node = node.child_by_field_name("name")
            if name_node:
                new_caller = lines[name_node.start_point[0]][name_node.start_point[1]:name_node.end_point[1]]

        elif language in ("javascript", "typescript") and node_type in ("function_declaration", "method_definition"):
            name_node = node.child_by_field_name("name")
            if name_node:
                new_caller = lines[name_node.start_point[0]][name_node.start_point[1]:name_node.end_point[1]]

        elif language == "go" and node_type in ("function_declaration", "method_declaration"):
            name_node = node.child_by_field_name("name")
            if name_node:
                new_caller = lines[name_node.start_point[0]][name_node.start_point[1]:name_node.end_point[1]]

        elif language == "java" and node_type in ("method_declaration", "constructor_declaration"):
            name_node = node.child_by_field_name("name")
            if name_node:
                new_caller = lines[name_node.start_point[0]][name_node.start_point[1]:name_node.end_point[1]]

        # Detect Function Calls
        if language == "python" and node_type == "call":
            func_node = node.child_by_field_name("function")
            if func_node:
                callee_text = lines[func_node.start_point[0]][func_node.start_point[1]:func_node.end_point[1]]
                # Extract bare function name from attribute e.g. self.authenticate_user -> authenticate_user
                clean_callee = callee_text.split(".")[-1].strip()
                if clean_callee and clean_callee not in ("print", "len", "range", "str", "int", "dict", "list", "set"):
                    deps.append(
                        ExtractedDependency(
                            caller_name=new_caller,
                            caller_file_path=file_path,
                            caller_line=node.start_point[0] + 1,
                            callee_name=clean_callee,
                            dependency_type=DependencyType.CALL,
                        )
                    )

        elif language in ("javascript", "typescript") and node_type == "call_expression":
            func_node = node.child_by_field_name("function")
            if func_node:
                callee_text = lines[func_node.start_point[0]][func_node.start_point[1]:func_node.end_point[1]]
                clean_callee = callee_text.split(".")[-1].strip()
                if clean_callee and clean_callee not in ("console", "log", "error", "push", "map", "filter"):
                    deps.append(
                        ExtractedDependency(
                            caller_name=new_caller,
                            caller_file_path=file_path,
                            caller_line=node.start_point[0] + 1,
                            callee_name=clean_callee,
                            dependency_type=DependencyType.CALL,
                        )
                    )

        elif language == "go" and node_type == "call_expression":
            func_node = node.child_by_field_name("function")
            if func_node:
                callee_text = lines[func_node.start_point[0]][func_node.start_point[1]:func_node.end_point[1]]
                clean_callee = callee_text.split(".")[-1].strip()
                deps.append(
                    ExtractedDependency(
                        caller_name=new_caller,
                        caller_file_path=file_path,
                        caller_line=node.start_point[0] + 1,
                        callee_name=clean_callee,
                        dependency_type=DependencyType.CALL,
                    )
                )

        elif language == "java" and node_type == "method_invocation":
            name_node = node.child_by_field_name("name")
            if name_node:
                callee_text = lines[name_node.start_point[0]][name_node.start_point[1]:name_node.end_point[1]]
                deps.append(
                    ExtractedDependency(
                        caller_name=new_caller,
                        caller_file_path=file_path,
                        caller_line=node.start_point[0] + 1,
                        callee_name=callee_text.strip(),
                        dependency_type=DependencyType.CALL,
                    )
                )

        # Recurse children with current caller context
        for child in node.children:
            cls._traverse_for_calls(child, lines, language, file_path, new_caller, deps)
