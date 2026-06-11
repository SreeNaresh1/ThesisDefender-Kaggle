from fastapi import APIRouter, Request
from datetime import datetime, timezone
import time

router = APIRouter()

@router.get("")
async def get_health(request: Request):
    app = request.app
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model_provider": app.state.model_client.provider if hasattr(app.state, "model_client") else "unknown",
        "foundry_iq_available": getattr(app.state, "foundry_client", None) is not None
    }

@router.get("/model")
async def test_model(request: Request):
    client = request.app.state.model_client
    start = time.time()
    try:
        # 1-token ping to check connectivity
        _ = await client.complete(
            system_prompt="Return 'ok'.",
            user_prompt="ping",
            temperature=0.0,
            max_tokens=5,
            json_mode=False
        )
        latency = int((time.time() - start) * 1000)
        return {
            "status": "ok",
            "provider": client.provider,
            "latency_ms": latency
        }
    except Exception as e:
        return {
            "status": "error",
            "provider": client.provider if hasattr(client, "provider") else "unknown",
            "latency_ms": int((time.time() - start) * 1000),
            "detail": str(e)
        }
