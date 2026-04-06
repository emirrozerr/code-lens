"""Rule change simulator stub.

Diffs rule subgraphs between base and head branches to detect:
  RULE_ADDED | RULE_MODIFIED | RULE_REMOVED

and generates a business-language impact summary for PR comments.
"""

from dataclasses import dataclass
from enum import Enum


class ChangeType(str, Enum):
    RULE_ADDED = "RULE_ADDED"
    RULE_MODIFIED = "RULE_MODIFIED"
    RULE_REMOVED = "RULE_REMOVED"


@dataclass
class RuleChange:
    rule_id: str
    change_type: ChangeType
    summary: str


def simulate(base_ref: str, head_ref: str, repo_path: str = ".") -> list[RuleChange]:
    """Diff rule subgraphs between base and head and return detected changes.

    TODO:
      1. Checkout base ref, index, capture rule snapshot.
      2. Checkout head ref, index, capture rule snapshot.
      3. Diff the two snapshots.
      4. Classify each change and generate LLM summary.
    """
    return []


def format_pr_comment(changes: list[RuleChange]) -> str:
    """Format detected rule changes into a structured PR comment body.

    TODO: Render changes as markdown with ⚠️ / ➕ / ✅ indicators.
    """
    if not changes:
        return "No business logic changes detected."
    lines = ["## ⚠️ Business Logic Changes Detected\n"]
    for change in changes:
        lines.append(f"- **{change.change_type}** `{change.rule_id}`: {change.summary}")
    return "\n".join(lines)
