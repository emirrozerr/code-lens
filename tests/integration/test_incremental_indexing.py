"""Integration tests for the incremental indexing logic."""

from pathlib import Path
import pytest
from codelens.indexer.indexer import Indexer
from codelens.indexer.models import NodeType

@pytest.fixture
def indexer():
    return Indexer()

def test_incremental_indexing_modifies_graph_correctly(indexer, tmp_path):
    # 1. Setup a simple python project
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    
    file_a = src_dir / "a.py"
    file_a.write_text("class A:\n    def foo(self):\n        pass\n")
    
    file_b = src_dir / "b.py"
    file_b.write_text("class B:\n    def bar(self):\n        pass\n")

    # 2. Initial Full Index
    initial_result = indexer.index_repository(tmp_path)
    initial_nodes = {n.uid: n for n in initial_result.nodes}
    
    assert len([n for n in initial_result.nodes if n.node_type == NodeType.FILE]) == 2
    assert len([n for n in initial_result.nodes if n.node_type == NodeType.CLASS]) == 2

    # 3. Modify a.py
    file_a.write_text("class A:\n    def foo(self):\n        pass\n    def new_method(self):\n        pass\n")
    
    # 4. Run Incremental Index
    incremental_result = indexer.index_incremental(
        repo_path=tmp_path,
        previous_result=initial_result,
        changed_files=[file_a],
        deleted_files=[]
    )
    
    # 5. Assertions
    # file_b's nodes should be untouched (exact same memory object or exact same attributes)
    b_nodes_initial = [n for n in initial_result.nodes if "b.py" in n.filepath]
    b_nodes_incremental = [n for n in incremental_result.nodes if "b.py" in n.filepath]
    assert len(b_nodes_initial) == len(b_nodes_incremental)
    
    # file_a should have a new method
    a_funcs_initial = [n for n in initial_result.nodes if "a.py" in n.filepath and n.node_type == NodeType.FUNCTION]
    a_funcs_incremental = [n for n in incremental_result.nodes if "a.py" in n.filepath and n.node_type == NodeType.FUNCTION]
    
    assert len(a_funcs_initial) == 1
    assert len(a_funcs_incremental) == 2
    assert any("new_method" in n.name for n in a_funcs_incremental)

def test_incremental_indexing_deleted_file(indexer, tmp_path):
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    file_a = src_dir / "a.py"
    file_a.write_text("class A:\n    pass\n")
    
    initial_result = indexer.index_repository(tmp_path)
    assert len(initial_result.nodes) > 0
    
    # Delete file
    file_a.unlink()
    
    incremental_result = indexer.index_incremental(
        repo_path=tmp_path,
        previous_result=initial_result,
        changed_files=[],
        deleted_files=[file_a]
    )
    
    # Graph should be empty
    assert len(incremental_result.nodes) == 0
    assert len(incremental_result.edges) == 0
