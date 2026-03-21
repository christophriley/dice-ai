#!/usr/bin/env python3
"""
Dice AI Job Search Agent

A conversational agent that connects to Dice.com's MCP server and uses
Claude to search for tech jobs via natural language.
"""

import os
import anyio
import anthropic
from anthropic.lib.tools.mcp import async_mcp_tool
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from dotenv import load_dotenv

load_dotenv()

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


async def run_agent() -> None:
    print("=" * 55)
    print("  Dice AI Job Search Agent")
    print("  Powered by Claude Opus 4.6 + Dice MCP Server")
    print("=" * 55)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise SystemExit(
            "Error: ANTHROPIC_API_KEY is not set. "
            "Copy .env.example to .env and add your key."
        )

    print("\nConnecting to Dice MCP server...", end="", flush=True)

    try:
        async with streamable_http_client(DICE_MCP_URL) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()

                tools_result = await session.list_tools()
                tool_names = [t.name for t in tools_result.tools]
                print(f" connected!\nAvailable tools: {', '.join(tool_names)}\n")

                client = anthropic.AsyncAnthropic(api_key=api_key)
                mcp_tools = [async_mcp_tool(t, session) for t in tools_result.tools]

                messages: list[dict] = []
                print("Describe the kind of job you're looking for.")
                print("Type 'quit' to exit.\n")

                while True:
                    try:
                        user_input = input("You: ").strip()
                    except (EOFError, KeyboardInterrupt):
                        print("\nGoodbye!")
                        break

                    if not user_input:
                        continue
                    if user_input.lower() in ("quit", "exit", "q"):
                        print("Good luck with your search!")
                        break

                    messages.append({"role": "user", "content": user_input})

                    # The tool runner handles the full agentic loop:
                    # Claude → tool_use request → MCP call → result → final response
                    runner = client.beta.messages.tool_runner(
                        model=MODEL,
                        max_tokens=4096,
                        thinking={"type": "adaptive"},
                        system=SYSTEM_PROMPT,
                        tools=mcp_tools,
                        messages=messages,
                    )

                    print("\nAssistant: ", flush=True)
                    final_text = ""

                    async for message in runner:
                        # Show a progress indicator when Claude calls the search tool
                        if any(b.type == "tool_use" for b in message.content):
                            print("  [Searching Dice...]\n", flush=True)

                        for block in message.content:
                            if block.type == "text":
                                print(block.text, flush=True)
                                final_text = block.text

                    print()

                    # Keep the assistant's final reply in conversation history
                    if final_text:
                        messages.append({"role": "assistant", "content": final_text})

    except* ConnectionError as eg:
        print(f"\nCould not reach the Dice MCP server: {eg.exceptions[0]}")
    except* Exception as eg:
        print(f"\nUnexpected error: {eg.exceptions[0]}")
        print(eg.exceptions)


def main() -> None:
    anyio.run(run_agent)


if __name__ == "__main__":
    main()
