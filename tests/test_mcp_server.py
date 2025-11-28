import unittest
from unittest.mock import patch, AsyncMock, MagicMock
import asyncio
from mcp_server import get_docs, fetch_url

class TestMcpServer(unittest.IsolatedAsyncioTestCase):
    
    @patch('mcp_server.trafilatura')
    async def test_fetch_url(self, mock_trafilatura):
        mock_trafilatura.fetch_url.return_value = "<html>content</html>"
        mock_trafilatura.extract.return_value = "extracted content"
        
        result = await fetch_url("http://example.com")
        self.assertEqual(result, "extracted content")
        
    @patch('mcp_server.trafilatura')
    async def test_fetch_url_fail(self, mock_trafilatura):
        mock_trafilatura.fetch_url.return_value = None
        
        result = await fetch_url("http://example.com")
        self.assertIsNone(result)

    @patch('mcp_server.search_web')
    @patch('mcp_server.fetch_url')
    async def test_get_docs_success(self, mock_fetch_url, mock_search_web):
        mock_search_web.return_value = {
            "organic": [
                {"link": "http://example.com/1"},
                {"link": "http://example.com/2"}
            ]
        }
        mock_fetch_url.side_effect = ["Content 1", "Content 2"]
        
        result = await get_docs("query", "langchain")
        
        self.assertIn("SOURCE: http://example.com/1", result)
        self.assertIn("Content 1", result)
        self.assertIn("SOURCE: http://example.com/2", result)
        self.assertIn("Content 2", result)

    @patch('mcp_server.search_web')
    async def test_get_docs_no_results(self, mock_search_web):
        mock_search_web.return_value = {"organic": []}
        
        result = await get_docs("query", "langchain")
        self.assertEqual(result, "no results found")

    async def test_get_docs_invalid_library(self):
        with self.assertRaises(ValueError):
            await get_docs("query", "invalid_lib")

if __name__ == '__main__':
    unittest.main()
