"""FastAPI application — REST API for CodeLens frontend."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from codelens.api import store
from codelens.api.auth import router as auth_router
from codelens.api.chat import router as chat_router
from codelens.api.domains import router as domains_router
from codelens.api.graph import router as graph_router
from codelens.api.jobs import router as jobs_router
from codelens.api.repos import router as repos_router
from codelens.api.stats import router as stats_router
from codelens.api.users import router as users_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    store.init_db()
    yield


app = FastAPI(title="CodeLens API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(repos_router)
app.include_router(jobs_router)
app.include_router(domains_router)
app.include_router(stats_router)
app.include_router(graph_router)
app.include_router(chat_router)


@app.get("/health")
def health():
    return {"status": "ok"}
