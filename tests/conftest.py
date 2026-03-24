from unittest.mock import AsyncMock, MagicMock

import aiohttp
import discord
import pytest

from voltricx import Node, NodeConfig, Pool


@pytest.fixture
def mock_client():
    client = MagicMock(spec=discord.Client)
    client.user = MagicMock()
    client.user.id = 123456789
    client.dispatch = MagicMock()
    return client


@pytest.fixture
def node_config():
    return NodeConfig(
        identifier="test_node",
        uri="http://localhost:2333",
        password="youshallnotpass",
        region="us",
    )


@pytest.fixture
def mock_node(mock_client, node_config):
    mock_session = AsyncMock(spec=aiohttp.ClientSession)
    node = Node(config=node_config, client=mock_client, session=mock_session)
    node.status = MagicMock()
    return node


@pytest.fixture
def mock_guild():
    guild = MagicMock(spec=discord.Guild)
    guild.id = 111222333
    return guild


@pytest.fixture
def mock_voice_channel(mock_guild):
    channel = MagicMock(spec=discord.VoiceChannel)
    channel.guild = mock_guild
    channel.id = 444555666
    return channel


@pytest.fixture(autouse=True)
def cleanup_pool():
    yield
    # Sync cleanup of Pool states to prevent leakage without breaking sync tests
    try:
        Pool._Pool__nodes.clear()
        Pool._Pool__cache = None
    except Exception:
        pass
