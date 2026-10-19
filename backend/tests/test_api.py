import asyncio
import httpx
from biddelta.api import create_app


def test_health_does_not_claim_inference_verification(tmp_path):
    app = create_app(tmp_path / "health.sqlite3")
    async def check():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://127.0.0.1:8000") as client:
            response = await client.get("/health")
            assert response.status_code == 200
            assert response.json() == {"status": "ok", "milestone": "P0-B-slice-1", "inference": "unverified"}
            assert (await client.post("/approve")).status_code == 404
    asyncio.run(check())
