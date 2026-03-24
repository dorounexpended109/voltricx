"""Expanded tests for voltricx.node — covering all remaining branches."""

from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from voltricx.exceptions import LavalinkException, NodeException
from voltricx.node import Node
from voltricx.typings.enums import NodeStatus
from voltricx.typings.node import CPUStats, FrameStats, NodeConfig


def make_config(**kwargs):
    defaults = dict(identifier="N1", uri="http://localhost:2333", password="test", region="us")
    defaults.update(kwargs)
    return NodeConfig(**defaults)


def make_node(**kwargs):
    cfg = make_config(**kwargs)
    client = MagicMock()
    client.user = MagicMock()
    client.user.id = 123
    node = Node(config=cfg, client=client)
    return node


# ── __repr__ and __eq__ ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_node_repr():
    n = make_node()
    r = repr(n)
    assert "N1" in r


@pytest.mark.asyncio
async def test_node_eq():
    n1 = make_node()
    n2 = make_node()
    assert n1 == n2


@pytest.mark.asyncio
async def test_node_eq_different():
    n1 = make_node(identifier="A")
    n2 = make_node(identifier="B")
    assert n1 != n2


@pytest.mark.asyncio
async def test_node_eq_non_node():
    n = make_node()
    result = n.__eq__("not a node")
    assert result is NotImplemented


# ── Properties ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_node_identifier():
    n = make_node(identifier="TestNode")
    assert n.identifier == "TestNode"


@pytest.mark.asyncio
async def test_node_uri():
    n = make_node(uri="http://myhost:2333")
    assert n.uri == "http://myhost:2333"


@pytest.mark.asyncio
async def test_node_headers_without_session():
    n = make_node()
    headers = n.headers
    assert "Authorization" in headers
    assert "Session-Id" not in headers


@pytest.mark.asyncio
async def test_node_headers_with_session():
    n = make_node()
    n.session_id = "sess123"
    headers = n.headers
    assert headers["Session-Id"] == "sess123"


@pytest.mark.asyncio
async def test_node_players_returns_copy():
    n = make_node()
    player = MagicMock()
    n._players[1] = player
    snap = n.players
    snap[999] = MagicMock()
    assert 999 not in n._players


# ── penalty ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_penalty_disconnected():
    n = make_node()
    n.status = NodeStatus.disconnected
    assert n.penalty == 9e30


@pytest.mark.asyncio
async def test_penalty_connected_no_stats():
    n = make_node()
    n.status = NodeStatus.connected
    assert n.penalty == 9e30


@pytest.mark.asyncio
async def test_penalty_connected_with_cpu():
    n = make_node()
    n.status = NodeStatus.connected
    n.stats_cpu = CPUStats(cores=4, systemLoad=0.1, lavalinkLoad=0.05)
    n.stats_frames = None
    n.playing_count = 2
    penalty = n.penalty
    assert penalty > 0
    assert penalty < 9e30


@pytest.mark.asyncio
async def test_penalty_connected_with_frames():
    n = make_node()
    n.status = NodeStatus.connected
    n.stats_cpu = CPUStats(cores=4, systemLoad=0.2, lavalinkLoad=0.1)
    n.stats_frames = FrameStats(sent=3000, deficit=100, nulled=50)
    n.playing_count = 0
    penalty = n.penalty
    assert penalty > 0


# ── REST helper methods ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_node_fetch_stats():
    n = make_node()
    n.request = AsyncMock(return_value={"memory": {}, "cpu": {}})
    await n.fetch_stats()
    n.request.assert_called_once_with("GET", "/v4/stats")


@pytest.mark.asyncio
async def test_node_fetch_version():
    n = make_node()
    n.request = AsyncMock(return_value="4.0.0")
    result = await n.fetch_version()
    assert result == "4.0.0"


@pytest.mark.asyncio
async def test_node_load_tracks():
    n = make_node()
    n.request = AsyncMock(return_value={"loadType": "empty", "data": {}})
    await n.load_tracks("dzsearch:test")
    n.request.assert_called_once_with(
        "GET", "/v4/loadtracks", params={"identifier": "dzsearch:test"}
    )


@pytest.mark.asyncio
async def test_node_update_session():
    n = make_node()
    n.session_id = "sess1"
    n.request = AsyncMock(return_value={})
    await n.update_session(resuming=True, resume_timeout=60)
    n.request.assert_called_once()


