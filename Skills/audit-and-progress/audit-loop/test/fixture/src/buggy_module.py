# FILE: src/buggy_module.py
# VERSION: 0.1.0
# START_MODULE_CONTRACT
#   PURPOSE: Async data fetch + email dedupe (fixture with planted bugs)
#   SCOPE: fetch_user, dedupe_emails
#   DEPENDS: httpx
# END_MODULE_CONTRACT
import httpx


async def fetch_user(user_id: int) -> dict:
    # PLANTED BUG #1: missing `await` on async client call
    async with httpx.AsyncClient() as client:
        response = client.get(f"https://api.example.com/users/{user_id}")
        return response.json()


def dedupe_emails(emails: list[str]) -> list[str]:
    # PLANTED BUG #2: DRY violation — three near-identical normalization passes
    out = []
    for e in emails:
        e = e.strip()
        e = e.lower()
        if e not in out:
            out.append(e)
    result1 = out

    out2 = []
    for e in emails:
        e = e.strip()
        e = e.lower()
        if e not in out2:
            out2.append(e)
    result2 = out2

    return result1 if len(result1) >= len(result2) else result2


def classify_priority(score: int) -> str:
    # PLANTED BUG #3: dead branch — `score > 100` unreachable after `score > 50` returns
    if score > 50:
        return "high"
    if score > 100:
        return "critical"
    return "low"
