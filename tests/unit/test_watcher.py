"""Unit tests for incremental indexing and the file watcher daemon."""

import time
from pathlib import Path
from queue import Queue

import pytest
from watchdog.events import FileModifiedEvent

from codelens.indexer.indexer import Indexer
from codelens.indexer.models import NodeType
from codelens.watcher import CodeLensEventHandler, WatcherDaemon

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "sample-java-repo"


@pytest.fixture
def indexer():
    return Indexer()


# ---------------------------------------------------------------------------
# Incremental Indexing Tests
# ---------------------------------------------------------------------------


class TestIncrementalIndexing:
    """Test that index_incremental correctly updates the graph."""

    def test_incremental_add_file(self, indexer, tmp_path):
        # 1. Initial index (empty)
        initial_result = indexer.index_repository(tmp_path)
        assert len(initial_result.nodes) == 0

        # 2. Add a file
        new_file = tmp_path / "Main.java"
        new_file.write_text("public class Main { public void run() {} }")

        # 3. Incremental update
        updated_result = indexer.index_incremental(
            tmp_path,
            initial_result,
            changed_files=[new_file],
            deleted_files=[],
        )

        files = [n for n in updated_result.nodes if n.node_type == NodeType.FILE]
        assert len(files) == 1
        assert files[0].name == "Main.java"

        classes = [n for n in updated_result.nodes if n.node_type == NodeType.CLASS]
        assert len(classes) == 1
        assert classes[0].name == "Main"

    def test_incremental_modify_file(self, indexer, tmp_path):
        # 1. Initial index
        main_file = tmp_path / "Main.java"
        main_file.write_text("public class Main { }")
        initial_result = indexer.index_repository(tmp_path)
        assert len([n for n in initial_result.nodes if n.node_type == NodeType.FUNCTION]) == 0

        # 2. Modify the file
        main_file.write_text("public class Main { public void run() {} }")

        # 3. Incremental update
        updated_result = indexer.index_incremental(
            tmp_path,
            initial_result,
            changed_files=[main_file],
            deleted_files=[],
        )

        funcs = [n for n in updated_result.nodes if n.node_type == NodeType.FUNCTION]
        assert len(funcs) == 1
        assert funcs[0].name == "run"

    def test_incremental_delete_file(self, indexer, tmp_path):
        # 1. Initial index
        main_file = tmp_path / "Main.java"
        main_file.write_text("public class Main { }")
        initial_result = indexer.index_repository(tmp_path)
        assert len(initial_result.nodes) > 0

        # 2. Delete the file
        main_file.unlink()

        # 3. Incremental update
        updated_result = indexer.index_incremental(
            tmp_path,
            initial_result,
            changed_files=[],
            deleted_files=[main_file],
        )

        assert len(updated_result.nodes) == 0
        assert len(updated_result.edges) == 0


# ---------------------------------------------------------------------------
# Watchdog Event Handler Tests
# ---------------------------------------------------------------------------


class TestWatcherEventHandler:
    """Test that the event handler correctly filters and queues events."""

    def test_filters_out_hidden_and_build_dirs(self):
        q = Queue()
        handler = CodeLensEventHandler(q)

        # Should be ignored
        handler.on_modified(FileModifiedEvent("/repo/.git/config"))
        handler.on_modified(FileModifiedEvent("/repo/target/classes/Main.class"))
        handler.on_modified(FileModifiedEvent("/repo/build/output.java"))
        handler.on_modified(FileModifiedEvent("/repo/.idea/workspace.xml"))

        # Should be queued
        handler.on_modified(FileModifiedEvent("/repo/src/Main.java"))

        events = []
        while not q.empty():
            events.append(q.get_nowait())

        assert len(events) == 1
        assert events[0][0] == "changed"
        assert events[0][1].name == "Main.java"
