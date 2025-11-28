# client.py - FIXED VERSION
import asyncio
import os
from dotenv import load_dotenv
from mcp.client.stdio import stdio_client
from mcp import ClientSession, StdioServerParameters
from utils import get_response_from_llm

load_dotenv()

# Debug: Check if keys are loaded
print(f"SERPER_API_KEY loaded: {bool(os.getenv('SERPER_API_KEY'))}")
print(f"GROQ_API_KEY loaded: {bool(os.getenv('GROQ_API_KEY'))}")

# Pass ALL environment variables to subprocess
server_params = StdioServerParameters(
    command="uv",
    args=["run", "mcp_server.py"],
    env=os.environ.copy()  # Pass ALL environment variables
)

async def main():
    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            tools = await session.list_tools()
            print("Available tools:", [t.name for t in tools.tools])

            # Query
            query = "chromadb"
            library = "langchain"

            print(f"\n--- Calling get_docs tool ---")
            print(f"Query: {query}")
            print(f"Library: {library}\n")
            
            response = await session.call_tool(
                "get_docs",
                {"query": query, "library": library}
            )

            # Extract text from response
            context_text = ""
            for item in response.content:
                if hasattr(item, 'text'):
                    context_text += item.text
            
            print(f"Context length: {len(context_text)} characters")
            print(f"Preview: {context_text[:500]}...\n")

            if len(context_text) < 100:
                print("ERROR: Insufficient context received!")
                print(f"Full context: {context_text}")
                return

            user_prompt = f"Query: {query}\n\nContext:\n{context_text}"

            SYSTEM_PROMPT = """
            You are a helpful documentation assistant.
            Use ONLY the provided context to answer the query.
            If the context doesn't contain the answer, say "I don't have enough information."
            Keep SOURCE links in your answer.
            """

            print("Generating answer...")
            answer = await get_response_from_llm(
                user_prompt=user_prompt,
                system_prompt=SYSTEM_PROMPT,
                model="llama-3.1-8b-instant",
            )

            print("\n" + "="*80)
            print("ANSWER:")
            print("="*80)
            print(answer)

if __name__ == "__main__":
    asyncio.run(main())