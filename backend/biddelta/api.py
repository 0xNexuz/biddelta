"""P0-A API foundation. Domain writes are trusted local service calls only."""
from fastapi import FastAPI

app = FastAPI(title="BidDelta", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "milestone": "P0-A", "inference": "unverified"}
