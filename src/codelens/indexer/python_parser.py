"""Python AST parser using Tree-sitter.

Walks a Python source file's AST and extracts CodeNode and CodeEdge entities
that represent the file's structural elements and their relationships.
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Optional

import tree_sitter_python as ts_python
from tree_sitter import Language, Parser, Node

from codelens.indexer.models import (
    CodeEdge,
    CodeNode,
    EdgeType,
    NodeType,
    ParseResult,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Language setup (cached at module level)
# ---------------------------------------------------------------------------

PYTHON_LANGUAGE = Language(ts_python.language())


def _make_parser() -> Parser:
    """Create a Tree-sitter parser configured for Python."""
    parser = Parser(PYTHON_LANGUAGE)
    return parser


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _node_text(node: Node, source: bytes) -> str:
    """Extract the UTF-8 text for a Tree-sitter node."""
    if not node:
        return ""
    return source[node.start_byte:node.end_byte].decode("utf-8", errors="replace")


def _file_hash(source: bytes) -> str:
    """SHA-256 hex digest of the raw source bytes."""
    return hashlib.sha256(source).hexdigest()


def _extract_docstring(body: Node, source: bytes) -> Optional[str]:
    """Look for a docstring at the top of a class or function body."""
    # The first child of a block is usually an expression_statement containing a string
    if body and body.type == "block" and len(body.children) > 0:
        first = body.children[0]
        if first.type == "expression_statement" and first.children[0].type == "string":
            return _node_text(first.children[0], source).strip('\'"')
    return None


def _extract_signature(node: Node, source: bytes) -> Optional[str]:
    """Extract the function signature (everything before the body)."""
    body = node.child_by_field_name("body")
    if body:
        sig_bytes = source[node.start_byte:body.start_byte]
        sig = sig_bytes.decode("utf-8", errors="replace").strip()
        # Remove trailing colon
        if sig.endswith(":"):
            sig = sig[:-1].strip()
        return sig
    return None


# ---------------------------------------------------------------------------
# Main parser class
# ---------------------------------------------------------------------------


class PythonParser:
    """Parses a single Python file and extracts code graph entities."""

    def __init__(self) -> None:
        self._parser = _make_parser()

    def parse_file(self, filepath: Path, repo_root: Path) -> ParseResult:
        """Parse a single Python file and return structured extraction results."""
        source = filepath.read_bytes()
        relative = str(filepath.relative_to(repo_root))
        tree = self._parser.parse(source)
        root = tree.root_node

        result = ParseResult(filepath=relative)
        fhash = _file_hash(source)

        file_node = CodeNode(
            uid=relative,
            name=filepath.name,
            qualified_name=filepath.name,
            node_type=NodeType.FILE,
            filepath=relative,
            start_line=1,
            end_line=source.count(b"\n") + 1,
            file_hash=fhash,
        )
        result.nodes.append(file_node)

        # Walk top-level declarations
        for child in root.children:
            if child.type == "class_definition":
                self._walk_class(child, source, relative, fhash, file_node.uid, relative, result)
            elif child.type == "function_definition":
                self._walk_function(child, source, relative, fhash, file_node.uid, relative, result)
            elif child.type in ("import_statement", "import_from_statement"):
                self._extract_import(child, source, relative, result)
            else:
                self._visit_statement(child, source, relative, file_node.uid, result)

        if root.has_error:
            result.errors.append(f"Tree-sitter reported syntax errors in {relative}")

        return result

    # -----------------------------------------------------------------------
    # Import extraction
    # -----------------------------------------------------------------------

    def _extract_import(
        self,
        node: Node,
        source: bytes,
        filepath: str,
        result: ParseResult,
    ) -> None:
        """Extract import/from-import statement."""
        if node.type == "import_statement":
            # e.g. import os, sys
            for child in node.children:
                if child.type == "dotted_name" or child.type == "aliased_import":
                    target = _node_text(child, source).split(" as ")[0].strip()
                    self._add_import_edge(filepath, target, node.start_point[0] + 1, result)
        elif node.type == "import_from_statement":
            # e.g. from x import y
            module_name_node = node.child_by_field_name("module_name")
            if module_name_node:
                mod_name = _node_text(module_name_node, source)
                # Just connect to the module name
                self._add_import_edge(filepath, mod_name, node.start_point[0] + 1, result)

    def _add_import_edge(self, filepath: str, target: str, line: int, result: ParseResult):
        result.edges.append(
            CodeEdge(
                source_uid=filepath,
                target_uid=f"import:{target}",
                edge_type=EdgeType.IMPORTS,
                filepath=filepath,
                line=line,
            )
        )

    # -----------------------------------------------------------------------
    # Class walking
    # -----------------------------------------------------------------------

    def _walk_class(
        self,
        node: Node,
        source: bytes,
        filepath: str,
        fhash: str,
        parent_uid: str,
        module_path: str,
        result: ParseResult,
    ) -> None:
        """Extract a class definition and its members."""
        name_node = node.child_by_field_name("name")
        if not name_node:
            return
        class_name = _node_text(name_node, source)
        qualified = f"{module_path}:{class_name}"
        uid = f"{filepath}:{qualified}"

        body = node.child_by_field_name("body")
        docstring = _extract_docstring(body, source) if body else None

        class_node = CodeNode(
            uid=uid,
            name=class_name,
            qualified_name=qualified,
            node_type=NodeType.CLASS,
            filepath=filepath,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            docstring=docstring,
            file_hash=fhash,
        )
        result.nodes.append(class_node)
        result.edges.append(
            CodeEdge(
                source_uid=parent_uid,
                target_uid=uid,
                edge_type=EdgeType.CONTAINS,
                filepath=filepath,
            )
        )

        superclasses = node.child_by_field_name("superclasses")
        if superclasses:
            for child in superclasses.children:
                if child.type in ("identifier", "attribute"):
                    parent_name = _node_text(child, source)
                    result.edges.append(
                        CodeEdge(
                            source_uid=uid,
                            target_uid=f"unresolved:{parent_name}",
                            edge_type=EdgeType.EXTENDS,
                            filepath=filepath,
                            line=child.start_point[0] + 1,
                        )
                    )

        if body:
            self._walk_block(body, source, filepath, fhash, uid, qualified, result)

    def _walk_block(
        self,
        body: Node,
        source: bytes,
        filepath: str,
        fhash: str,
        parent_uid: str,
        parent_qualified: str,
        result: ParseResult,
    ) -> None:
        """Walk the body of a class or function."""
        for member in body.children:
            if member.type == "function_definition":
                self._walk_function(member, source, filepath, fhash, parent_uid, parent_qualified, result)
            elif member.type == "class_definition":
                self._walk_class(member, source, filepath, fhash, parent_uid, parent_qualified, result)
            else:
                self._visit_statement(member, source, filepath, parent_uid, result)

    # -----------------------------------------------------------------------
    # Function walking
    # -----------------------------------------------------------------------

    def _walk_function(
        self,
        node: Node,
        source: bytes,
        filepath: str,
        fhash: str,
        parent_uid: str,
        parent_qualified: str,
        result: ParseResult,
    ) -> None:
        name_node = node.child_by_field_name("name")
        if not name_node:
            return

        func_name = _node_text(name_node, source)
        qualified = f"{parent_qualified}.{func_name}"
        uid = f"{filepath}:{qualified}"

        body = node.child_by_field_name("body")
        docstring = _extract_docstring(body, source) if body else None

        ntype = NodeType.CONSTRUCTOR if func_name == "__init__" else NodeType.FUNCTION

        func_node = CodeNode(
            uid=uid,
            name=func_name,
            qualified_name=qualified,
            node_type=ntype,
            filepath=filepath,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            docstring=docstring,
            signature=_extract_signature(node, source),
            file_hash=fhash,
        )
        result.nodes.append(func_node)
        result.edges.append(
            CodeEdge(
                source_uid=parent_uid,
                target_uid=uid,
                edge_type=EdgeType.CONTAINS,
                filepath=filepath,
            )
        )

        if body:
            self._walk_block(body, source, filepath, fhash, uid, qualified, result)

    # -----------------------------------------------------------------------
    # Statement / Call walking
    # -----------------------------------------------------------------------

    def _visit_statement(
        self,
        node: Node,
        source: bytes,
        filepath: str,
        parent_uid: str,
        result: ParseResult,
    ) -> None:
        if node.type == "call":
            self._extract_call(node, source, filepath, parent_uid, result)
            return

        if node.type in ("if_statement", "for_statement", "while_statement", "match_statement"):
            branch_uid = f"{parent_uid}:branch@L{node.start_point[0] + 1}"
            branch_node = CodeNode(
                uid=branch_uid,
                name=f"{node.type}@L{node.start_point[0] + 1}",
                qualified_name=branch_uid.split(":", 1)[1] if ":" in branch_uid else branch_uid,
                node_type=NodeType.CONDITIONAL_BRANCH,
                filepath=filepath,
                start_line=node.start_point[0] + 1,
                end_line=node.end_point[0] + 1,
            )
            result.nodes.append(branch_node)
            result.edges.append(
                CodeEdge(
                    source_uid=parent_uid,
                    target_uid=branch_uid,
                    edge_type=EdgeType.HAS_BRANCH,
                    filepath=filepath,
                    line=node.start_point[0] + 1,
                )
            )

        if node.type == "return_statement":
            ret_uid = f"{parent_uid}:return@L{node.start_point[0] + 1}"
            ret_node = CodeNode(
                uid=ret_uid,
                name="return",
                qualified_name=ret_uid.split(":", 1)[1] if ":" in ret_uid else ret_uid,
                node_type=NodeType.RETURN_STATEMENT,
                filepath=filepath,
                start_line=node.start_point[0] + 1,
                end_line=node.end_point[0] + 1,
            )
            result.nodes.append(ret_node)
            result.edges.append(
                CodeEdge(
                    source_uid=parent_uid,
                    target_uid=ret_uid,
                    edge_type=EdgeType.RETURNS,
                    filepath=filepath,
                    line=node.start_point[0] + 1,
                )
            )

        for child in node.children:
            self._visit_statement(child, source, filepath, parent_uid, result)

    def _extract_call(
        self,
        node: Node,
        source: bytes,
        filepath: str,
        parent_uid: str,
        result: ParseResult,
    ) -> None:
        function_node = node.child_by_field_name("function")
        if function_node:
            call_text = _node_text(function_node, source)
            target = f"unresolved:{call_text}"
            result.edges.append(
                CodeEdge(
                    source_uid=parent_uid,
                    target_uid=target,
                    edge_type=EdgeType.CALLS,
                    filepath=filepath,
                    line=node.start_point[0] + 1,
                )
            )

        args = node.child_by_field_name("arguments")
        if args:
            for arg in args.children:
                self._visit_statement(arg, source, filepath, parent_uid, result)