@pytest.mark.asyncio
async def test_node_update_session_no_session_raises():
    n = make_node()
    with pytest.raises(NodeException, match="session ID"):
        await n.update_session()


@pytest.mark.asyncio
async def test_node_fetch_player_no_session():
    n = make_node()
    result = await n.fetch_player(guild_id=123)
    assert result is None


@pytest.mark.asyncio
async def test_node_fetch_players_no_session():
    n = make_node()
    result = await n.fetch_players()
    assert result == []


@pytest.mark.asyncio
async def test_node_get_player():
    n = make_node()
    player = MagicMock()
    n._players[111] = player
    assert n.get_player(111) is player


@pytest.mark.asyncio
async def test_node_get_player_not_found():
    n = make_node()
    assert n.get_player(999) is None


@pytest.mark.asyncio
async def test_node_update_player_no_session():
    n = make_node()
    with pytest.raises(NodeException, match="Session ID"):
        await n._update_player(123, data={"paused": True})


@pytest.mark.asyncio
async def test_node_destroy_player_no_session():
    n = make_node()
    await n._destroy_player(123)  # should not raise


@pytest.mark.asyncio
async def test_node_request_success_json():
    """Test request() on a successful 200 response."""
    n = make_node()

    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.json = AsyncMock(return_value={"result": "ok"})

    class _FakeCM:
        async def __aenter__(self):
            return mock_resp

        async def __aexit__(self, *a):
            pass

    n._session = MagicMock()
    n._session.request = MagicMock(return_value=_FakeCM())
    result = await n.request("GET", "/v4/stats")
    assert result == {"result": "ok"}


@pytest.mark.asyncio
async def test_node_request_204_returns_none():
    """Test request() on a 204 No Content response."""
    n = make_node()

    mock_resp = MagicMock()
    mock_resp.status = 204

    class _FakeCM:
        async def __aenter__(self):
            return mock_resp

        async def __aexit__(self, *a):
            pass

    n._session = MagicMock()
    n._session.request = MagicMock(return_value=_FakeCM())
    result = await n.request("DELETE", "/v4/sessions/s1/players/123")
    assert result is None


@pytest.mark.asyncio
async def test_node_request_error_raises_lavalink_exception():
    """Test that request() raises LavalinkException on 4xx response."""
    n = make_node()

    mock_resp = MagicMock()
    mock_resp.status = 404
    mock_resp.json = AsyncMock(
        return_value={
            "timestamp": 0,
            "status": 404,
            "error": "Not Found",
            "path": "/test",
            "trace": None,
            "message": "Not found",
        }
    )

    class _FakeCM:
        async def __aenter__(self):
            return mock_resp

        async def __aexit__(self, *a):
            pass

    n._session = MagicMock()
    n._session.request = MagicMock(return_value=_FakeCM())
    with pytest.raises(LavalinkException):
        await n.request("GET", "/v4/test")


@pytest.mark.asyncio
async def test_node_fetch_routeplanner_status_none():
    n = make_node()
    n.request = AsyncMock(return_value=None)
    result = await n.fetch_routeplanner_status()
    assert result is None


@pytest.mark.asyncio
async def test_node_free_address():
    n = make_node()
    n.request = AsyncMock(return_value=None)
    await n.free_address("1.2.3.4")
    n.request.assert_called_once()


@pytest.mark.asyncio
async def test_node_free_all_addresses():
    n = make_node()
    n.request = AsyncMock(return_value=None)
    await n.free_all_addresses()
    n.request.assert_called_once()


@pytest.mark.asyncio
async def test_node_decode_track():
    n = make_node()
    info_data = dict(
        identifier="id1",
        isSeekable=True,
        author="Art",
        length=180000,
        isStream=False,
        position=0,
        title="T",
        sourceName="youtube",
    )
    n.request = AsyncMock(
        return_value={
            "encoded": "enc",
            "info": info_data,
            "pluginInfo": {},
            "userData": {},
        }
    )
    result = await n.decode_track("enc")
    assert result.encoded == "enc"


@pytest.mark.asyncio
async def test_node_decode_tracks():
    n = make_node()
    info_data = dict(
        identifier="id1",
        isSeekable=True,
        author="Art",
        length=180000,
        isStream=False,
        position=0,
        title="T",
        sourceName="youtube",
    )
    n.request = AsyncMock(
        return_value=[
            {"encoded": "enc1", "info": info_data, "pluginInfo": {}, "userData": {}},
        ]
    )
    result = await n.decode_tracks(["enc1"])
    assert len(result) == 1


