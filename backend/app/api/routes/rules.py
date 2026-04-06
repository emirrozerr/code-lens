from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class Rule(BaseModel):
    id: str
    statement: str
    domain: str
    source_file: str
    source_line: int
    persona: str = "developer"


@router.get("/")
def list_rules(q: str | None = None, domain: str | None = None, persona: str = "developer") -> list[Rule]:
    # TODO: if q is provided, run full-text + vector search over Rule nodes;
    #       otherwise list all rules optionally filtered by domain, rendered by persona
    return []


@router.get("/{rule_id}")
def get_rule(rule_id: str, persona: str = "developer") -> Rule:
    # TODO: fetch Rule node from Neo4j and render with Persona Explainer
    return Rule(
        id=rule_id,
        statement="",
        domain="",
        source_file="",
        source_line=0,
        persona=persona,
    )
