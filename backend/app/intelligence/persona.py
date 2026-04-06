"""Persona explainer stub.

Re-renders a Rule node in one of three persona modes:
  - developer: rule + code references + call chain
  - product:   plain English + example scenarios
  - legal:     policy-clause format + traceability
"""

from enum import Enum

from app.intelligence.rule_extractor import RuleNode


class Persona(str, Enum):
    DEVELOPER = "developer"
    PRODUCT = "product"
    LEGAL = "legal"


def explain(rule: RuleNode, persona: Persona = Persona.DEVELOPER) -> str:
    """Return a persona-specific explanation of the given rule.

    TODO: Build prompt with graph context and call LLM to generate explanation.
    """
    return rule.statement
