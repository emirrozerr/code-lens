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

