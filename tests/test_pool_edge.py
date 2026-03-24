from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from voltricx.exceptions import InvalidNodeException, LavalinkLoadException
from voltricx.node import Node, NodeConfig
from voltricx.pool import REGIONS, Pool
from voltricx.typings.enums import LoadType, NodeStatus
from voltricx.typings.track import Playable, Playlist


@pytest.fixture(autouse=True)
def reset_pool():
    # Cleanup Pool states between tests
    Pool._Pool__nodes.clear()
    Pool._Pool__cache = None
    Pool._client = None
    Pool._default_search_source = None
    Pool._regions = REGIONS
    yield
    Pool._Pool__nodes.clear()
    Pool._Pool__cache = None
    Pool._regions = REGIONS


def make_mock_node(identifier="test_node", region="us", status=NodeStatus.connected, penalty=0):
    cfg = NodeConfig(identifier=identifier, uri="ws://test", password="test", region=region)
    n = MagicMock(spec=Node)
    n.identifier = identifier
    n.config = cfg
    n.status = status
    n.penalty = penalty
    n.connect = AsyncMock()
    n.disconnect = AsyncMock()
    n.load_tracks = AsyncMock()
    n.players = {}
    return n


@pytest.mark.asyncio
async def test_pool_connect_duplicate_node():
    node1 = make_mock_node("N1")
    Pool._Pool__nodes["N1"] = node1

    # Try adding N1 again
    await Pool._add_node(node1)
    # The connect mock should not have been called again since it skips
    node1.connect.assert_not_called()


@pytest.mark.asyncio
async def test_pool_connect_exception():
    node1 = make_mock_node("N1")
    node1.connect.side_effect = Exception("Connect failed")

    # Should safely catch exception
    await Pool._add_node(node1)
    assert "N1" not in Pool._Pool__nodes


@pytest.mark.asyncio
async def test_get_node_by_identifier():
    n1 = make_mock_node("N1")
    Pool._Pool__nodes["N1"] = n1
    assert Pool.get_node("N1") == n1

    with pytest.raises(InvalidNodeException, match="not found in Pool"):
        Pool.get_node("UNKNOWN")


@pytest.mark.asyncio
async def test_get_node_fallback_no_nodes():
    with pytest.raises(InvalidNodeException, match="No connected nodes"):
        Pool.get_node()


@pytest.mark.asyncio
async def test_get_node_region_routing():
    n1 = make_mock_node("N1", region="us", penalty=10)
    n2 = make_mock_node("N2", region="us", penalty=5)
    n3 = make_mock_node("N3", region="eu", penalty=1)

    Pool._Pool__nodes["N1"] = n1
    Pool._Pool__nodes["N2"] = n2
    Pool._Pool__nodes["N3"] = n3

    # Best US node should be n2
    assert Pool.get_node(region="us") == n2

    # Unknown region should fallback to lowest penalty overall (n3)
    assert Pool.get_node(region="asia") == n3


def test_region_from_endpoint():
    # US ('atl' is in US)
    assert Pool.region_from_endpoint("atl.discord.gg") == "us"
    # Asia ('syd' is in Asia region)
    assert Pool.region_from_endpoint("syd.discord.gg") == "asia"
    # Fallback default
    # Use 'xyz' to avoid matching 'ord' inside of 'discord' or any other substrings
    assert Pool.region_from_endpoint("xyz-endpoint") == "global"
    assert Pool.region_from_endpoint(None) == "global"


@pytest.mark.asyncio
async def test_fetch_tracks_caching():
    n1 = make_mock_node("N1")
    Pool._Pool__nodes["N1"] = n1

    # Manually configure a mock cache
    mock_cache = MagicMock()
    mock_cache.get_query.return_value = [MagicMock(spec=Playable)]
    Pool._Pool__cache = mock_cache

    res = await Pool.fetch_tracks("ytsearch:test")
    assert mock_cache.get_query.called
    assert len(res) == 1
    n1.load_tracks.assert_not_called()


