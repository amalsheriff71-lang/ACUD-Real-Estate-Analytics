from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout

from fastapi import APIRouter, HTTPException

from app.config import get_settings
from app.schemas import ChatRequest, ChatResponse
from app.services.cohere_chat import generate_reply

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])
executor = ThreadPoolExecutor(max_workers=4)


@router.post("", response_model=ChatResponse)
def chat(payload: ChatRequest):
    settings = get_settings()
    if not settings.cohere_api_key:
        raise HTTPException(
            status_code=503,
            detail="The chat assistant is not configured yet. Add COHERE_API_KEY to backend/.env.",
        )

    future = executor.submit(
        generate_reply,
        payload.language,
        payload.message,
        payload.history,
    )
    try:
        result = future.result(timeout=35)
    except FutureTimeout:
        future.cancel()
        raise HTTPException(
            status_code=504,
            detail="The assistant took too long to respond. Please try again.",
        )
    except Exception as exc:
        # Log details server-side, but do not expose provider secrets to the client.
        print(f"Cohere chat error: {type(exc).__name__}: {exc}")
        raise HTTPException(
            status_code=502,
            detail="The assistant is temporarily unavailable. Please try again.",
        )

    return ChatResponse(reply=result["reply"], model=settings.cohere_model, **{
        key: value for key, value in result.items() if key != "reply"
    })
