import pytest
import pytest_asyncio
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from src.api.highlights import HighlightsAPI
from pathlib import Path
import json

@pytest_asyncio.fixture
async def api_async():
    api_instance = HighlightsAPI(api_key="test_key")
    yield api_instance
    await api_instance.close()

@pytest.mark.asyncio
async def test_get_highlights_success(api_async):
    api = api_async
    mock_response = MagicMock()
    mock_response.json.return_value = [{"id": 1, "title": "Test Highlight"}]
    mock_response.raise_for_status.return_value = None

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response
    api.client = mock_client

    highlights = await api.get_highlights()
    assert len(highlights) == 1
    assert highlights[0]["title"] == "Test Highlight"
    mock_client.get.assert_called_once()
    args, kwargs = mock_client.get.call_args
    assert args[0] == "https://api.highlightly.net/highlights"
    assert "Authorization" in kwargs["headers"]

@pytest.mark.asyncio
async def test_get_highlights_search(api_async):
    api = api_async
    mock_response = MagicMock()
    mock_response.json.return_value = []
    mock_response.raise_for_status.return_value = None

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response
    api.client = mock_client

    await api.get_highlights(search="dunk")
    mock_client.get.assert_called_once()
    args, kwargs = mock_client.get.call_args
    assert kwargs["params"] == {"search": "dunk"}

@pytest.mark.asyncio
async def test_get_by_team(api_async):
    api = api_async
    mock_response = MagicMock()
    mock_response.json.return_value = []
    mock_response.raise_for_status.return_value = None

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response
    api.client = mock_client

    await api.get_by_team("Lakers")
    mock_client.get.assert_called_once()
    args, kwargs = mock_client.get.call_args
    assert args[0] == "https://api.highlightly.net/highlights/team/Lakers"

@pytest.mark.asyncio
async def test_get_by_player(api_async):
    api = api_async
    mock_response = MagicMock()
    mock_response.json.return_value = []
    mock_response.raise_for_status.return_value = None

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response
    api.client = mock_client

    await api.get_by_player("LeBron James")
    mock_client.get.assert_called_once()
    args, kwargs = mock_client.get.call_args
    # Assuming URL encoding
    assert args[0] == "https://api.highlightly.net/highlights/player/LeBron%20James"

@pytest.mark.asyncio
async def test_download_video(api_async, tmp_path):
    api = api_async
    mock_response = AsyncMock()
    mock_response.raise_for_status = MagicMock() # Ensure this is a regular Mock to avoid warning
    mock_response.raise_for_status.return_value = None

    # aiter_bytes needs to yield bytes
    async def bytes_iterator():
        yield b"chunk1"
        yield b"chunk2"

    mock_response.aiter_bytes = bytes_iterator

    # Correctly mock the context manager for stream
    mock_client = MagicMock()

    # Define the async context manager
    class AsyncContextManager:
        async def __aenter__(self):
            return mock_response
        async def __aexit__(self, exc_type, exc, tb):
            pass

    mock_client.stream.return_value = AsyncContextManager()

    # Mock aclose as async
    mock_client.aclose = AsyncMock()

    api.client = mock_client

    save_path = tmp_path / "video.mp4"
    result = await api.download_video("http://example.com/video.mp4", save_path)

    assert result is True
    assert save_path.exists()
    content = save_path.read_bytes()
    assert content == b"chunk1chunk2"

@pytest.mark.asyncio
async def test_context_manager():
    async with HighlightsAPI(api_key="test") as api:
        assert isinstance(api, HighlightsAPI)
        api.client.aclose = AsyncMock()

    api.client.aclose.assert_called_once()
