#!/usr/bin/env python3
"""
Dice AI Job Search - Flask API
"""

import asyncio
import os
import uuid

import anthropic
from anthropic.lib.tools.mcp import async_mcp_tool
from anthropic.types.beta import BetaMessageParam
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

load_dotenv()

app = Flask(__name__)
CORS(app)

# In-memory session store: session_id -> list of messages
sessions: dict[str, list[BetaMessageParam]] = {}

DICE_MCP_URL = "https://mcp.dice.com/mcp"
MODEL = "claude-opus-4-6"

SYSTEM_PROMPT = """\
You are a helpful tech job search assistant with direct, real-time access to Dice's \
job database — the leading platform for tech professionals.

When a user describes a job they are looking for, use the search_jobs tool to find \
relevant listings. After retrieving results, present them clearly and conversationally:

- Job title and company name
- Location and workplace type (remote / hybrid / on-site)
- Key skills or requirements mentioned
- How recently the role was posted

If the user's request is vague, ask one targeted follow-up question to narrow it down \
(e.g. preferred location, remote vs. on-site, years of experience, or specific stack). \
Keep the conversation friendly and focused on helping them land their next role.\
"""


async def _process_message(messages: list[BetaMessageParam]) -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY is not set")

    async with streamable_http_client(DICE_MCP_URL) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools_result = await session.list_tools()
            client = anthropic.AsyncAnthropic(api_key=api_key)
            mcp_tools = [async_mcp_tool(t, session) for t in tools_result.tools]

            runner = client.beta.messages.tool_runner(
                model=MODEL,
                max_tokens=4096,
                thinking={"type": "adaptive"},
                system=SYSTEM_PROMPT,
                tools=mcp_tools,
                messages=messages,
            )

            final_text = ""
            async for message in runner:
                for block in message.content:
                    if block.type == "text":
                        final_text = block.text

            return final_text


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    session_id = data.get("session_id") or str(uuid.uuid4())

    if not message:
        return jsonify({"error": "message is required"}), 400

    if session_id not in sessions:
        sessions[session_id] = []

    sessions[session_id].append({"role": "user", "content": message})

    try:
        reply = asyncio.run(_process_message(sessions[session_id]))
        sessions[session_id].append({"role": "assistant", "content": reply})

        return jsonify({"reply": reply, "session_id": session_id})
    except ValueError as e:
        return jsonify({"error": str(e)}), 500
    except ConnectionError as e:
        return jsonify({"error": f"\nCould not reach the Dice MCP server: {e}"}), 500
    except Exception as e:
        root = e
        while isinstance(root, ExceptionGroup):
            root = root.exceptions[0]
        return jsonify({"error": str(root), "type": type(root).__name__}), 500

    


@app.route("/api/chat/<session_id>", methods=["DELETE"])
def clear_session(session_id: str):
    sessions.pop(session_id, None)
    return jsonify({"status": "cleared", "session_id": session_id})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(debug=True)
