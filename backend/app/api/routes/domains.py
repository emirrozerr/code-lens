from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class Domain(BaseModel):
    id: str
    name: str
    rule_count: int


@router.get("/")
def list_domains() -> list[Domain]:
    # TODO: query Neo4j for domain clusters grouped by community detection
    return []


@router.get("/{domain_id}")
def get_domain(domain_id: str) -> Domain:
    # TODO: fetch domain details and associated rules from Neo4j
    return Domain(id=domain_id, name="", rule_count=0)
