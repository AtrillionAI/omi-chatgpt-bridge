import os
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Omi ChatGPT Bridge", version="0.1.0")

BRIDGE_MODE = os.getenv("BRIDGE_MODE", "openai").strip().lower()
BRIDGE_NAME = os.getenv("BRIDGE_NAME", "Mac").strip() or "Mac"


class OmiToolRequest(BaseModel):
    # Omi may include these metadata fields with Chat Tool calls.
    uid: str | None = None
    app_id: str | None = None
    tool_name: str | None = None
    message: str = Field(min_length=1, max_length=12000)


@app.get("/")
def root() -> dict[str, Any]:
    return {
        "service": "omi-chatgpt-bridge",
        "status": "ok",
        "assistant": BRIDGE_NAME,
        "mode": BRIDGE_MODE,
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "mode": BRIDGE_MODE}


@app.post("/api/ask_mac")
async def ask_mac(payload: OmiToolRequest) -> dict[str, Any]:
    message = payload.message.strip()

    if BRIDGE_MODE == "openai":
        return await ask_openai(message)

    if BRIDGE_MODE == "slack":
        return await send_to_slack(message, payload)

    raise HTTPException(
        status_code=500,
        detail="BRIDGE_MODE must be 'openai' or 'slack'.",
    )


async def ask_openai(message: str) -> dict[str, Any]:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    model = os.getenv("OPENAI_MODEL", "gpt-5.6-luna").strip()

    if not api_key:
        raise HTTPException(status_code=503, detail="OPENAI_API_KEY is not configured.")

    # Import here so Slack-only deployments do not require OpenAI initialization.
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=api_key)

    try:
        response = await client.responses.create(
            model=model,
            instructions=(
                f"You are {BRIDGE_NAME}, a concise temporary voice assistant used through an Omi wearable. "
                "Answer naturally for speech. Keep routine answers short. "
                "Do not claim access to the user's ChatGPT account, memory, connectors, calendar, email, "
                "Slack, finances, or other private systems unless the current bridge explicitly provides it."
            ),
            input=message,
        )
        text = (response.output_text or "").strip()
    except Exception as exc:
        # Do not expose credentials or raw provider details to Omi.
        raise HTTPException(status_code=502, detail="Assistant request failed.") from exc

    if not text:
        text = "I received that, but I didn't get a usable response."

    return {
        "success": True,
        "message": text,
        "response": text,
        "mode": "openai",
    }


async def send_to_slack(message: str, payload: OmiToolRequest) -> dict[str, Any]:
    webhook_url = os.getenv("SLACK_WEBHOOK_URL", "").strip()

    if not webhook_url:
        raise HTTPException(status_code=503, detail="SLACK_WEBHOOK_URL is not configured.")

    slack_text = f"🎙️ Omi → {BRIDGE_NAME}: {message}"

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(webhook_url, json={"text": slack_text})
            response.raise_for_status()
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Slack relay failed.") from exc

    acknowledgement = f"Got it. I sent that to the {BRIDGE_NAME} bridge."
    return {
        "success": True,
        "message": acknowledgement,
        "response": acknowledgement,
        "mode": "slack",
    }