@pytest.mark.asyncio
async def test_fetch_tracks_fails_over_nodes():
    n1 = make_mock_node("N1", penalty=10)
    n2 = make_mock_node("N2", penalty=5)
    Pool._Pool__nodes["N1"] = n1
    Pool._Pool__nodes["N2"] = n2

    # n2 should fail, it will then try n1
    n2.load_tracks.side_effect = Exception("Node offline")

    valid_playable = Playable(
        encoded="encoded123",
        info={
            "sourceName": "youtube",
            "title": "Title",
            "identifier": "id1",
            "author": "auth",
            "length": 10000,
            "position": 0,
            "isStream": False,
            "isSeekable": True,
            "uri": "http://test",
        },
    )

    n1.load_tracks.return_value = {
        "loadType": LoadType.track,
        "data": valid_playable.model_dump(),
    }

    res = await Pool.fetch_tracks("ytsearch:test")
    # n2 is sorted first (penalty 5), then n1 (penalty 10)
    n2.load_tracks.assert_called_once()
    n1.load_tracks.assert_called_once()

    assert isinstance(res, list)
    assert len(res) == 1
    assert res[0].identifier == "id1"


@pytest.mark.asyncio
async def test_fetch_tracks_playlist_load():
    n1 = make_mock_node("N1")
    Pool._Pool__nodes["N1"] = n1

    n1.load_tracks.return_value = {
        "loadType": LoadType.playlist,
        "data": {
            "info": {"name": "My Playlist", "selectedTrack": 0},
            "pluginInfo": {},
            "tracks": [],
        },
    }

    res = await Pool.fetch_tracks("ytpl:test")
    assert isinstance(res, Playlist)
    assert res.info.name == "My Playlist"


@pytest.mark.asyncio
async def test_fetch_tracks_search_load():
    n1 = make_mock_node("N1")
    Pool._Pool__nodes["N1"] = n1

    valid_track = {
        "encoded": "enc1",
        "info": {
            "sourceName": "yt",
            "title": "T1",
            "identifier": "id1",
            "author": "a",
            "length": 1,
            "position": 0,
            "isStream": False,
            "isSeekable": True,
            "uri": "u1",
        },
    }

    n1.load_tracks.return_value = {"loadType": LoadType.search, "data": [valid_track]}

    res = await Pool.fetch_tracks("ytsearch:test")
    assert isinstance(res, list)
    assert len(res) == 1
    assert res[0].identifier == "id1"


@pytest.mark.asyncio
async def test_fetch_tracks_empty_load():
    n1 = make_mock_node("N1")
    Pool._Pool__nodes["N1"] = n1

    n1.load_tracks.return_value = {"loadType": LoadType.empty, "data": {}}

    res = await Pool.fetch_tracks("ytsearch:test")
    assert res == []


@pytest.mark.asyncio
async def test_fetch_tracks_lavalink_error():
    n1 = make_mock_node("N1")
    Pool._Pool__nodes["N1"] = n1

    n1.load_tracks.return_value = {
        "loadType": LoadType.error,
        "data": {
            "message": "Banned from YouTube",
            "severity": "common",
            "cause": "403",
            "causeStackTrace": "Stack Trace...",
        },
    }

    with pytest.raises(LavalinkLoadException) as excinfo:
        await Pool.fetch_tracks("ytsearch:test")

    assert "Banned from YouTube" in str(excinfo.value)


@pytest.mark.asyncio
async def test_pool_connect_timeout_and_report():
    # Test connect with multiple configs and a cache config
    client = MagicMock()
    config1 = NodeConfig(identifier="N1", uri="ws://test", password="test", region="us")
    config2 = NodeConfig(identifier="N2", uri="ws://test2", password="test", region="eu")

    # We patch _add_node to simulate connecting
    async def mock_add_node(node):
        Pool._Pool__nodes[node.identifier] = node
        if node.identifier == "N1":
            node.status = NodeStatus.connected
        else:
            node.status = NodeStatus.disconnected  # Simulate failure to connect fully

    with patch.object(Pool, "_add_node", side_effect=mock_add_node):
        # Time string patch inside connect await asyncio.sleep loop to bypass 5 seconds
        with patch("asyncio.sleep", new_callable=AsyncMock):
            # We mock time to instantly exit the 5s loop
            with patch("asyncio.get_event_loop") as mock_loop:
                mock_loop.return_value.time.side_effect = [0, 6.0]  # Instant timeout

                # We can also test cosmetic report output
                nodes = await Pool.connect(
                    client=client,
                    nodes=[config1, config2],
                    cache_config={"max_gb": 1.0, "max_hours": 1.0},
                    regions={"custom": ["cst"]},
                    default_search_source="spsearch",
                )

                assert "N1" in nodes
                assert nodes["N1"].status == NodeStatus.connected
                assert nodes["N2"].status == NodeStatus.disconnected
                assert Pool._default_search_source == "spsearch"
                assert "custom" in Pool._regions


