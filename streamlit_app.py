# streamlit_app.py

import streamlit as st
import asyncio
import os
from dotenv import load_dotenv
from mcp.client.stdio import stdio_client
from mcp import ClientSession, StdioServerParameters
from utils import get_response_from_llm

load_dotenv()

# --------------------------
# Streamlit Page Config
# --------------------------
st.set_page_config(
    page_title="AI Documentation Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------
# Sidebar
# --------------------------
st.sidebar.title("Settings")
library_options = ["langchain", "llama-index", "openai", "uv"]
library = st.sidebar.selectbox("Select Library", library_options)
query = st.sidebar.text_input("Enter your query", "")

# --------------------------
# Server Parameters
# --------------------------
server_params = StdioServerParameters(
    command="uv",
    args=["run", "mcp_server.py"],
    env=os.environ.copy()
)

# --------------------------
# Async MCP + LLM Call
# --------------------------
async def fetch_answer(query: str, library: str):
    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            # Call MCP tool
            response = await session.call_tool(
                "get_docs",
                {"query": query, "library": library}
            )

            # Extract text
            context_text = ""
            if isinstance(response.content, list):
                for item in response.content:
                    if hasattr(item, "text"):
                        context_text += item.text
            else:
                context_text = str(response.content)

            # If context too short, return immediately
            if len(context_text.strip()) < 50:
                return "No sufficient context found from documentation.", context_text

            # LLM Prompt
            user_prompt = f"Query: {query}\n\nContext:\n{context_text}"
            system_prompt = """
            You are a helpful documentation assistant.
            Use ONLY the provided context to answer the query.
            If the context doesn't contain the answer, say "I don't have enough information."
            Keep SOURCE links in your answer.
            """

            # Get LLM response
            answer = await get_response_from_llm(
                user_prompt=user_prompt,
                system_prompt=system_prompt,
                model="llama-3.1-8b-instant"
            )

            return answer, context_text

# --------------------------
# Main App Layout
# --------------------------
st.markdown("<h1 style='text-align:center;color:#4B0082;'>🤖 AI Documentation Assistant</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;color:gray;'>Ask questions about Python libraries and get precise answers from docs.</p>", unsafe_allow_html=True)

if st.button("Get Answer"):
    if not query:
        st.warning("Please enter a query!")
    else:
        with st.spinner("Fetching answer from MCP server and LLM..."):
            answer, context_text = asyncio.run(fetch_answer(query, library))

            # Display Context
            with st.expander("📄 View Extracted Context (Optional)"):
                st.write(context_text[:5000] + ("..." if len(context_text) > 5000 else ""))

            # Display LLM Answer
            st.markdown("<h3 style='color:#006400;'>💡 Answer:</h3>", unsafe_allow_html=True)
            st.markdown(answer)

# --------------------------
# Footer
# --------------------------
st.markdown(
    """
    <hr>
    <p style='text-align:center;color:gray;font-size:12px;'>
    Made with ❤️ by Hanzla Zafar
    </p>
    """,
    unsafe_allow_html=True
)
