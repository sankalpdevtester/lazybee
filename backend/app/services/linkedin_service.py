import httpx
import os
from datetime import datetime

LINKEDIN_API = "https://api.linkedin.com/v2"

def _get_token():
    return os.getenv("LINKEDIN_ACCESS_TOKEN", "")

def _headers():
    return {
        "Authorization": f"Bearer {_get_token()}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
    }

async def get_profile() -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(f"{LINKEDIN_API}/userinfo", headers=_headers())
        if r.status_code != 200:
            raise RuntimeError(f"LinkedIn profile fetch failed: {r.status_code} {r.text[:200]}")
        return r.json()

async def post_text(person_urn: str, text: str) -> dict:
    payload = {
        "author": f"urn:li:person:{person_urn}",
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
    }
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(f"{LINKEDIN_API}/ugcPosts", json=payload, headers=_headers())
        if r.status_code not in (200, 201):
            raise RuntimeError(f"LinkedIn post failed: {r.status_code} {r.text[:200]}")
        return r.json()
