import asyncio
import httpx
from biddelta.api import app


def test_health_does_not_claim_inference_verification():
    async def check():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/health")
            assert response.status_code == 200
            assert response.json() == {"status": "ok", "milestone": "P0-A", "inference": "unverified"}
            assert (await client.post("/approve")).status_code == 404
    asyncio.run(check())
