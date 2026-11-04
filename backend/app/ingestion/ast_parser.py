import re
from typing import List, Optional, Dict, Any
import tree_sitter_languages
from tree_sitter import Node, Tree
from app.models.code_symbol import SymbolType


class ParsedSymbol:
    """Represents a structural code symbol extracted from the AST."""
    def __init__(
        self,
        name: str,
        symbol_type: SymbolType,
        start_line: int,
        end_line: int,
        signature: Optional[str] = None,
        docstring: Optional[str] = None,
    ):
        self.name = name
        self.symbol_type = symbol_type
        self.start_line = start_line
        self.end_line = end_line
        self.signature = signature
        self.docstring = docstring


class ASTParser:
    """Polyglot syntax parser leveraging Tree-sitter to extract functions, classes, and methods."""

    SUPPORTED_LANGUAGES = {"python", "javascript", "typescript", "java", "go"}

    @classmethod
    def is_supported(cls, language: str) -> bool:
        return language in cls.SUPPORTED_LANGUAGES

    @classmethod
    def parse_code(cls, code: str, language: str) -> List[ParsedSymbol]:
        """Extract all functions, classes and methods from source code."""
        if not cls.is_supported(language):
            return []

        try:
            parser = tree_sitter_languages.get_parser(language)
            tree: Tree = parser.parse(code.encode("utf-8"))
        except Exception:
            return []

        symbols: List[ParsedSymbol] = []
        lines = code.splitlines()

        cls._traverse_node(tree.root_node, lines, language, symbols)
        return symbols

    @classmethod
    def _traverse_node(
        cls,
        node: Node,
        lines: List[str],
        language: str,
        symbols: List[ParsedSymbol],
        parent_class: Optional[str] = None,
    ) -> None:
        """Recursive AST walker extracting relevant syntactic structures."""
        node_type = node.type

        # ---------------- Python ----------------
        if language == "python":
            if node_type == "class_definition":
                name_node = node.child_by_field_name("name")
                if name_node:
                    class_name = lines[name_node.start_point[0]][name_node.start_point[1]:name_node.end_point[1]]
                    start_l = node.start_point[0] + 1
                    end_l = node.end_point[0] + 1
                    sig = lines[node.start_point[0]].strip()
                    doc = cls._extract_python_docstring(node, lines)
                    symbols.append(
                        ParsedSymbol(
                            name=class_name,
                            symbol_type=SymbolType.CLASS,
                            start_line=start_l,
                            end_line=end_l,
                            signature=sig,
                            docstring=doc,
                        )
                    )
                    # Recurse children with parent_class
                    for child in node.children:
                        cls._traverse_node(child, lines, language, symbols, parent_class=class_name)
                    return

            elif node_type == "function_definition":
                name_node = node.child_by_field_name("name")
                if name_node:
                    func_name = lines[name_node.start_point[0]][name_node.start_point[1]:name_node.end_point[1]]
                    start_l = node.start_point[0] + 1
                    end_l = node.end_point[0] + 1
                    sig = lines[node.start_point[0]].strip()
                    doc = cls._extract_python_docstring(node, lines)
                    sym_type = SymbolType.METHOD if parent_class else SymbolType.FUNCTION
                    full_name = f"{parent_class}.{func_name}" if parent_class else func_name
                    symbols.append(
                        ParsedSymbol(
                            name=full_name,
                            symbol_type=sym_type,
                            start_line=start_l,
                            end_line=end_l,
                            signature=sig,
                            docstring=doc,
                        )
                    )
                    return

        # ---------------- JavaScript / TypeScript ----------------
        elif language in ("javascript", "typescript"):
            if node_type in ("class_declaration", "interface_declaration"):
                name_node = node.child_by_field_name("name")
                if name_node:
                    cname = lines[name_node.start_point[0]][name_node.start_point[1]:name_node.end_point[1]]
                    sym_type = SymbolType.CLASS if node_type == "class_declaration" else SymbolType.INTERFACE
                    symbols.append(
                        ParsedSymbol(
                            name=cname,
                            symbol_type=sym_type,
                            start_line=node.start_point[0] + 1,
                            end_line=node.end_point[0] + 1,
                            signature=lines[node.start_point[0]].strip(),
                        )
                    )
                    for child in node.children:
                        cls._traverse_node(child, lines, language, symbols, parent_class=cname)
                    return

            elif node_type in ("function_declaration", "method_definition"):
                name_node = node.child_by_field_name("name")
                if name_node:
                    fname = lines[name_node.start_point[0]][name_node.start_point[1]:name_node.end_point[1]]
                    sym_type = SymbolType.METHOD if (parent_class or node_type == "method_definition") else SymbolType.FUNCTION
                    full_name = f"{parent_class}.{fname}" if parent_class else fname
                    symbols.append(
                        ParsedSymbol(
                            name=full_name,
                            symbol_type=sym_type,
                            start_line=node.start_point[0] + 1,
                            end_line=node.end_point[0] + 1,
                            signature=lines[node.start_point[0]].strip(),
                        )
                    )
                    return

        # ---------------- Go ----------------
        elif language == "go":
            if node_type in ("function_declaration", "method_declaration"):
                name_node = node.child_by_field_name("name")
                if name_node:
                    fname = lines[name_node.start_point[0]][name_node.start_point[1]:name_node.end_point[1]]
                    sym_type = SymbolType.METHOD if node_type == "method_declaration" else SymbolType.FUNCTION
                    symbols.append(
                        ParsedSymbol(
                            name=fname,
                            symbol_type=sym_type,
                            start_line=node.start_point[0] + 1,
                            end_line=node.end_point[0] + 1,
                            signature=lines[node.start_point[0]].strip(),
                        )
                    )
                    return

        # ---------------- Java ----------------
        elif language == "java":
            if node_type in ("class_declaration", "interface_declaration"):
                name_node = node.child_by_field_name("name")
                if name_node:
                    cname = lines[name_node.start_point[0]][name_node.start_point[1]:name_node.end_point[1]]
                    sym_type = SymbolType.CLASS if node_type == "class_declaration" else SymbolType.INTERFACE
                    symbols.append(
                        ParsedSymbol(
                            name=cname,
                            symbol_type=sym_type,
                            start_line=node.start_point[0] + 1,
                            end_line=node.end_point[0] + 1,
                            signature=lines[node.start_point[0]].strip(),
                        )
                    )
                    for child in node.children:
                        cls._traverse_node(child, lines, language, symbols, parent_class=cname)
                    return
            elif node_type in ("method_declaration", "constructor_declaration"):
                name_node = node.child_by_field_name("name")
                if name_node:
                    mname = lines[name_node.start_point[0]][name_node.start_point[1]:name_node.end_point[1]]
                    full_name = f"{parent_class}.{mname}" if parent_class else mname
                    symbols.append(
                        ParsedSymbol(
                            name=full_name,
                            symbol_type=SymbolType.METHOD,
                            start_line=node.start_point[0] + 1,
                            end_line=node.end_point[0] + 1,
                            signature=lines[node.start_point[0]].strip(),
                        )
                    )
                    return

        # Recurse through all children
        for child in node.children:
            cls._traverse_node(child, lines, language, symbols, parent_class=parent_class)

    @staticmethod
    def _extract_python_docstring(node: Node, lines: List[str]) -> Optional[str]:
        """Extract docstring expression from Python function or class body."""
        body_node = node.child_by_field_name("body")
        if not body_node:
            return None
        for child in body_node.children:
            if child.type == "expression_statement":
                for subchild in child.children:
                    if subchild.type == "string":
                        start_line = subchild.start_point[0]
                        end_line = subchild.end_point[0]
                        raw_doc = "\n".join(lines[start_line : end_line + 1]).strip()
                        doc = re.sub(r'^(?:"""|\'\'\'|["\'])\s*', '', raw_doc)
                        doc = re.sub(r'\s*(?:"""|\'\'\'|["\'])$', '', doc).strip()
                        return doc
            elif child.type != "comment":
                break
        return None
