# AI Store Assistant

A React and FastAPI app with Gemini-powered chat, direct catalog price lookup, and store policy answers that show their source.

## First-time setup on Windows

Use PowerShell from the project root. The project was tested with Python 3.13 and Node.js 26.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

if (-not (Test-Path .env)) {
    Copy-Item .env.example .env
}
```

Set `GEMINI_API_KEY` and `GEMINI_MODEL` in your local `.env`.

## Run the app

Start FastAPI from the project root:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app:app --reload
```

In a second terminal, start React from the project root:

```powershell
cd frontend
npm.cmd ci
npm.cmd run dev
```

Open the URL Vite prints. Keep both terminals running. On later runs, you can skip `npm.cmd ci` unless the dependencies changed.

## Run the tests

From the project root:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## Evaluate Gemini chat tool use

From the project root with `GEMINI_API_KEY` and `GEMINI_MODEL` configured in your local `.env`, run:

```powershell
.\.venv\Scripts\python.exe -m evaluate_chat_tools
```

The script sends three live questions about stock and store policies, each with a fresh chat history. It prints the answer and response time for each case, followed by the number of cases that passed. Read any answer marked `REVIEW` to see whether a fact is missing or the wording differs from the phrase checks.

## Deploy the public portfolio demo on Render

Use the repository's Dockerfile and set the service's health check path to `/api/health`.
Add these environment variables in Render:

- `PUBLIC_DEMO=true` enables guest access with separate conversation histories.
- `PUBLIC_DEMO_GEMINI_API_KEY` holds a key from a dedicated Gemini Free Tier project.
- `GEMINI_MODEL` is a model enabled for that project's Free Tier.

The app allows eight requests to the chat and policy routes per visitor and 60 across the demo per UTC day. Catalog lookups are separate. On Render Free, SQLite history and these local counters reset when the service restarts, redeploys, or spins down. The dedicated Gemini project supplies the provider-side quota across those resets. [Render Free limitations](https://render.com/docs/free) · [Gemini API rate limits](https://ai.google.dev/gemini-api/docs/rate-limits)

For a password-protected deployment, set `DEMO_PASSWORD` and the regular `GEMINI_API_KEY` and omit `PUBLIC_DEMO`.
