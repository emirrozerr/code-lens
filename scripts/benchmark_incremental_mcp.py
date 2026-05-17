import time
import os
import shutil
from pathlib import Path
from codelens.indexer.indexer import Indexer
from codelens.graph.neo4j_client import Neo4jClient
from codelens.mcp_server.server import get_code_context, get_callers, get_callees, search_nodes

def run_benchmarks():
    repo_path = Path(".").resolve()
    print(f"=== BENCHMARKING CODE-LENS REPO ({repo_path}) ===\n")

    # 1. Full Indexing
    indexer = Indexer()
    print("[1] Running Full Indexing...")
    start_time = time.time()
    result = indexer.index_repository(repo_path)
    full_index_time = time.time() - start_time
    print(f"    Full index completed in {full_index_time:.4f} seconds.")
    print(f"    Extracted {len(result.nodes)} nodes and {len(result.edges)} edges.")

    # 2. Ingestion to Neo4j
    print("\n[2] Ingesting to Neo4j...")
    client = Neo4jClient()
    start_time = time.time()
    try:
        with client.session() as session:
            session.run("MATCH (n) DETACH DELETE n") # Clear DB for benchmark
        client.ingest_parse_result(result)
        ingest_time = time.time() - start_time
        print(f"    Ingestion completed in {ingest_time:.4f} seconds.")
    finally:
        client.close()

    # 3. Incremental Indexing
    print("\n[3] Testing Incremental Indexing...")
    # Simulate a file modification
    test_file = Path("src/codelens/settings.py")
    original_content = test_file.read_text()
    
    try:
        # Modify the file
        test_file.write_text(original_content + "\n# Benchmarking mock comment\n")
        
        start_time = time.time()
        incremental_result = indexer.index_incremental(repo_path, result, changed_files=[test_file], deleted_files=[])
        incremental_time = time.time() - start_time
        print(f"    Incremental index (1 changed file) completed in {incremental_time:.4f} seconds.")
        print(f"    Speedup: {full_index_time / incremental_time:.2f}x faster than full index.")
    finally:
        # Restore the file
        test_file.write_text(original_content)

    # 4. MCP Query Layer Benchmarks
    print("\n[4] Benchmarking MCP Query Layer (Latency & Usefulness)...")
    
    # Tool 1: search_nodes
    start_time = time.time()
    search_res = search_nodes("CodeNode")
    search_time = time.time() - start_time
    print(f"  - search_nodes('CodeNode') took {search_time:.4f}s")
    
    # Tool 2: get_code_context
    start_time = time.time()
    context_res = get_code_context("JavaParser")
    context_time = time.time() - start_time
    print(f"  - get_code_context('JavaParser') took {context_time:.4f}s")
    print(f"\n--- Output of get_code_context('JavaParser') ---\n{context_res}\n------------------------------------------------")

    # Tool 3: get_callers
    start_time = time.time()
    callers_res = get_callers("Neo4jClient")
    callers_time = time.time() - start_time
    print(f"\n  - get_callers('Neo4jClient') took {callers_time:.4f}s")

    # Tool 4: get_callees
    start_time = time.time()
    callees_res = get_callees("index_repository")
    callees_time = time.time() - start_time
    print(f"  - get_callees('index_repository') took {callees_time:.4f}s")

if __name__ == "__main__":
    run_benchmarks()
