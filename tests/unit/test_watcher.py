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

    def test_event_handler_on_created_and_deleted(self):
        from watchdog.events import FileCreatedEvent, FileDeletedEvent
        q = Queue()
        handler = CodeLensEventHandler(q)
        
        handler.on_created(FileCreatedEvent("/repo/src/Foo.java"))
        handler.on_deleted(FileDeletedEvent("/repo/src/Bar.py"))
        
        events = []
        while not q.empty():
            events.append(q.get_nowait())
            
        assert len(events) == 2
        assert events[0] == ("changed", Path("/repo/src/Foo.java"))
        assert events[1] == ("deleted", Path("/repo/src/Bar.py"))

    def test_event_handler_on_moved(self):
        from watchdog.events import FileMovedEvent
        q = Queue()
        handler = CodeLensEventHandler(q)
        
        # Move relevant to relevant
        handler.on_moved(FileMovedEvent("/repo/src/Bar.java", "/repo/src/NewBar.py"))
        # Move irrelevant to irrelevant
        handler.on_moved(FileMovedEvent("/repo/target/Bar.class", "/repo/target/NewBar.class"))
        
        events = []
        while not q.empty():
            events.append(q.get_nowait())
            
        assert len(events) == 2
        assert events[0] == ("deleted", Path("/repo/src/Bar.java"))
        assert events[1] == ("changed", Path("/repo/src/NewBar.py"))


class TestWatcherDaemonExecution:
    """Test WatcherDaemon control logic, loops, and debouncing."""

    def test_watcher_daemon_start_validation(self):
        daemon = WatcherDaemon(Path("/nonexistent/dir"))
        with pytest.raises(ValueError, match="does not exist"):
            daemon.start()

    def test_watcher_daemon_stop(self):
        from unittest.mock import MagicMock
        daemon = WatcherDaemon(Path("."))
        daemon.observer = MagicMock()
        daemon._running = True
        daemon.stop()
        assert not daemon._running
        daemon.observer.stop.assert_called_once()
        daemon.observer.join.assert_called_once()

    def test_watcher_daemon_process_loop_debounces(self):
        from unittest.mock import MagicMock
        daemon = WatcherDaemon(Path("/fake/repo"))
        daemon.indexer = MagicMock()
        daemon.current_result = MagicMock()
        daemon._running = True
        
        # Populate some mock events in the queue
        daemon.event_queue.put(("changed", Path("/fake/repo/A.java")))
        daemon.event_queue.put(("changed", Path("/fake/repo/B.java")))
        daemon.event_queue.put(("deleted", Path("/fake/repo/C.java")))
        
        # We want to exit the loop after one cycle
        # Patch time.sleep to set _running = False so the loop terminates immediately
        import time
        original_sleep = time.sleep
        def mock_sleep(secs):
            daemon._running = False
            
        time.sleep = mock_sleep
        try:
            daemon._process_loop()
        finally:
            time.sleep = original_sleep
            
        # Assert indexer was called once with aggregated events
        daemon.indexer.index_incremental.assert_called_once()
        args = daemon.indexer.index_incremental.call_args[0]
        assert set(args[2]) == {Path("/fake/repo/A.java"), Path("/fake/repo/B.java")}
        assert set(args[3]) == {Path("/fake/repo/C.java")}


class TestWatcherNeo4jSync:
    """Test that _sync_to_neo4j calls the Neo4jClient correctly."""

    def _make_daemon(self, tmp_path):
        """Helper: daemon with a mocked Neo4j client and a minimal in-memory result."""
        from unittest.mock import MagicMock
        from codelens.indexer.models import ParseResult, CodeNode, CodeEdge, NodeType, EdgeType

        daemon = WatcherDaemon(tmp_path)
        daemon._neo4j = MagicMock()

        # Populate in-memory state with one node and one edge for a fake file
        rel = "src/Foo.java"
        node = CodeNode(
            uid=f"{rel}:Foo",
            name="Foo",
            qualified_name="Foo",
            node_type=NodeType.CLASS,
            filepath=rel,
            start_line=1,
            end_line=10,
        )
        edge = CodeEdge(
            source_uid=f"{rel}:Foo",
            target_uid="unresolved:Bar",
            edge_type=EdgeType.CALLS,
            filepath=rel,
            line=5,
        )
        result = ParseResult(filepath=str(tmp_path))
        result.nodes = [node]
        result.edges = [edge]
        daemon.current_result = result
        return daemon, rel

    def test_sync_deleted_calls_delete_subgraph(self, tmp_path):
        daemon, rel = self._make_daemon(tmp_path)
        deleted_abs = tmp_path / rel

        daemon._sync_to_neo4j(changed=set(), deleted={deleted_abs})

        daemon._neo4j.delete_file_subgraph.assert_called_once_with(rel)
        daemon._neo4j.ingest_parse_result.assert_not_called()

    def test_sync_changed_deletes_then_reingests(self, tmp_path):
        daemon, rel = self._make_daemon(tmp_path)
        changed_abs = tmp_path / rel

        daemon._sync_to_neo4j(changed={changed_abs}, deleted=set())

        daemon._neo4j.delete_file_subgraph.assert_called_once_with(rel)
        daemon._neo4j.ingest_parse_result.assert_called_once()

        ingested: ParseResult = daemon._neo4j.ingest_parse_result.call_args[0][0]
        assert len(ingested.nodes) == 1
        assert ingested.nodes[0].filepath == rel
        assert len(ingested.edges) == 1

    def test_sync_no_op_when_neo4j_is_none(self, tmp_path):
        daemon, rel = self._make_daemon(tmp_path)
        daemon._neo4j = None
        changed_abs = tmp_path / rel

        # Should not raise, should do nothing
        daemon._sync_to_neo4j(changed={changed_abs}, deleted=set())

    def test_sync_changed_excludes_unrelated_nodes(self, tmp_path):
        """Nodes from other files must not be included in the mini ParseResult."""
        from unittest.mock import MagicMock
        from codelens.indexer.models import ParseResult, CodeNode, NodeType

        daemon = WatcherDaemon(tmp_path)
        daemon._neo4j = MagicMock()

        rel_changed = "src/Foo.java"
        rel_other = "src/Bar.java"

        def make_node(rel, name):
            return CodeNode(
                uid=f"{rel}:{name}",
                name=name,
                qualified_name=name,
                node_type=NodeType.CLASS,
                filepath=rel,
                start_line=1,
                end_line=5,
            )

        result = ParseResult(filepath=str(tmp_path))
        result.nodes = [make_node(rel_changed, "Foo"), make_node(rel_other, "Bar")]
        result.edges = []
        daemon.current_result = result

        daemon._sync_to_neo4j(changed={tmp_path / rel_changed}, deleted=set())

        ingested: ParseResult = daemon._neo4j.ingest_parse_result.call_args[0][0]
        assert len(ingested.nodes) == 1
        assert ingested.nodes[0].name == "Foo"
