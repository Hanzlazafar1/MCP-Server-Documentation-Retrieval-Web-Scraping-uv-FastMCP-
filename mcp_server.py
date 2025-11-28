# mcp_server.py - FINAL WORKING VERSION
import os
import httpx
import asyncio
import trafilatura
from dotenv import load_dotenv
from fastmcp import FastMCP

load_dotenv()

mcp = FastMCP("docs")

SERPER_URL = "https://google.serper.dev/search"

async def search_web(query: str):
    """Search using Serper API"""
    payload = {"q": query, "num": 3}
    headers = {
        "X-API-KEY": os.getenv("SERPER_API_KEY"),
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(SERPER_URL, json=payload, headers=headers)
        r.raise_for_status()
        return r.json()


async def fetch_and_clean_url(url: str) -> str:
    """Fetch URL and extract clean text using trafilatura"""
    try:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            r = await client.get(url)
            html = r.text
        
        # Use trafilatura to extract clean text
        text = trafilatura.extract(
            html,
            include_comments=False,
            include_tables=True,
            favor_recall=True
        )
        
        return text if text else "No content extracted"
        
    except Exception as e:
        return f"FAILED: {e}"


docs_urls = {
    "langchain": "python.langchain.com/docs",
    "llama-index": "docs.llamaindex.ai/en/stable",
    "openai": "platform.openai.com/docs",
    "uv": "docs.astral.sh/uv",
}

@mcp.tool()
async def get_docs(query: str, library: str) -> str:
    """
    Search documentation and return relevant content.
    
    Args:
        query: Search query for documentation
        library: Library name (langchain, llama-index, openai, or uv)
    
    Returns:
        Formatted documentation content with sources
    """
    
    if library not in docs_urls:
        return f"Library '{library}' not supported. Available: {', '.join(docs_urls.keys())}"

    search_query = f"site:{docs_urls[library]} {query}"
    
    try:
        results = await search_web(search_query)
    except Exception as e:
        return f"Search failed: {e}"

    if not results.get("organic"):
        return f"No results found for query: '{query}' in {library} docs"

    output = []
    for item in results["organic"][:2]:  # Process top 2 results
        url = item.get("link")
        if not url:
            continue
        
        text = await fetch_and_clean_url(url)
        
        # Limit text length to avoid token limits
        if len(text) > 4000:
            text = text[:4000] + "\n\n...[Content truncated for length]"
        
        output.append(f"SOURCE: {url}\n\n{text}")

    if not output:
        return "Found search results but failed to extract content from pages"

    return "\n\n" + "="*80 + "\n\n".join(output)


def main():
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()