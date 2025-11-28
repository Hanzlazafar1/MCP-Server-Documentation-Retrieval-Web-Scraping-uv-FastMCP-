# utils.py
import os
import trafilatura
from dotenv import load_dotenv
from groq import Groq
import asyncio

load_dotenv()

# Use environment variable instead of hardcoded key
groq_client = Groq(api_key="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")

def clean_html_to_txt(html: str) -> str:
    try:
        extracted = trafilatura.extract(
            html,
            include_comments=False,
            include_tables=False,
            favor_recall=False
        )
        return extracted or ""
    except:
        return ""

async def get_response_from_llm(user_prompt: str, system_prompt: str, model: str) -> str:
    """
    Runs Groq call inside a background thread.
    Prevents blocking asyncio / MCP server.
    """
    def blocking_call():
        completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            model=model,
        )
        return completion.choices[0].message.content

    return await asyncio.to_thread(blocking_call)