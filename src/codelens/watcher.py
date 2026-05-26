"""Background daemon for real-time incremental code indexing.

Uses watchdog to monitor the filesystem and triggers incremental
parsing in the Indexer when Java files change.
"""

import logging
import time
from pathlib import Path
from queue import Empty, Queue

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from codelens.indexer.indexer import Indexer
from codelens.indexer.models import ParseResult

logger = logging.getLogger(__name__)


class CodeLensEventHandler(FileSystemEventHandler):
    """Listens for file changes and queues them for processing."""

    def __init__(self, event_queue: Queue):
        self.event_queue = event_queue

    def _is_relevant(self, event: FileSystemEvent) -> bool:
        if event.is_directory:
            return False
        path = Path(event.src_path)

        # Skip hidden and common build dirs
        skip_dirs = {".git", "target", "build", "node_modules", ".idea", ".vscode"}
        if any(p in skip_dirs or p.startswith(".") for p in path.parts):
            return False

        return path.suffix.lower() == ".java"

    def on_created(self, event: FileSystemEvent):
        if self._is_relevant(event):
            self.event_queue.put(("changed", Path(event.src_path)))

    def on_modified(self, event: FileSystemEvent):
        if self._is_relevant(event):
            self.event_queue.put(("changed", Path(event.src_path)))

    def on_deleted(self, event: FileSystemEvent):
        if self._is_relevant(event):
            self.event_queue.put(("deleted", Path(event.src_path)))

    def on_moved(self, event: FileSystemEvent):
        # Treat as delete of old, create of new
        if not event.is_directory:
            old_path = Path(event.src_path)
            new_path = Path(event.dest_path)

            # Use same filters
            skip_dirs = {".git", "target", "build", "node_modules", ".idea", ".vscode"}

            old_relevant = old_path.suffix.lower() == ".java" and not any(
                p in skip_dirs or p.startswith(".") for p in old_path.parts
            )
            new_relevant = new_path.suffix.lower() == ".java" and not any(
                p in skip_dirs or p.startswith(".") for p in new_path.parts
            )

            if old_relevant:
                self.event_queue.put(("deleted", old_path))
            if new_relevant:
                self.event_queue.put(("changed", new_path))


class WatcherDaemon:
    """Manages the watchdog observer and the processing loop."""

    def __init__(self, repo_path: Path):
        self.repo_path = repo_path.resolve()
        self.indexer = Indexer()
        self.event_queue: Queue = Queue()
        self.observer = Observer()
        self.current_result: ParseResult | None = None
        self._running = False

    def start(self):
        """Start the watcher daemon."""
        if not self.repo_path.is_dir():
            raise ValueError(f"Repository path does not exist: {self.repo_path}")

        # 1. Initial full index
        logger.info("Starting initial index of %s...", self.repo_path)
        self.current_result = self.indexer.index_repository(self.repo_path)
        logger.info("Initial index complete. Starting file watcher...")

        # 2. Start watchdog
        event_handler = CodeLensEventHandler(self.event_queue)
        self.observer.schedule(event_handler, str(self.repo_path), recursive=True)
        self.observer.start()
        self._running = True

        # 3. Enter processing loop
        try:
            self._process_loop()
        except KeyboardInterrupt:
            logger.info("Stopping watcher...")
        finally:
            self.stop()

    def stop(self):
        self._running = False
        if self.observer.is_alive():
            self.observer.stop()
            self.observer.join()

    def _process_loop(self):
        """Consume events from the queue, debounce, and trigger incremental updates."""
        while self._running:
            try:
                # Wait for at least one event
                event_type, path = self.event_queue.get(timeout=1.0)

                # Debounce: wait a short time to accumulate rapid successive events
                time.sleep(0.5)

                changed = {path} if event_type == "changed" else set()
                deleted = {path} if event_type == "deleted" else set()

                # Drain queue of all currently pending events
                while not self.event_queue.empty():
                    try:
                        et, p = self.event_queue.get_nowait()
                        if et == "changed":
                            changed.add(p)
                        else:
                            deleted.add(p)
                    except Empty:
                        break

                # A file might be both changed and deleted in rapid succession. Deleted wins.
                changed -= deleted

                if changed or deleted:
                    logger.info("Detected changes: %d modified, %d deleted", len(changed), len(deleted))
                    if self.current_result:
                        self.current_result = self.indexer.index_incremental(
                            self.repo_path,
                            self.current_result,
                            list(changed),
                            list(deleted),
                        )

            except Empty:
                continue
