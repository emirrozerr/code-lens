"""Repository indexer — walks a repository and parses all supported files.

Orchestrates the parsing pipeline: discovers files, delegates to language-
specific parsers, and collects the combined ParseResult for the entire repo.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path

from codelens.indexer.java_parser import JavaParser
from codelens.indexer.python_parser import PythonParser
from codelens.indexer.models import CodeEdge, CodeNode, EdgeType, NodeType, ParseResult

logger = logging.getLogger(__name__)

# File extensions to their parser
SUPPORTED_EXTENSIONS: dict[str, str] = {
    ".java": "java",
    ".py": "python",
}


class Indexer:
    """Walks a repository directory and indexes all supported source files."""

    def __init__(self) -> None:
        self._java_parser = JavaParser()
        self._python_parser = PythonParser()

    def index_repository(self, repo_path: Path) -> ParseResult:
        """Index an entire repository, returning a combined ParseResult.

        Args:
            repo_path: Absolute path to the repository root.

        Returns:
            A single ParseResult containing all nodes and edges from all files.
        """
        repo_path = repo_path.resolve()
        if not repo_path.is_dir():
            raise ValueError(f"Repository path does not exist or is not a directory: {repo_path}")

        combined = ParseResult(filepath=str(repo_path))
        files_parsed = 0
        files_skipped = 0
        start = time.time()

        for source_file in self._discover_files(repo_path):
            ext = source_file.suffix.lower()
            lang = SUPPORTED_EXTENSIONS.get(ext)

            if lang == "java":
                try:
                    file_result = self._java_parser.parse_file(source_file, repo_path)
                    combined.nodes.extend(file_result.nodes)
                    combined.edges.extend(file_result.edges)
                    combined.errors.extend(file_result.errors)
                    files_parsed += 1
                except Exception as exc:
                    msg = f"Failed to parse {source_file}: {exc}"
                    logger.warning(msg)
                    combined.errors.append(msg)
                    files_skipped += 1
            elif lang == "python":
                try:
                    file_result = self._python_parser.parse_file(source_file, repo_path)
                    combined.nodes.extend(file_result.nodes)
                    combined.edges.extend(file_result.edges)
                    combined.errors.extend(file_result.errors)
                    files_parsed += 1
                except Exception as exc:
                    msg = f"Failed to parse {source_file}: {exc}"
                    logger.warning(msg)
                    combined.errors.append(msg)
                    files_skipped += 1
            else:
                files_skipped += 1

        elapsed = time.time() - start

        # Resolve unresolved call targets where possible
        self._resolve_calls(combined)

        logger.info(
            "Indexing complete: %d files parsed, %d skipped, %d nodes, %d edges (%.2fs)",
            files_parsed,
            files_skipped,
            len(combined.nodes),
            len(combined.edges),
            elapsed,
        )

        return combined

    def index_incremental(
        self,
        repo_path: Path,
        previous_result: ParseResult,
        changed_files: list[Path],
        deleted_files: list[Path],
    ) -> ParseResult:
        """Incrementally update a previous ParseResult with changed/deleted files.

        Args:
            repo_path: Absolute path to the repository root.
            previous_result: The result of the last index run.
            changed_files: List of absolute paths to files that were modified or added.
            deleted_files: List of absolute paths to files that were deleted.

        Returns:
            A new ParseResult with the updated graph state.
        """
        import copy

        repo_path = repo_path.resolve()
        start = time.time()

        # 1. Start with a copy of the previous state
        new_result = copy.deepcopy(previous_result)

        # 2. Determine which relative file paths need to be purged
        files_to_purge = set()
        for f in changed_files + deleted_files:
            try:
                rel = str(f.resolve().relative_to(repo_path))
                files_to_purge.add(rel)
            except ValueError:
                continue

        if not files_to_purge:
            return new_result

        # 3. Remove old nodes and edges from the purged files
        new_result.nodes = [n for n in new_result.nodes if n.filepath not in files_to_purge]
        new_result.edges = [e for e in new_result.edges if e.filepath not in files_to_purge]

        # 4. Parse the newly changed/added files
        files_parsed = 0
        for source_file in changed_files:
            if not source_file.is_file():
                continue
            
            ext = source_file.suffix.lower()
            lang = SUPPORTED_EXTENSIONS.get(ext)

            if lang == "java":
                try:
                    file_result = self._java_parser.parse_file(source_file, repo_path)
                    new_result.nodes.extend(file_result.nodes)
                    new_result.edges.extend(file_result.edges)
                    new_result.errors.extend(file_result.errors)
                    files_parsed += 1
                except Exception as exc:
                    msg = f"Failed to parse {source_file}: {exc}"
                    logger.warning(msg)
                    new_result.errors.append(msg)
            elif lang == "python":
                try:
                    file_result = self._python_parser.parse_file(source_file, repo_path)
                    new_result.nodes.extend(file_result.nodes)
                    new_result.edges.extend(file_result.edges)
                    new_result.errors.extend(file_result.errors)
                    files_parsed += 1
                except Exception as exc:
                    msg = f"Failed to parse {source_file}: {exc}"
                    logger.warning(msg)
                    new_result.errors.append(msg)

        elapsed = time.time() - start

        # 5. Re-resolve calls (since new methods might have been added)
        # Note: we only try to resolve calls that are still marked as "unresolved:"
        self._resolve_calls(new_result)

        logger.info(
            "Incremental update: %d files parsed, %d deleted, %d nodes, %d edges (%.2fs)",
            files_parsed,
            len(deleted_files),
            len(new_result.nodes),
            len(new_result.edges),
            elapsed,
        )

        return new_result

    def _discover_files(self, repo_path: Path):
        """Yield all source files in the repository, skipping hidden dirs and common junk."""
        skip_dirs = {
            ".git", ".svn", ".hg", "node_modules", "__pycache__", ".venv", "venv",
            ".idea", ".vscode", ".settings", "target", "build", "out", "bin",
        }

        for path in repo_path.rglob("*"):
            # Skip hidden and junk directories
            parts = path.relative_to(repo_path).parts
            if any(p in skip_dirs or p.startswith(".") for p in parts[:-1]):
                continue

            if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
                yield path

    def _resolve_calls(self, result: ParseResult) -> None:
        """Attempt to resolve 'unresolved:' target UIDs to real node UIDs.

        Uses a simple name-matching strategy: if the unresolved target ends
        with a method name that matches a known node, link to it.
        """
        # Build lookup: method_name -> list of UIDs
        name_to_uids: dict[str, list[str]] = {}
        for node in result.nodes:
            if node.node_type in (NodeType.FUNCTION, NodeType.CONSTRUCTOR):
                name_to_uids.setdefault(node.name, []).append(node.uid)

        resolved_count = 0
        for edge in result.edges:
            if edge.target_uid.startswith("unresolved:"):
                unresolved_name = edge.target_uid[len("unresolved:"):]
                # Try exact qualified match first
                # e.g. "unresolved:OrderService.calculateTotal" -> look for "calculateTotal"
                method_name = unresolved_name.rsplit(".", 1)[-1]
                # Strip <init> for constructor calls
                if method_name == "<init>":
                    # Try to match the class name as constructor
                    class_name = unresolved_name.rsplit(".", 2)[-2] if "." in unresolved_name else unresolved_name
                    candidates = name_to_uids.get(class_name, [])
                else:
                    candidates = name_to_uids.get(method_name, [])

                if len(candidates) == 1:
                    edge.target_uid = candidates[0]
                    resolved_count += 1
                elif len(candidates) > 1:
                    # Ambiguous — leave as unresolved for now
                    logger.debug(
                        "Ambiguous call resolution for %s: %d candidates",
                        unresolved_name,
                        len(candidates),
                    )

        if resolved_count:
            logger.info("Resolved %d / %d call targets by name matching", resolved_count, len(result.edges))