@pytest.mark.asyncio
async def test_node_connect_already_connected():
    n = make_node()
    n.status = NodeStatus.connected
    await n.connect()


@pytest.mark.asyncio
async def test_node_connect_failure():
    n = make_node()
    with patch("voltricx.websocket.Websocket.connect", side_effect=Exception("conn failed")):
        with pytest.raises(Exception, match="conn failed"):
            await n.connect()
    assert n.status == NodeStatus.disconnected


@pytest.mark.asyncio
async def test_node_disconnect():
    n = make_node()
    n._websocket = MagicMock()
    n._websocket.close = AsyncMock()
    await n.disconnect()
    assert n.status == NodeStatus.disconnected


@pytest.mark.asyncio
async def test_node_refresh_info_alias():
    n = make_node()
    with patch.object(n, "fetch_info", new_callable=AsyncMock) as mock_fi:
        mock_fi.return_value = MagicMock()
        await n.refresh_info()
        mock_fi.assert_called_once()


@pytest.mark.asyncio
async def test_node_request_content_type_error():
    n = make_node()
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.json = AsyncMock(side_effect=aiohttp.ContentTypeError(None, None))
    mock_resp.text = AsyncMock(return_value="raw text")

    class _FakeCM:
        async def __aenter__(self):
            return mock_resp

        async def __aexit__(self, *a):
            pass

    n._session = MagicMock()
    n._session.request = MagicMock(return_value=_FakeCM())
    result = await n.request("GET", "/test")
    assert result == "raw text"


@pytest.mark.asyncio
async def test_node_request_non_json_error():
    n = make_node()
    mock_resp = MagicMock()
    mock_resp.status = 400
    mock_resp.json = AsyncMock(side_effect=ValueError("not json"))
    mock_resp.text = AsyncMock(return_value="not json")

    class _FakeCM:
        async def __aenter__(self):
            return mock_resp

        async def __aexit__(self, *a):
            pass

    n._session = MagicMock()
    n._session.request = MagicMock(return_value=_FakeCM())
    with pytest.raises(NodeException, match="not json"):
        await n.request("GET", "/test")


@pytest.mark.asyncio
async def test_node_fetch_routeplanner_404():
    n = make_node()
    # Mock request to raise LavalinkException with 404
    n.request = AsyncMock(side_effect=LavalinkException(data=MagicMock(status=404)))
    result = await n.fetch_routeplanner_status()
    assert result is None


@pytest.mark.asyncio
async def test_node_fetch_routeplanner_other_error():
    n = make_node()
    n.request = AsyncMock(side_effect=LavalinkException(data=MagicMock(status=500)))
    with pytest.raises(LavalinkException):
        await n.fetch_routeplanner_status()


@pytest.mark.asyncio
async def test_node_fetch_player_404():
    n = make_node()
    n.session_id = "sess"
    n.request = AsyncMock(side_effect=LavalinkException(data=MagicMock(status=404)))
    result = await n.fetch_player(123)
    assert result is None


@pytest.mark.asyncio
async def test_node_fetch_player_other_error():
    n = make_node()
    n.session_id = "sess"
    n.request = AsyncMock(side_effect=LavalinkException(data=MagicMock(status=500)))
    with pytest.raises(LavalinkException):
        await n.fetch_player(123)


@pytest.mark.asyncio
async def test_node_disconnect_force():
    n = make_node()
    mock_player = MagicMock()
    mock_player.disconnect = AsyncMock()
    n._players[1] = mock_player
    n._websocket = MagicMock()
    n._websocket.close = AsyncMock()

    await n.disconnect(force=True)
    mock_player.disconnect.assert_called_once()
    assert 1 not in n._players


@pytest.mark.asyncio
async def test_node_disconnect_soft_with_players():
    n = make_node()
    n.session_id = "sess"
    n._players[1] = MagicMock()
    n._websocket = MagicMock()
    n._websocket.close = AsyncMock()

    with patch.object(n, "_destroy_player", new_callable=AsyncMock) as mock_destroy:
        await n.disconnect(force=False)
        mock_destroy.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_node_disconnect_soft_destroy_error():
    n = make_node()
    n.session_id = "sess"
    n._players[1] = MagicMock()
    n._websocket = MagicMock()
    n._websocket.close = AsyncMock()

    with patch.object(n, "_destroy_player", side_effect=Exception("oops")):
        await n.disconnect(force=False)  # Should not raise
