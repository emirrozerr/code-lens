"""Data models for code graph nodes and edges extracted by the parser."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Node types
# ---------------------------------------------------------------------------


class NodeType(str, Enum):
    """Types of code entities stored in the graph."""

    FILE = "File"
    PACKAGE = "Package"
    CLASS = "Class"
    INTERFACE = "Interface"
    FUNCTION = "Function"          # methods and standalone functions
    CONSTRUCTOR = "Constructor"
    CONDITIONAL_BRANCH = "ConditionalBranch"
    RETURN_STATEMENT = "ReturnStatement"


# ---------------------------------------------------------------------------
# Edge types
# ---------------------------------------------------------------------------


class EdgeType(str, Enum):
    """Types of relationships between code entities."""

    CONTAINS = "contains"          # File -> Class, Class -> Function, etc.
    CALLS = "calls"                # Function -> Function
    IMPORTS = "imports"            # File -> File  (import statements)
    IMPLEMENTS = "implements"      # Class -> Interface
    EXTENDS = "extends"            # Class -> Class
    RETURNS = "returns"            # Function -> ReturnStatement
    HAS_BRANCH = "has_branch"      # Function -> ConditionalBranch


# ---------------------------------------------------------------------------
# Code node
# ---------------------------------------------------------------------------


class CodeNode(BaseModel):
    """A single code entity extracted from the AST."""

    uid: str = Field(
        ...,
        description="Globally unique identifier: '<filepath>:<qualified_name>'",
    )
    name: str = Field(..., description="Simple name of the symbol (e.g. 'calculateTotal')")
    qualified_name: str = Field(
        ...,
        description="Fully qualified name within the file (e.g. 'OrderService.calculateTotal')",
    )
    node_type: NodeType
    filepath: str = Field(..., description="Relative path from repo root")
    start_line: int
    end_line: int
    docstring: Optional[str] = None
    signature: Optional[str] = Field(
        None,
        description="Method/function signature string (for Function and Constructor nodes)",
    )

    # Metadata for incremental re-indexing
    file_hash: Optional[str] = Field(
        None,
        description="SHA-256 hash of the source file at index time",
    )


# ---------------------------------------------------------------------------
# Code edge
# ---------------------------------------------------------------------------


class CodeEdge(BaseModel):
    """A directed relationship between two code nodes."""

    source_uid: str = Field(..., description="UID of the source node")
    target_uid: str = Field(..., description="UID of the target node")
    edge_type: EdgeType
    filepath: Optional[str] = Field(
        None,
        description="File where this relationship was observed",
    )
    line: Optional[int] = Field(
        None,
        description="Line number where this relationship was observed",
    )


# ---------------------------------------------------------------------------
# Parse result (output of a single file parse)
# ---------------------------------------------------------------------------


class ParseResult(BaseModel):
    """The full extraction result from parsing one source file."""

    filepath: str
    nodes: list[CodeNode] = Field(default_factory=list)
    edges: list[CodeEdge] = Field(default_factory=list)
    errors: list[str] = Field(
        default_factory=list,
        description="Non-fatal parse warnings or errors",
    )
