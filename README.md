# AI WooCommerce Assistant

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