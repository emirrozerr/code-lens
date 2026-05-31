"""TypeScript/TSX parser — thin wrapper over JavaScriptParser with TS grammar."""

from __future__ import annotations

from pathlib import Path

import tree_sitter_typescript as ts_ts
from tree_sitter import Language, Parser

from codelens.indexer.javascript_parser import JavaScriptParser
from codelens.indexer.models import ParseResult

TS_LANGUAGE = Language(ts_ts.language_typescript())
TSX_LANGUAGE = Language(ts_ts.language_tsx())


class TypeScriptParser(JavaScriptParser):
    """Parses .ts files using the TypeScript tree-sitter grammar."""

    def __init__(self) -> None:
        # Don't call super().__init__() — we override the parser per file
        pass

    def parse_file(self, filepath: Path, repo_root: Path) -> ParseResult:
        lang = TSX_LANGUAGE if filepath.suffix.lower() == ".tsx" else TS_LANGUAGE
        self._parser = Parser(lang)
        return super().parse_file(filepath, repo_root)