@pytest.mark.asyncio
async def test_fetch_tracks_default_source_spacing():
    n1 = make_mock_node("N1")
    Pool._Pool__nodes["N1"] = n1
    Pool._default_search_source = "ytsearch"

    n1.load_tracks.return_value = {"loadType": LoadType.empty, "data": {}}

    await Pool.fetch_tracks("never gonna give you up")
    n1.load_tracks.assert_called_with('ytsearch:"never gonna give you up"')

    await Pool.fetch_tracks("rickroll")
    n1.load_tracks.assert_called_with("ytsearch:rickroll")


@pytest.mark.asyncio
async def test_handle_node_failover_empty_players():
    # Calling failover on a node with no players should return early
    n1 = make_mock_node("N1")
    n1.players = {}
    await Pool._handle_node_failover(n1)
    # Shouldn't exception


@pytest.mark.asyncio
async def test_handle_node_failover_migration():
    n1 = make_mock_node("N1", region="us")
    n2 = make_mock_node("N2", region="us", penalty=2)
    n3 = make_mock_node("N3", region="eu", penalty=5)
    Pool._Pool__nodes["N1"] = n1
    Pool._Pool__nodes["N2"] = n2
    Pool._Pool__nodes["N3"] = n3

    mock_player = MagicMock()
    mock_player._voice_state = {"endpoint": "atl.discord.gg"}
    mock_player.migrate_to = AsyncMock()

    n1.players = {1: mock_player}

    client = MagicMock()
    Pool._client = client

    # Player should migrate to n2 (since n2 penalty=2 < n3 penalty=5)
    # Just to be extremely certain of the exact payload, we use 'us' as endpoint to guarantee US
    mock_player._voice_state = {"endpoint": "atl.discord.gg"}

    await Pool._handle_node_failover(n1)

    # Client dispatch should fire
    client.dispatch.assert_called_once()

    mock_player.migrate_to.assert_called_once_with(n2)


@pytest.mark.asyncio
async def test_handle_node_failover_no_nodes():
    n1 = make_mock_node("N1")
    Pool._Pool__nodes["N1"] = n1

    mock_player = MagicMock()
    n1.players = {1: mock_player}

    # Failover should silently abort if no other nodes
    await Pool._handle_node_failover(n1)
    mock_player.migrate_to.assert_not_called()


@pytest.mark.asyncio
async def test_close_pool():
    n1 = make_mock_node("N1")
    Pool._Pool__nodes["N1"] = n1
    Pool._Pool__cache = MagicMock()

    await Pool.close()

    n1.disconnect.assert_called_once_with(force=True)
    assert len(Pool._Pool__nodes) == 0
    assert Pool._Pool__cache is None


def test_cache_stats_and_entries_without_cache():
    Pool._Pool__cache = None
    assert Pool.get_cache_stats() == {"l1_queries": 0, "l2_tracks": 0}
    assert Pool.get_cache_entries() == {}
    assert Pool.get_random_cached_track() is None


def test_cache_stats_and_entries_with_cache():
    mock_cache = MagicMock()
    mock_cache.get_stats.return_value = {"l1_queries": 5, "l2_tracks": 10}
    mock_cache.get_entries.return_value = {"test": ["track"]}
    mock_cache.get_random_track.return_value = MagicMock(spec=Playable)
    Pool._Pool__cache = mock_cache

    assert Pool.get_cache_stats()["l1_queries"] == 5
    assert "test" in Pool.get_cache_entries()
    assert Pool.get_random_cached_track() is not None
