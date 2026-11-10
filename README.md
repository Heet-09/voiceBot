# Talk to Heet

A voice bot that answers interview questions as Heet would. A Flask app (`app.py`) serves `index.html` and a `/api/chat` endpoint that calls Google Gemini with the persona in `persona.py`. The API key is read from the `GEMINI_API_KEY` environment variable (`.env` locally).

Live URL: _add after deploying_

Run locally: `pip install -r requirements.txt`, then `python app.py`, then open http://localhost:3000.

Deploy on Render (free web service): build command `pip install -r requirements.txt`, start command `gunicorn app:app`, and set `GEMINI_API_KEY` under Environment.
