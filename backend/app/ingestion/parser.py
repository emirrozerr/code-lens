"""Tree-sitter AST parser stub.

Parses Python and TypeScript source files and extracts nodes:
  File, Module, Class, Function, ConditionalBranch, ReturnStatement

and edges:
  calls, imports, defines, contains, returns
"""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class CodeNode:
    id: str
    kind: str  # File | Module | Class | Function | ConditionalBranch | ReturnStatement
    name: str
    file_path: str
    start_line: int
    end_line: int


@dataclass
class CodeEdge:
    source_id: str
    target_id: str
    kind: str  # calls | imports | defines | contains | returns


@dataclass
class ParseResult:
    nodes: list[CodeNode] = field(default_factory=list)
    edges: list[CodeEdge] = field(default_factory=list)


def parse_file(path: Path) -> ParseResult:
    """Parse a single source file and return extracted nodes and edges.

    TODO: Implement using tree-sitter for Python and TypeScript.
    """
    return ParseResult()


def parse_repository(repo_path: Path, languages: list[str] | None = None) -> ParseResult:
    """Recursively parse all supported source files in a repository.

    TODO: Walk repo_path, call parse_file per file, merge results.
    """
    return ParseResult()
