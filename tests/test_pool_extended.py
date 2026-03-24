"""Expanded tests for voltricx.pool — covering all remaining branches."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from voltricx import NodeStatus, Pool
from voltricx.exceptions import InvalidNodeException


def make_connected_mock_node(identifier="N1", region="us", penalty=10.0):
    node = AsyncMock()
    node.identifier = identifier
    node.uri = "http://localhost:2333"
    node.status = NodeStatus.connected
    node.config = MagicMock()
    node.config.region = region
    node.penalty = penalty
    node.players = {}
    node._players = {}
    node.disconnect = AsyncMock()
    return node


# ── get_node ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_node_by_identifier():
    node = make_connected_mock_node("MyNode")
    Pool._Pool__nodes["MyNode"] = node
    result = Pool.get_node("MyNode")
    assert result is node


@pytest.mark.asyncio
async def test_get_node_not_found_raises():
    with pytest.raises(InvalidNodeException):
        Pool.get_node("nonexistent")


@pytest.mark.asyncio
async def test_get_node_no_connected_nodes_raises():
    node = make_connected_mock_node()
    node.status = NodeStatus.disconnected
    Pool._Pool__nodes["N1"] = node
    with pytest.raises(InvalidNodeException):
        Pool.get_node()


@pytest.mark.asyncio
async def test_get_node_best_by_penalty():
    n1 = make_connected_mock_node("N1", penalty=100.0)
    n2 = make_connected_mock_node("N2", penalty=5.0)
    Pool._Pool__nodes = {"N1": n1, "N2": n2}
    result = Pool.get_node()
    assert result is n2


@pytest.mark.asyncio
async def test_get_node_by_region():
    n_us = make_connected_mock_node("US", region="us", penalty=5.0)
    n_eu = make_connected_mock_node("EU", region="eu", penalty=1.0)
    Pool._Pool__nodes = {"US": n_us, "EU": n_eu}
    result = Pool.get_node(region="us")
    assert result is n_us


@pytest.mark.asyncio
async def test_get_node_region_fallback_global():
    """If no nodes in requested region, falls back to global selection."""
    n_eu = make_connected_mock_node("EU", region="eu", penalty=5.0)
    Pool._Pool__nodes = {"EU": n_eu}
    result = Pool.get_node(region="us")  # no US nodes, should fall back
    assert result is n_eu


# ── region_from_endpoint ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_region_none_endpoint():
    assert Pool.region_from_endpoint(None) == "global"


@pytest.mark.asyncio
async def test_region_empty_endpoint():
    assert Pool.region_from_endpoint("") == "global"


# ── fetch_tracks with default search source ────────────────────────────────


@pytest.mark.asyncio
async def test_fetch_tracks_prepends_source_for_plain_query():
    n = make_connected_mock_node()
    n.load_tracks = AsyncMock(
        return_value={
            "loadType": "search",
            "data": [],
        }
    )
    Pool._Pool__nodes = {"N1": n}
    Pool._default_search_source = "dzsearch"
    result = await Pool.fetch_tracks("my song")
    assert result == []


@pytest.mark.asyncio
async def test_fetch_tracks_http_url_not_prefixed():
    n = make_connected_mock_node()
    n.load_tracks = AsyncMock(return_value={"loadType": "empty", "data": {}})
    Pool._Pool__nodes = {"N1": n}
    Pool._default_search_source = "dzsearch"
    result = await Pool.fetch_tracks("http://example.com/track")
    n.load_tracks.assert_called_once_with("http://example.com/track")
    assert result == []


@pytest.mark.asyncio
async def test_fetch_tracks_uses_region():
    n_us = make_connected_mock_node("US", region="us")
    n_us.load_tracks = AsyncMock(return_value={"loadType": "empty", "data": {}})
    n_eu = make_connected_mock_node("EU", region="eu")
    n_eu.load_tracks = AsyncMock(return_value={"loadType": "empty", "data": {}})
    Pool._Pool__nodes = {"US": n_us, "EU": n_eu}
    await Pool.fetch_tracks("query", region="us")
    n_us.load_tracks.assert_called_once()


@pytest.mark.asyncio
async def test_fetch_tracks_raises_last_exception_on_all_fail():
    n = make_connected_mock_node()
    n.load_tracks = AsyncMock(side_effect=Exception("network error"))
    Pool._Pool__nodes = {"N1": n}
    with pytest.raises(Exception, match="network error"):
        await Pool.fetch_tracks("somequery")


# ── get_cache_stats and get_cache_entries when no cache ───────────────────


@pytest.mark.asyncio
async def test_get_cache_stats_no_cache():
    stats = Pool.get_cache_stats()
    assert stats == {"l1_queries": 0, "l2_tracks": 0}


@pytest.mark.asyncio
async def test_get_cache_entries_no_cache():
    entries = Pool.get_cache_entries()
    assert entries == {}


@pytest.mark.asyncio
async def test_get_random_cached_track_no_cache():
    track = Pool.get_random_cached_track()
    assert track is None


# ── get_cache_stats with cache ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_cache_stats_with_cache():
    from voltricx.hypercache import HyperCache

    cache = HyperCache()
    Pool._Pool__cache = cache
    stats = Pool.get_cache_stats()
    assert "l1_queries" in stats


@pytest.mark.asyncio
async def test_get_cache_entries_with_cache():
    from voltricx.hypercache import HyperCache

    cache = HyperCache()
    Pool._Pool__cache = cache
    entries = Pool.get_cache_entries()
    assert isinstance(entries, dict)


@pytest.mark.asyncio
async def test_get_random_cached_track_with_cache():
    from voltricx.hypercache import HyperCache

    cache = HyperCache()
    t = MagicMock()
    t.encoded = "test"
    t.title = "Song"
    cache.put_query("q", [t])
    Pool._Pool__cache = cache
    track = Pool.get_random_cached_track()
    assert track is not None


# ── export_cache_data ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_export_cache_data_no_cache():
    data = Pool.export_cache_data()
    assert data == {"l1": {}, "l2": {}}


@pytest.mark.asyncio
async def test_export_cache_data_with_cache():
    from voltricx.hypercache import HyperCache

    cache = HyperCache()
    t = MagicMock()
    t.encoded = "enc"
    t.title = "Track"
    cache.put_query("q", [t])
    Pool._Pool__cache = cache
    data = Pool.export_cache_data()
    assert "l1" in data and "l2" in data


# ── nodes() ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_pool_nodes_returns_copy():
    n = make_connected_mock_node()
    Pool._Pool__nodes = {"N1": n}
    snapshot = Pool.nodes()
    snapshot["INJECTED"] = MagicMock()
    assert "INJECTED" not in Pool._Pool__nodes


# ── _display_report ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_display_report_mixed_status(capsys):
    n_conn = make_connected_mock_node("C1")
    n_disc = make_connected_mock_node("D1")
    n_disc.status = NodeStatus.disconnected
    Pool._Pool__nodes = {"C1": n_conn, "D1": n_disc}
    Pool._display_report()
    out = capsys.readouterr().out
    assert "CONNECTED" in out
    assert "FAILED" in out
