# Standora web dashboard

The custom React + TypeScript dashboard calls the existing Python/LangGraph engine through FastAPI. FastAPI serves the production frontend from the same origin. The original Gradio interface remains available as a legacy entry point.

## Local development

Requires Python 3.11+ and Node.js 20.19+ (or 22.12+).

```sh
uv pip install -e '.[dev]'
cd frontend
npx --yes pnpm@11.19.0 install --frozen-lockfile
npx --yes pnpm@11.19.0 run dev
```

In another terminal, from the repository root:

```sh
STANDORT_LLM_MODE=offline .venv/bin/uvicorn standort_agent.api:app --app-dir src --host 127.0.0.1 --port 8000
```

Open the Vite URL. Its `/api` proxy forwards requests to FastAPI.

## Production preview

```sh
cd frontend
npx --yes pnpm@11.19.0 run build
cd ..
.venv/bin/uvicorn standort_agent.api:app --app-dir src --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000.

## Deploy to Render Free

1. Push this repository, including `frontend/pnpm-lock.yaml` and `render.yaml`, to your GitHub account. Do not commit `.env` or API keys.
2. Sign in to Render, choose **New → Blueprint**, and connect the repository. Render reads `render.yaml` and creates one Free web service.
3. Keep `STANDORT_LLM_MODE=auto` for a working demo without credentials. Optionally add `GROQ_API_KEY` as a secret environment variable in the Render dashboard; never put it in frontend code. Optional `GROQ_MODEL` defaults to `openai/gpt-oss-20b`.
4. Wait for the build and health check. Open the assigned `https://standora-….onrender.com` address and test an example profile.
5. Before the interview, open the app and complete an analysis to wake the service. Free Render services sleep after 15 minutes without traffic and can take about a minute to restart.

The deployment needs no database. Reports are generated in temporary isolated folders, returned with each response and downloaded in the browser; no shared report file is exposed. The server accepts one analysis at a time to limit concurrent LLM work. This is a demo safeguard, not per-user authentication or rate limiting. Groq account quotas still apply.

## Demo behaviour and limits

- Scores and order are calculated in Python. AI explanations cannot change them.
- The UI streams progress as workflow nodes complete.
- In `auto` mode, unavailable Groq falls back to rule-based explanations. Strict `groq` mode returns an error instead.
- Data: 20 synthetic municipalities/districts across nine federal states, June 2026.
- Map: interactive Leaflet/OpenStreetMap with sourced reference points for all 20 candidates, selected-location zoom, an all-location view and official Vienna district outlines. Coordinate sources and precision are included in the UI. Points represent districts or city centres, not specific properties. Geography is bundled locally; there are no runtime geocoding requests. Map tiles and Google Fonts need internet access; coordinates and system fonts remain available if external services fail.
- Rent estimates are the supplied rent index multiplied by required area, not property quotes.
- The browser keeps the completed analysis separate from profile edits; re-run to update results.

## Checks

```sh
STANDORT_LLM_MODE=offline .venv/bin/pytest -q
cd frontend
npx --yes pnpm@11.19.0 run build
```
