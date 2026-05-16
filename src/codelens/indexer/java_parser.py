"""Java AST parser using Tree-sitter.

Walks a Java source file's AST and extracts CodeNode and CodeEdge entities
that represent the file's structural elements and their relationships.
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Optional

import tree_sitter_java as ts_java
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

JAVA_LANGUAGE = Language(ts_java.language())


def _make_parser() -> Parser:
    """Create a Tree-sitter parser configured for Java."""
    parser = Parser(JAVA_LANGUAGE)
    return parser


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _node_text(node: Node, source: bytes) -> str:
    """Extract the UTF-8 text for a Tree-sitter node."""
    return source[node.start_byte:node.end_byte].decode("utf-8", errors="replace")


def _file_hash(source: bytes) -> str:
    """SHA-256 hex digest of the raw source bytes."""
    return hashlib.sha256(source).hexdigest()


def _find_docstring(node: Node, source: bytes) -> Optional[str]:
    """Look for a Javadoc block comment immediately before a declaration node."""
    prev = node.prev_named_sibling
    if prev and prev.type == "block_comment":
        text = _node_text(prev, source)
        if text.startswith("/**"):
            # Strip the comment markers
            lines = text.split("\n")
            cleaned = []
            for line in lines:
                line = line.strip()
                if line.startswith("/**"):
                    line = line[3:].strip()
                elif line.startswith("*/"):
                    continue
                elif line.startswith("*"):
                    line = line[1:].strip()
                if line:
                    cleaned.append(line)
            return "\n".join(cleaned) if cleaned else None
    return None


def _extract_signature(node: Node, source: bytes) -> Optional[str]:
    """Extract the method/constructor signature (everything before the body)."""
    body = node.child_by_field_name("body")
    if body:
        sig_bytes = source[node.start_byte:body.start_byte]
        return sig_bytes.decode("utf-8", errors="replace").strip()
    return None


def _find_child_by_type(node: Node, type_name: str) -> Optional[Node]:
    """Find the first direct child with a given type."""
    for child in node.children:
        if child.type == type_name:
            return child
    return None


def _find_children_by_type(node: Node, type_name: str) -> list[Node]:
    """Find all direct children with a given type."""
    return [c for c in node.children if c.type == type_name]


# ---------------------------------------------------------------------------
# Main parser class
# ---------------------------------------------------------------------------


class JavaParser:
    """Parses a single Java file and extracts code graph entities."""

    def __init__(self) -> None:
        self._parser = _make_parser()

    def parse_file(self, filepath: Path, repo_root: Path) -> ParseResult:
        """Parse a single Java file and return structured extraction results.

        Args:
            filepath: Absolute path to the .java file.
            repo_root: Absolute path to the repository root (for relative paths).

        Returns:
            ParseResult with all extracted nodes and edges.
        """
        source = filepath.read_bytes()
        relative = str(filepath.relative_to(repo_root))
        tree = self._parser.parse(source)
        root = tree.root_node

        result = ParseResult(filepath=relative)
        fhash = _file_hash(source)

        # Create File node
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

        # Extract package declaration
        package_name = self._extract_package(root, source)

        # Walk top-level declarations
        for child in root.children:
            if child.type == "class_declaration":
                self._walk_class(
                    child, source, relative, fhash, file_node.uid,
                    package_name, result,
                )
            elif child.type == "interface_declaration":
                self._walk_interface(
                    child, source, relative, fhash, file_node.uid,
                    package_name, result,
                )
            elif child.type == "import_declaration":
                self._extract_import(child, source, relative, result)

        # Check for syntax errors in the tree
        if root.has_error:
            result.errors.append(f"Tree-sitter reported syntax errors in {relative}")

        return result

    # -----------------------------------------------------------------------
    # Package extraction
    # -----------------------------------------------------------------------

    def _extract_package(self, root: Node, source: bytes) -> Optional[str]:
        """Extract the package name from the AST root."""
        for child in root.children:
            if child.type == "package_declaration":
                # The scoped identifier is the package name
                for c in child.children:
                    if c.type in ("scoped_identifier", "identifier"):
                        return _node_text(c, source)
        return None

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
        """Extract an import statement as an edge."""
        for child in node.children:
            if child.type in ("scoped_identifier", "identifier"):
                import_target = _node_text(child, source)
                result.edges.append(
                    CodeEdge(
                        source_uid=filepath,
                        target_uid=f"import:{import_target}",
                        edge_type=EdgeType.IMPORTS,
                        filepath=filepath,
                        line=node.start_point[0] + 1,
                    )
                )
                break

    # -----------------------------------------------------------------------
    # Class / Interface walking
    # -----------------------------------------------------------------------

    def _walk_class(
        self,
        node: Node,
        source: bytes,
        filepath: str,
        fhash: str,
        parent_uid: str,
        package_name: Optional[str],
        result: ParseResult,
    ) -> None:
        """Extract a class declaration and all its members."""
        name_node = node.child_by_field_name("name")
        if not name_node:
            return
        class_name = _node_text(name_node, source)
        qualified = f"{package_name}.{class_name}" if package_name else class_name
        uid = f"{filepath}:{qualified}"

        class_node = CodeNode(
            uid=uid,
            name=class_name,
            qualified_name=qualified,
            node_type=NodeType.CLASS,
            filepath=filepath,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            docstring=_find_docstring(node, source),
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

        # Check for extends / implements
        superclass = node.child_by_field_name("superclass")
        if superclass:
            # superclass node wraps the type identifier
            for child in superclass.children:
                if child.type in ("type_identifier", "scoped_type_identifier"):
                    extends_name = _node_text(child, source)
                    result.edges.append(
                        CodeEdge(
                            source_uid=uid,
                            target_uid=f"unresolved:{extends_name}",
                            edge_type=EdgeType.EXTENDS,
                            filepath=filepath,
                            line=child.start_point[0] + 1,
                        )
                    )

        interfaces = node.child_by_field_name("interfaces")
        if interfaces:
            for child in interfaces.children:
                if child.type in ("type_identifier", "scoped_type_identifier"):
                    impl_name = _node_text(child, source)
                    result.edges.append(
                        CodeEdge(
                            source_uid=uid,
                            target_uid=f"unresolved:{impl_name}",
                            edge_type=EdgeType.IMPLEMENTS,
                            filepath=filepath,
                            line=child.start_point[0] + 1,
                        )
                    )

        # Walk class body members
        body = node.child_by_field_name("body")
        if body:
            self._walk_class_body(body, source, filepath, fhash, uid, package_name, result)

    def _walk_interface(
        self,
        node: Node,
        source: bytes,
        filepath: str,
        fhash: str,
        parent_uid: str,
        package_name: Optional[str],
        result: ParseResult,
    ) -> None:
        """Extract an interface declaration."""
        name_node = node.child_by_field_name("name")
        if not name_node:
            return
        iface_name = _node_text(name_node, source)
        qualified = f"{package_name}.{iface_name}" if package_name else iface_name
        uid = f"{filepath}:{qualified}"

        iface_node = CodeNode(
            uid=uid,
            name=iface_name,
            qualified_name=qualified,
            node_type=NodeType.INTERFACE,
            filepath=filepath,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            docstring=_find_docstring(node, source),
            file_hash=fhash,
        )
        result.nodes.append(iface_node)
        result.edges.append(
            CodeEdge(
                source_uid=parent_uid,
                target_uid=uid,
                edge_type=EdgeType.CONTAINS,
                filepath=filepath,
            )
        )

        # Walk interface body for method signatures
        body = node.child_by_field_name("body")
        if body:
            self._walk_class_body(body, source, filepath, fhash, uid, package_name, result)

    def _walk_class_body(
        self,
        body: Node,
        source: bytes,
        filepath: str,
        fhash: str,
        class_uid: str,
        package_name: Optional[str],
        result: ParseResult,
    ) -> None:
        """Walk the body of a class or interface, extracting members."""
        for member in body.children:
            if member.type == "method_declaration":
                self._walk_method(
                    member, source, filepath, fhash, class_uid, result,
                )
            elif member.type == "constructor_declaration":
                self._walk_constructor(
                    member, source, filepath, fhash, class_uid, result,
                )
            elif member.type == "class_declaration":
                # Inner class
                self._walk_class(
                    member, source, filepath, fhash, class_uid,
                    package_name, result,
                )

    # -----------------------------------------------------------------------
    # Method / Constructor walking
    # -----------------------------------------------------------------------

    def _walk_method(
        self,
        node: Node,
        source: bytes,
        filepath: str,
        fhash: str,
        class_uid: str,
        result: ParseResult,
    ) -> None:
        """Extract a method and its internal structure."""
        name_node = node.child_by_field_name("name")
        if not name_node:
            return

        method_name = _node_text(name_node, source)
        # Build qualified name from class uid
        class_qualified = class_uid.split(":", 1)[1] if ":" in class_uid else class_uid
        qualified = f"{class_qualified}.{method_name}"
        uid = f"{filepath}:{qualified}"

        method_node = CodeNode(
            uid=uid,
            name=method_name,
            qualified_name=qualified,
            node_type=NodeType.FUNCTION,
            filepath=filepath,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            docstring=_find_docstring(node, source),
            signature=_extract_signature(node, source),
            file_hash=fhash,
        )
        result.nodes.append(method_node)
        result.edges.append(
            CodeEdge(
                source_uid=class_uid,
                target_uid=uid,
                edge_type=EdgeType.CONTAINS,
                filepath=filepath,
            )
        )

        # Walk method body for calls, conditionals, returns
        body = node.child_by_field_name("body")
        if body:
            self._walk_method_body(body, source, filepath, uid, result)

    def _walk_constructor(
        self,
        node: Node,
        source: bytes,
        filepath: str,
        fhash: str,
        class_uid: str,
        result: ParseResult,
    ) -> None:
        """Extract a constructor declaration."""
        name_node = node.child_by_field_name("name")
        if not name_node:
            return

        ctor_name = _node_text(name_node, source)
        class_qualified = class_uid.split(":", 1)[1] if ":" in class_uid else class_uid
        qualified = f"{class_qualified}.{ctor_name}"
        uid = f"{filepath}:{qualified}"

        ctor_node = CodeNode(
            uid=uid,
            name=ctor_name,
            qualified_name=qualified,
            node_type=NodeType.CONSTRUCTOR,
            filepath=filepath,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            docstring=_find_docstring(node, source),
            signature=_extract_signature(node, source),
            file_hash=fhash,
        )
        result.nodes.append(ctor_node)
        result.edges.append(
            CodeEdge(
                source_uid=class_uid,
                target_uid=uid,
                edge_type=EdgeType.CONTAINS,
                filepath=filepath,
            )
        )

        # Walk constructor body
        body = node.child_by_field_name("body")
        if body:
            self._walk_method_body(body, source, filepath, uid, result)

    # -----------------------------------------------------------------------
    # Method body walking (calls, conditionals, returns)
    # -----------------------------------------------------------------------

    def _walk_method_body(
        self,
        node: Node,
        source: bytes,
        filepath: str,
        method_uid: str,
        result: ParseResult,
    ) -> None:
        """Recursively walk a method body extracting calls, conditionals, returns."""
        for child in node.children:
            self._visit_statement(child, source, filepath, method_uid, result)

    def _visit_statement(
        self,
        node: Node,
        source: bytes,
        filepath: str,
        method_uid: str,
        result: ParseResult,
    ) -> None:
        """Visit a statement node, extracting interesting constructs."""
        # --- Method invocations ---
        if node.type == "method_invocation":
            self._extract_call(node, source, filepath, method_uid, result)
            # _extract_call handles recursion into arguments, so don't recurse here
            return

        # --- Object creation (new Foo()) ---
        if node.type == "object_creation_expression":
            type_node = node.child_by_field_name("type")
            if type_node:
                type_name = _node_text(type_node, source)
                result.edges.append(
                    CodeEdge(
                        source_uid=method_uid,
                        target_uid=f"unresolved:{type_name}.<init>",
                        edge_type=EdgeType.CALLS,
                        filepath=filepath,
                        line=node.start_point[0] + 1,
                    )
                )
            # Recurse into arguments of the constructor call
            args = node.child_by_field_name("arguments")
            if args:
                for arg in args.children:
                    self._visit_statement(arg, source, filepath, method_uid, result)
            return

        # --- Conditional branches ---
        if node.type in ("if_statement", "switch_expression", "switch_statement"):
            self._extract_conditional(node, source, filepath, method_uid, result)
            return

        # --- Return statements ---
        if node.type == "return_statement":
            ret_uid = f"{method_uid}:return@L{node.start_point[0] + 1}"
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
                    source_uid=method_uid,
                    target_uid=ret_uid,
                    edge_type=EdgeType.RETURNS,
                    filepath=filepath,
                    line=node.start_point[0] + 1,
                )
            )

        # Recurse into all children
        for child in node.children:
            self._visit_statement(child, source, filepath, method_uid, result)

    def _extract_call(
        self,
        node: Node,
        source: bytes,
        filepath: str,
        method_uid: str,
        result: ParseResult,
    ) -> None:
        """Extract a method call edge."""
        name_node = node.child_by_field_name("name")
        obj_node = node.child_by_field_name("object")

        if name_node:
            call_name = _node_text(name_node, source)
            if obj_node:
                obj_text = _node_text(obj_node, source)
                target = f"unresolved:{obj_text}.{call_name}"
            else:
                target = f"unresolved:{call_name}"

            result.edges.append(
                CodeEdge(
                    source_uid=method_uid,
                    target_uid=target,
                    edge_type=EdgeType.CALLS,
                    filepath=filepath,
                    line=node.start_point[0] + 1,
                )
            )

        # Recurse into arguments for nested calls
        args = node.child_by_field_name("arguments")
        if args:
            for arg in args.children:
                self._visit_statement(arg, source, filepath, method_uid, result)

    def _extract_conditional(
        self,
        node: Node,
        source: bytes,
        filepath: str,
        method_uid: str,
        result: ParseResult,
    ) -> None:
        """Extract conditional branch nodes (if / switch)."""
        condition = node.child_by_field_name("condition")
        condition_text = _node_text(condition, source) if condition else ""
        branch_uid = f"{method_uid}:branch@L{node.start_point[0] + 1}"

        branch_node = CodeNode(
            uid=branch_uid,
            name=f"{node.type}@L{node.start_point[0] + 1}",
            qualified_name=branch_uid.split(":", 1)[1] if ":" in branch_uid else branch_uid,
            node_type=NodeType.CONDITIONAL_BRANCH,
            filepath=filepath,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            docstring=f"Condition: {condition_text}" if condition_text else None,
        )
        result.nodes.append(branch_node)
        result.edges.append(
            CodeEdge(
                source_uid=method_uid,
                target_uid=branch_uid,
                edge_type=EdgeType.HAS_BRANCH,
                filepath=filepath,
                line=node.start_point[0] + 1,
            )
        )

        # Walk the body of the conditional for nested calls/statements
        consequence = node.child_by_field_name("consequence")
        if consequence:
            self._walk_method_body(consequence, source, filepath, method_uid, result)
        alternative = node.child_by_field_name("alternative")
        if alternative:
            self._walk_method_body(alternative, source, filepath, method_uid, result)
        # switch body
        body = node.child_by_field_name("body")
        if body:
            self._walk_method_body(body, source, filepath, method_uid, result)
