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

from codelens.graph.neo4j_client import Neo4jClient
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

        return path.suffix.lower() in {".java", ".py"}

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

            old_relevant = old_path.suffix.lower() in {".java", ".py"} and not any(
                p in skip_dirs or p.startswith(".") for p in old_path.parts
            )
            new_relevant = new_path.suffix.lower() in {".java", ".py"} and not any(
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
        self._neo4j: Neo4jClient | None = None  # opened in start(), closed in stop()

    def start(self):
        """Start the watcher daemon."""
        if not self.repo_path.is_dir():
            raise ValueError(f"Repository path does not exist: {self.repo_path}")

        # 1. Initial full index (in-memory, for call resolution state)
        logger.info("Starting initial index of %s...", self.repo_path)
        self.current_result = self.indexer.index_repository(self.repo_path)
        logger.info("Initial index complete. Starting file watcher...")

        # 2. Open Neo4j connection (best-effort — watcher still works without it)
        try:
            self._neo4j = Neo4jClient()
            logger.info("Connected to Neo4j for incremental sync.")
        except Exception as e:
            logger.warning(
                "Could not connect to Neo4j (%s). File changes will not be persisted to graph.", e
            )
            self._neo4j = None

        # 3. Start watchdog
        event_handler = CodeLensEventHandler(self.event_queue)
        self.observer.schedule(event_handler, str(self.repo_path), recursive=True)
        self.observer.start()
        self._running = True

        # 4. Enter processing loop
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
        if self._neo4j is not None:
            self._neo4j.close()
            self._neo4j = None

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
                        self._sync_to_neo4j(changed, deleted)

            except Empty:
                continue

    def _sync_to_neo4j(self, changed: set[Path], deleted: set[Path]) -> None:
        """Persist incremental changes to Neo4j. No-op if Neo4j is not connected."""
        if self._neo4j is None:
            return

        # Convert absolute paths to relative filepaths (same format parsers use)
        def to_rel(p: Path) -> str:
            try:
                return str(p.resolve().relative_to(self.repo_path))
            except ValueError:
                return str(p)

        # 1. Purge deleted files from Neo4j
        for path in deleted:
            rel = to_rel(path)
            try:
                self._neo4j.delete_file_subgraph(rel)
                logger.info("Neo4j: deleted subgraph for %s", rel)
            except Exception as e:
                logger.warning("Neo4j: failed to delete subgraph for %s: %s", rel, e)

        # 2. For changed files: purge old data, then write fresh data
        if changed and self.current_result is not None:
            changed_rels = {to_rel(p) for p in changed}

            # Purge old subgraphs
            for rel in changed_rels:
                try:
                    self._neo4j.delete_file_subgraph(rel)
                    logger.debug("Neo4j: purged old subgraph for %s", rel)
                except Exception as e:
                    logger.warning("Neo4j: failed to purge old subgraph for %s: %s", rel, e)

            # Build a mini ParseResult with only the changed files' nodes and edges
            mini = ParseResult(filepath=str(self.repo_path))
            mini.nodes = [n for n in self.current_result.nodes if n.filepath in changed_rels]
            mini.edges = [e for e in self.current_result.edges if e.filepath in changed_rels]

            if mini.nodes or mini.edges:
                try:
                    self._neo4j.ingest_parse_result(mini)
                    logger.info(
                        "Neo4j: synced %d nodes, %d edges for %d changed file(s)",
                        len(mini.nodes),
                        len(mini.edges),
                        len(changed_rels),
                    )
                except Exception as e:
                    logger.warning("Neo4j: failed to ingest updated subgraph: %s", e)
