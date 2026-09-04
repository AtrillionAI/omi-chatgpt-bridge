# Omi → ChatGPT Bridge

Temporary bridge for using an Omi wearable as a voice front end while the larger Personal OS is not yet built.

## What this repo does

This project exposes an Omi **Chat Tool** named `ask_mac` and a standard Omi tools manifest at:

`/.well-known/omi-tools.json`

Omi can call the tool with natural-language requests. The bridge supports two modes:

- `openai` — sends the request to the OpenAI API and returns the response immediately to Omi so Omi can present/speak it.
- `slack` — forwards the request to a private Slack bridge channel via an incoming webhook. This is useful for routing tasks into a ChatGPT/Slack workflow, but it does **not** by itself create an immediate spoken ChatGPT reply.

## Important limitation

The OpenAI API is not the same thing as the consumer ChatGPT account/session. API mode gives a fast two-way voice assistant path through Omi, but it does not automatically inherit ChatGPT conversation history, memory, connectors, or account-specific context.

The Slack mode is intended to preserve the path into the connected ChatGPT workspace while we continue building the temporary bridge.

## Files

- `main.py` — FastAPI bridge server
- `.well-known/omi-tools.json` — Omi Chat Tools manifest
- `.env.example` — environment-variable template only; never commit real secrets
- `requirements.txt` — Python dependencies
- `.gitignore` — prevents common secret/local files from being committed

## Environment variables

Copy `.env.example` to `.env` locally or enter these as private environment variables in your hosting provider.

### Common

- `BRIDGE_MODE=openai` or `BRIDGE_MODE=slack`
- `BRIDGE_NAME=Mac`

### OpenAI mode

- `OPENAI_API_KEY` — required
- `OPENAI_MODEL=gpt-5.6-luna` — optional

### Slack mode

- `SLACK_WEBHOOK_URL` — required incoming webhook URL for the private bridge channel

## Local run

```bash
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

Health check:

`GET /health`

Manifest:

`GET /.well-known/omi-tools.json`

Tool endpoint:

`POST /api/ask_mac`

Example body:

```json
{
  "uid": "omi-user-id",
  "app_id": "omi-app-id",
  "tool_name": "ask_mac",
  "message": "What is on my agenda today?"
}
```

## Omi configuration

When the server is deployed over HTTPS, set the Omi **Chat Tools Manifest URL** to:

`https://YOUR-HOST/.well-known/omi-tools.json`

Omi Chat Tools require the `external_integration` capability. Omi resolves the relative tool endpoint against the app home/server URL.

## Security

This repository is intentionally safe to keep public. Never commit:

- OpenAI API keys
- Slack webhook URLs/tokens
- Omi API or MCP keys
- conversation transcripts
- personal data
- `.env` files

All real credentials belong in private hosting environment variables.
