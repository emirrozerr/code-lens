"""Rule extractor stub.

LangGraph agent that traverses ConditionalBranch nodes in the code graph,
gathers context via multi-hop traversal, and synthesises human-readable
Rule nodes using an LLM.
"""

from dataclasses import dataclass, field


@dataclass
class RuleNode:
    id: str
    statement: str
    domain: str
    source_node_ids: list[str] = field(default_factory=list)
    is_stale: bool = False


def extract_rules(domain: str | None = None) -> list[RuleNode]:
    """Run the LangGraph rule extraction agent.

    Traverses ConditionalBranch nodes (optionally filtered by domain),
    iteratively fetches callee subgraphs, and synthesises Rule nodes via LLM.

    TODO: Implement LangGraph agent with Neo4j traversal and LLM synthesis.
    """
    return []


def reextract_stale_rules() -> list[RuleNode]:
    """Re-extract only rules whose source nodes have been marked stale.

    TODO: Query Neo4j for stale Rule nodes and re-run extraction agent on them.
    """
    return []
