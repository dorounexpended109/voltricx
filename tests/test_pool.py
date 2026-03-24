import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from voltricx import NodeStatus, Pool


@pytest.mark.asyncio
async def test_pool_connect(mock_client, node_config):
    # Mock Node.connect to avoid real websocket connection
    with patch("voltricx.node.Node.connect", new_callable=AsyncMock):
        nodes = [node_config]

        # We need to mock the node status change because Pool.connect waits for it
        def side_effect(*args, **kwargs):
            node = Pool.get_node("test_node")
            node.status = NodeStatus.connected
            return asyncio.Future()  # dummy

        # Actually Pool.connect waits for node.status == NodeStatus.connected
        # We can't easily change it from inside connect because it iterates over cls.__nodes

        # Let's mock Pool._add_node instead to control the process
        with patch("voltricx.Pool._add_node", new_callable=AsyncMock) as mock_add:

            async def mock_add_node(node):
                Pool._Pool__nodes[node.identifier] = node
                node.status = NodeStatus.connected

            mock_add.side_effect = mock_add_node

            await Pool.connect(client=mock_client, nodes=nodes)

            assert "test_node" in Pool.nodes()
            assert Pool.get_node("test_node").status == NodeStatus.connected


@pytest.mark.asyncio
async def test_pool_fetch_tracks_cached():
    # Setup cache
    mock_cache = MagicMock()
    mock_cache.get_query.return_value = ["track1"]
    Pool._Pool__cache = mock_cache

    result = await Pool.fetch_tracks("some query")
    assert result == ["track1"]
    mock_cache.get_query.assert_called_with("some query")


@pytest.mark.asyncio
async def test_pool_fetch_tracks_no_nodes(mock_client):
    Pool._Pool__nodes = {}
    with pytest.raises(Exception):  # InvalidNodeException
        await Pool.fetch_tracks("query")


@pytest.mark.asyncio
async def test_region_from_endpoint():
    # Reset regions to ensure default state
    Pool._regions = {"asia": ["bom", "maa"], "eu": ["ams", "fra"], "us": ["iad", "atl"]}
    assert Pool.region_from_endpoint("iad123.discord.gg") == "us"
    assert Pool.region_from_endpoint("ams456.discord.gg") == "eu"
    assert Pool.region_from_endpoint("unknown.discord.gg") == "global"
