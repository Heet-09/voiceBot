import os

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory

from persona import PERSONA

load_dotenv()

app = Flask(__name__)

# Tried in order; falls through on overload (429/503) or network errors.
MODELS = [
    m
    for m in [
        os.environ.get("GEMINI_MODEL"),
        "gemini-3.1-flash-lite",
        "gemini-3.5-flash-lite",
        "gemini-3.5-flash",
        "gemini-3-flash-preview",
        "gemini-3.6-flash",
    ]
    if m
]

MAX_TURNS = 10
MAX_CHARS = 1000


@app.get("/")
def index():
    return send_from_directory(app.root_path, "index.html")


@app.post("/api/chat")
def chat():
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        return jsonify(error="Server is not configured yet."), 500

    body = request.get_json(silent=True) or {}
    incoming = body.get("messages")
    if not isinstance(incoming, list) or not incoming:
        return jsonify(error="No messages."), 400

    contents = [
        {
            "role": "model" if m.get("role") == "assistant" else "user",
            "parts": [{"text": m["content"][:MAX_CHARS]}],
        }
        for m in incoming[-MAX_TURNS:]
        if isinstance(m, dict) and isinstance(m.get("content"), str) and m["content"].strip()
    ]
    if not contents or contents[-1]["role"] != "user":
        return jsonify(error="Last message must be from the user."), 400

    payload = {
        "systemInstruction": {"parts": [{"text": PERSONA}]},
        "contents": contents,
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 400},
    }

    r = None
    for model in MODELS:
        try:
            r = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                headers={"x-goog-api-key": key},
                json=payload,
                timeout=12,
            )
        except requests.RequestException:
            continue
        if r.status_code not in (429, 503):
            break
    if r is None:
        return jsonify(error="Network hiccup. Please try again."), 502

    if r.status_code in (429, 503):
        return jsonify(error="I'm getting a lot of questions right now. Please try again in a moment."), 503
    if not r.ok:
        return jsonify(error="Something went wrong reaching my brain. Please try again."), 502

    try:
        parts = r.json()["candidates"][0]["content"]["parts"]
        reply = "".join(p.get("text", "") for p in parts).strip()
    except (KeyError, IndexError, ValueError):
        reply = ""
    if not reply:
        return jsonify(error="I didn't catch that. Could you ask again?"), 502
    return jsonify(reply=reply)


if __name__ == "__main__":
    app.run(debug=True, port=int(os.environ.get("PORT", 3000)))
