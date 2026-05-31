"""JavaScript/TypeScript AST parser using Tree-sitter.

Extracts functions, classes, arrow functions, imports, and call edges
from .js, .mjs, .cjs, .ts, .tsx files.
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Optional

import tree_sitter_javascript as ts_js
from tree_sitter import Language, Parser, Node

from codelens.indexer.models import (
    CodeEdge,
    CodeNode,
    EdgeType,
    NodeType,
    ParseResult,
)

logger = logging.getLogger(__name__)

JS_LANGUAGE = Language(ts_js.language())


def _make_parser() -> Parser:
    return Parser(JS_LANGUAGE)


def _text(node: Node, src: bytes) -> str:
    return src[node.start_byte:node.end_byte].decode("utf-8", errors="replace")


def _file_hash(src: bytes) -> str:
    return hashlib.sha256(src).hexdigest()


def _extract_name(node: Node, src: bytes) -> Optional[str]:
    """Try to get a meaningful name from various node types."""
    name_node = node.child_by_field_name("name")
    if name_node:
        return _text(name_node, src)
    return None


class JavaScriptParser:
    """Parses a single JavaScript/TypeScript file."""

    def __init__(self) -> None:
        self._parser = _make_parser()

    def parse_file(self, filepath: Path, repo_root: Path) -> ParseResult:
        src = filepath.read_bytes()
        relative = str(filepath.relative_to(repo_root))
        tree = self._parser.parse(src)
        root = tree.root_node

        result = ParseResult(filepath=relative)
        fhash = _file_hash(src)

        file_uid = relative
        file_node = CodeNode(
            uid=file_uid,
            name=filepath.name,
            qualified_name=filepath.name,
            node_type=NodeType.FILE,
            filepath=relative,
            start_line=1,
            end_line=src.count(b"\n") + 1,
            file_hash=fhash,
        )
        result.nodes.append(file_node)

        self._walk_statements(root.children, src, relative, fhash, file_uid, relative, result)
        return result

    # ── Top-level walker ──────────────────────────────────────────────────────

    def _walk_statements(
        self,
        nodes: list[Node],
        src: bytes,
        filepath: str,
        fhash: str,
        parent_uid: str,
        parent_qualified: str,
        result: ParseResult,
    ) -> None:
        for node in nodes:
            t = node.type

            if t == "function_declaration":
                self._handle_function(node, src, filepath, fhash, parent_uid, parent_qualified, result)

            elif t == "class_declaration":
                self._handle_class(node, src, filepath, fhash, parent_uid, parent_qualified, result)

            elif t in ("lexical_declaration", "variable_declaration"):
                # const foo = () => {} or const foo = function() {}
                self._handle_variable_decl(node, src, filepath, fhash, parent_uid, parent_qualified, result)

            elif t in ("import_declaration", "import_statement"):
                self._handle_import(node, src, filepath, result)

            elif t == "expression_statement":
                # require() calls, foo(), etc.
                self._visit_expr(node, src, filepath, parent_uid, result)

            else:
                self._visit_expr(node, src, filepath, parent_uid, result)

    # ── Function declaration ──────────────────────────────────────────────────

    def _handle_function(
        self,
        node: Node,
        src: bytes,
        filepath: str,
        fhash: str,
        parent_uid: str,
        parent_qualified: str,
        result: ParseResult,
        override_name: str | None = None,
    ) -> str | None:
        name = override_name or _extract_name(node, src)
        if not name:
            return None

        qualified = f"{parent_qualified}.{name}"
        uid = f"{filepath}:{qualified}"

        # Build signature: "function name(params)"
        params_node = node.child_by_field_name("parameters")
        params_text = _text(params_node, src) if params_node else "()"
        signature = f"function {name}{params_text}"

        func_node = CodeNode(
            uid=uid,
            name=name,
            qualified_name=qualified,
            node_type=NodeType.FUNCTION,
            filepath=filepath,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            signature=signature,
            file_hash=fhash,
        )
        result.nodes.append(func_node)
        result.edges.append(CodeEdge(
            source_uid=parent_uid,
            target_uid=uid,
            edge_type=EdgeType.CONTAINS,
            filepath=filepath,
        ))

        body = node.child_by_field_name("body")
        if body:
            self._walk_statements(body.children, src, filepath, fhash, uid, qualified, result)

        return uid

    # ── Arrow / function expression ───────────────────────────────────────────

    def _handle_arrow_or_func_expr(
        self,
        node: Node,
        src: bytes,
        filepath: str,
        fhash: str,
        parent_uid: str,
        parent_qualified: str,
        result: ParseResult,
        name: str,
    ) -> None:
        qualified = f"{parent_qualified}.{name}"
        uid = f"{filepath}:{qualified}"

        params_node = node.child_by_field_name("parameters") or node.child_by_field_name("parameter")
        params_text = _text(params_node, src) if params_node else "()"
        is_arrow = node.type == "arrow_function"
        signature = f"const {name} = {params_text} =>" if is_arrow else f"const {name} = function{params_text}"

        func_node = CodeNode(
            uid=uid,
            name=name,
            qualified_name=qualified,
            node_type=NodeType.FUNCTION,
            filepath=filepath,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            signature=signature,
            file_hash=fhash,
        )
        result.nodes.append(func_node)
        result.edges.append(CodeEdge(
            source_uid=parent_uid,
            target_uid=uid,
            edge_type=EdgeType.CONTAINS,
            filepath=filepath,
        ))

        body = node.child_by_field_name("body")
        if body:
            children = body.children if body.type == "statement_block" else [body]
            self._walk_statements(children, src, filepath, fhash, uid, qualified, result)

    # ── Variable declaration (const foo = ...) ───────────────────────────────

    def _handle_variable_decl(
        self,
        node: Node,
        src: bytes,
        filepath: str,
        fhash: str,
        parent_uid: str,
        parent_qualified: str,
        result: ParseResult,
    ) -> None:
        for declarator in node.children:
            if declarator.type != "variable_declarator":
                continue
            name_node = declarator.child_by_field_name("name")
            value_node = declarator.child_by_field_name("value")
            if not name_node or not value_node:
                continue
            name = _text(name_node, src)
            if value_node.type in ("arrow_function", "function_expression", "function"):
                self._handle_arrow_or_func_expr(
                    value_node, src, filepath, fhash, parent_uid, parent_qualified, result, name
                )
            elif value_node.type == "class":
                self._handle_class_body(
                    value_node, src, filepath, fhash, parent_uid, parent_qualified, result, name
                )

    # ── Class ─────────────────────────────────────────────────────────────────

    def _handle_class(
        self,
        node: Node,
        src: bytes,
        filepath: str,
        fhash: str,
        parent_uid: str,
        parent_qualified: str,
        result: ParseResult,
    ) -> None:
        name = _extract_name(node, src)
        if not name:
            return
        self._handle_class_body(node, src, filepath, fhash, parent_uid, parent_qualified, result, name)

    def _handle_class_body(
        self,
        node: Node,
        src: bytes,
        filepath: str,
        fhash: str,
        parent_uid: str,
        parent_qualified: str,
        result: ParseResult,
        name: str,
    ) -> None:
        qualified = f"{parent_qualified}.{name}"
        uid = f"{filepath}:{qualified}"

        # Check for extends
        heritage = node.child_by_field_name("heritage")
        superclass = None
        if not heritage:
            # tree-sitter-javascript uses class_heritage
            for child in node.children:
                if child.type == "class_heritage":
                    heritage = child
                    break
        if heritage:
            for child in heritage.children:
                if child.type == "identifier":
                    superclass = _text(child, src)
                    break

        class_node = CodeNode(
            uid=uid,
            name=name,
            qualified_name=qualified,
            node_type=NodeType.CLASS,
            filepath=filepath,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            file_hash=fhash,
        )
        result.nodes.append(class_node)
        result.edges.append(CodeEdge(
            source_uid=parent_uid,
            target_uid=uid,
            edge_type=EdgeType.CONTAINS,
            filepath=filepath,
        ))

        if superclass:
            result.edges.append(CodeEdge(
                source_uid=uid,
                target_uid=f"unresolved:{superclass}",
                edge_type=EdgeType.EXTENDS,
                filepath=filepath,
                line=node.start_point[0] + 1,
            ))

        body = node.child_by_field_name("body")
        if body:
            for member in body.children:
                if member.type == "method_definition":
                    self._handle_method(member, src, filepath, fhash, uid, qualified, result)

    def _handle_method(
        self,
        node: Node,
        src: bytes,
        filepath: str,
        fhash: str,
        parent_uid: str,
        parent_qualified: str,
        result: ParseResult,
    ) -> None:
        name_node = node.child_by_field_name("name")
        if not name_node:
            return
        method_name = _text(name_node, src)
        qualified = f"{parent_qualified}.{method_name}"
        uid = f"{filepath}:{qualified}"

        params_node = node.child_by_field_name("parameters") or node.child_by_field_name("value")
        params_text = ""
        if params_node and params_node.type == "formal_parameters":
            params_text = _text(params_node, src)
        signature = f"{method_name}{params_text}"

        ntype = NodeType.CONSTRUCTOR if method_name == "constructor" else NodeType.FUNCTION
        func_node = CodeNode(
            uid=uid,
            name=method_name,
            qualified_name=qualified,
            node_type=ntype,
            filepath=filepath,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            signature=signature,
            file_hash=fhash,
        )
        result.nodes.append(func_node)
        result.edges.append(CodeEdge(
            source_uid=parent_uid,
            target_uid=uid,
            edge_type=EdgeType.CONTAINS,
            filepath=filepath,
        ))

        value_node = node.child_by_field_name("value")
        if value_node and value_node.type == "function_expression":
            body = value_node.child_by_field_name("body")
            if body:
                self._walk_statements(body.children, src, filepath, fhash, uid, qualified, result)

    # ── Import ────────────────────────────────────────────────────────────────

    def _handle_import(self, node: Node, src: bytes, filepath: str, result: ParseResult) -> None:
        source_node = node.child_by_field_name("source")
        if source_node:
            mod = _text(source_node, src).strip("'\"")
            result.edges.append(CodeEdge(
                source_uid=filepath,
                target_uid=f"import:{mod}",
                edge_type=EdgeType.IMPORTS,
                filepath=filepath,
                line=node.start_point[0] + 1,
            ))

    # ── Call / expression visitor ─────────────────────────────────────────────

    def _visit_expr(
        self,
        node: Node,
        src: bytes,
        filepath: str,
        parent_uid: str,
        result: ParseResult,
    ) -> None:
        if node.type == "call_expression":
            func_node = node.child_by_field_name("function")
            if func_node:
                call_name = _text(func_node, src)
                # require("...") → import edge
                if call_name == "require":
                    args = node.child_by_field_name("arguments")
                    if args:
                        for arg in args.children:
                            if arg.type == "string":
                                mod = _text(arg, src).strip("'\"")
                                result.edges.append(CodeEdge(
                                    source_uid=parent_uid,
                                    target_uid=f"import:{mod}",
                                    edge_type=EdgeType.IMPORTS,
                                    filepath=filepath,
                                    line=node.start_point[0] + 1,
                                ))
                                return
                else:
                    result.edges.append(CodeEdge(
                        source_uid=parent_uid,
                        target_uid=f"unresolved:{call_name}",
                        edge_type=EdgeType.CALLS,
                        filepath=filepath,
                        line=node.start_point[0] + 1,
                    ))

        for child in node.children:
            self._visit_expr(child, src, filepath, parent_uid, result)
