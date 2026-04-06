from fastapi import APIRouter, Request

router = APIRouter()


@router.post("/github")
async def github_webhook(request: Request) -> dict:
    # TODO: validate HMAC signature, parse push/PR event, trigger re-indexing
    payload = await request.json()
    event = request.headers.get("X-GitHub-Event", "unknown")
    return {"received": True, "event": event}


@router.post("/gitlab")
async def gitlab_webhook(request: Request) -> dict:
    # TODO: validate token, parse push/MR event, trigger re-indexing
    payload = await request.json()
    return {"received": True}
