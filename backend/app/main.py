from fastapi import FastAPI

from app.api.routes import domains, rules, webhooks

app = FastAPI(
    title="CodeLens API",
    description="GraphRAG-powered code intelligence platform",
    version="0.1.0",
)

app.include_router(rules.router, prefix="/api/rules", tags=["rules"])
app.include_router(domains.router, prefix="/api/domains", tags=["domains"])
app.include_router(webhooks.router, prefix="/api/webhooks", tags=["webhooks"])


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
