"""Tests for voltricx.websocket — targeting 100% branch coverage."""

from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from voltricx.typings.enums import NodeStatus
from voltricx.websocket import Websocket


@pytest.fixture
def mock_node():
    node = MagicMock()
    node.identifier = "TestNode"
    node.uri = "http://localhost:2333"
    node.headers = {"Authorization": "youshallnotpass"}
    node.session_id = None
    node.status = NodeStatus.disconnected
    node._session = MagicMock()
    node.client = MagicMock()
    node.get_player = MagicMock(return_value=None)
    return node


def test_websocket_init(mock_node):
    ws = Websocket(node=mock_node)
    assert ws.node is mock_node
    assert ws.socket is None
    assert ws.backoff is not None


@pytest.mark.asyncio
async def test_websocket_connect_silent(mock_node):
    ws = Websocket(node=mock_node)
    mock_socket = AsyncMock()
    mock_node._session.ws_connect = AsyncMock(return_value=mock_socket)

    await ws.connect(silent=True)

    # Should create keep alive task
    assert getattr(ws, "_keep_alive_task", None) is not None
    # Cleanup
    ws._keep_alive_task.cancel()


@pytest.mark.asyncio
async def test_websocket_connect_with_session_id(mock_node):
    mock_node.session_id = "existing_session"
    ws = Websocket(node=mock_node)
    mock_socket = AsyncMock()
    mock_node._session.ws_connect = AsyncMock(return_value=mock_socket)

    await ws.connect(silent=True)

    mock_node._session.ws_connect.assert_called_with(
        "ws://localhost:2333/v4/websocket",
        headers={"Authorization": "youshallnotpass", "Session-Id": "existing_session"},
    )
    ws._keep_alive_task.cancel()


@pytest.mark.asyncio
async def test_websocket_connect_closed_early(mock_node):
    ws = Websocket(node=mock_node)
    ws._closed = True
    await ws.connect()
    # Should return without doing anything
    assert ws.socket is None


@pytest.mark.asyncio
async def test_websocket_connect_retry_logic(mock_node):
    ws = Websocket(node=mock_node)
    ws.backoff = MagicMock()
    ws.backoff.calculate.return_value = 0.01  # extremely short delay for testing

    mock_socket = AsyncMock()
    # Fail first time, succeed second time
    mock_node._session.ws_connect = AsyncMock(
        side_effect=[Exception("Connection refused"), mock_socket]
    )

    await ws.connect(silent=False)

    assert mock_node._session.ws_connect.call_count == 2
    ws._keep_alive_task.cancel()


@pytest.mark.asyncio
async def test_handle_message_invalid_payload(mock_node, caplog):
    ws = Websocket(node=mock_node)
    await ws._handle_message({"invalid": "data"})
    assert "Failed to validate Lavalink payload" in caplog.text


@pytest.mark.asyncio
async def test_handle_message_ready(mock_node):
    ws = Websocket(node=mock_node)
    data = {"op": "ready", "resumed": False, "sessionId": "new_session_123"}

    await ws._handle_message(data)

    assert mock_node.session_id == "new_session_123"
    assert mock_node.status == NodeStatus.connected
    mock_node.client.dispatch.assert_called_with("voltricx_node_ready", mock_node)


@pytest.mark.asyncio
async def test_handle_message_stats(mock_node):
    ws = Websocket(node=mock_node)
    data = {
        "op": "stats",
        "players": 1,
        "playingPlayers": 1,
        "uptime": 12345,
        "memory": {"free": 100, "used": 200, "allocated": 300, "reservable": 400},
        "cpu": {"cores": 4, "systemLoad": 0.5, "lavalinkLoad": 0.1},
        "frameStats": {"sent": 100, "nulled": 0, "deficit": 0},
    }

    await ws._handle_message(data)

    assert mock_node.playing_count == 1
    assert mock_node.stats_cpu.cores == 4
    mock_node.client.dispatch.assert_called_with("voltricx_node_stats", mock_node)


@pytest.mark.asyncio
async def test_handle_message_player_update(mock_node):
    ws = Websocket(node=mock_node)
    mock_player = MagicMock()
    mock_node.get_player.return_value = mock_player

    data = {
        "op": "playerUpdate",
        "guildId": "12345",
        "state": {"time": 123, "position": 456, "connected": True, "ping": 10},
    }

    await ws._handle_message(data)

    mock_node.get_player.assert_called_with(12345)
    mock_player._update_state.assert_called_once()


@pytest.mark.asyncio
async def test_handle_message_player_update_no_player(mock_node):
    ws = Websocket(node=mock_node)
    mock_node.get_player.return_value = None

    data = {
        "op": "playerUpdate",
        "guildId": "12345",
        "state": {"time": 123, "position": 456, "connected": True, "ping": 10},
    }

    await ws._handle_message(data)
    # Should not crash


@pytest.mark.asyncio
async def test_handle_event_track_start(mock_node):
    ws = Websocket(node=mock_node)
    mock_player = MagicMock()
    mock_node.get_player.return_value = mock_player

    data = {
        "op": "event",
        "type": "TrackStartEvent",
        "guildId": "12345",
        "track": {
            "encoded": "enc1",
            "info": {
                "identifier": "id",
                "isSeekable": True,
                "author": "a",
                "length": 1,
                "isStream": False,
                "position": 0,
                "title": "t",
                "sourceName": "s",
            },
        },
    }

    await ws._handle_message(data)
    mock_player.client.dispatch.assert_called_with(
        "voltricx_track_start", mock_player, mock_player.client.dispatch.call_args[0][2]
    )


@pytest.mark.asyncio
async def test_handle_event_track_end(mock_node):
    ws = Websocket(node=mock_node)
    mock_player = MagicMock()
    mock_player._handle_track_end = AsyncMock()
    mock_node.get_player.return_value = mock_player

    data = {
        "op": "event",
        "type": "TrackEndEvent",
        "guildId": "12345",
        "track": {
            "encoded": "enc1",
            "info": {
                "identifier": "id",
                "isSeekable": True,
                "author": "a",
                "length": 1,
                "isStream": False,
                "position": 0,
                "title": "t",
                "sourceName": "s",
            },
        },
        "reason": "finished",
    }

    from voltricx.typings.enums import TrackEndReason

    await ws._handle_message(data)
    mock_player._handle_track_end.assert_called_once()
    mock_player.client.dispatch.assert_called_with(
        "voltricx_track_end",
        mock_player,
        mock_player.client.dispatch.call_args[0][2],
        TrackEndReason.finished,
    )


@pytest.mark.asyncio
async def test_handle_event_track_exception(mock_node):
    ws = Websocket(node=mock_node)
    mock_player = MagicMock()
    mock_node.get_player.return_value = mock_player

    data = {
        "op": "event",
        "type": "TrackExceptionEvent",
        "guildId": "12345",
        "track": {
            "encoded": "enc1",
            "info": {
                "identifier": "id",
                "isSeekable": True,
                "author": "a",
                "length": 1,
                "isStream": False,
                "position": 0,
                "title": "t",
                "sourceName": "s",
            },
        },
        "exception": {
            "message": "failed",
            "severity": "common",
            "cause": "unknown",
            "causeStackTrace": "",
        },
    }

    await ws._handle_message(data)
    assert mock_player.client.dispatch.call_count == 1
    assert mock_player.client.dispatch.call_args[0][0] == "voltricx_track_exception"


@pytest.mark.asyncio
async def test_handle_event_track_stuck(mock_node):
    ws = Websocket(node=mock_node)
    mock_player = MagicMock()
    mock_node.get_player.return_value = mock_player

    data = {
        "op": "event",
        "type": "TrackStuckEvent",
        "guildId": "12345",
        "track": {
            "encoded": "enc1",
            "info": {
                "identifier": "id",
                "isSeekable": True,
                "author": "a",
                "length": 1,
                "isStream": False,
                "position": 0,
                "title": "t",
                "sourceName": "s",
            },
        },
        "thresholdMs": 10000,
    }

    await ws._handle_message(data)
    mock_player.client.dispatch.assert_called_with(
        "voltricx_track_stuck",
        mock_player,
        mock_player.client.dispatch.call_args[0][2],
        10000,
    )


@pytest.mark.asyncio
async def test_handle_event_websocket_closed(mock_node):
    ws = Websocket(node=mock_node)
    mock_player = MagicMock()
    mock_player._disconnected_wait = AsyncMock()
    mock_node.get_player.return_value = mock_player

    data = {
        "op": "event",
        "type": "WebSocketClosedEvent",
        "guildId": "12345",
        "code": 4006,
        "reason": "Session invalidated",
        "byRemote": True,
    }

    await ws._handle_message(data)
    mock_player.client.dispatch.assert_called_with(
        "voltricx_websocket_closed", mock_player, 4006, "Session invalidated", True
    )
    # Async task started for wait


@pytest.mark.asyncio
async def test_handle_dave_protocol_change(mock_node):
    ws = Websocket(node=mock_node)
    mock_player = MagicMock()
    mock_player._on_dave_protocol_change = AsyncMock()
    mock_node.get_player.return_value = mock_player

    data = {
        "op": "dave",
        "type": "protocolChange",
        "guildId": "12345",
        "protocol": "JsonReady",
        "encryptionKey": "testKey",
    }

    await ws._handle_message(data)
    mock_player._on_dave_protocol_change.assert_called_once()


@pytest.mark.asyncio
async def test_handle_dave_prepare_transition(mock_node):
    ws = Websocket(node=mock_node)
    mock_player = MagicMock()
    mock_player._on_dave_prepare_transition = AsyncMock()
    mock_node.get_player.return_value = mock_player

    data = {
        "op": "dave",
        "type": "prepareTransition",
        "guildId": "12345",
        "transitionId": 1,
        "epoch": 1234567,
        "nextEncryptionKey": "newTestKey",
    }

    await ws._handle_message(data)
    mock_player._on_dave_prepare_transition.assert_called_once()


@pytest.mark.asyncio
async def test_handle_dave_no_player(mock_node):
    ws = Websocket(node=mock_node)
    mock_node.get_player.return_value = None
    data = {
        "op": "dave",
        "type": "protocolChange",
        "guildId": "12345",
        "protocol": "JsonReady",
        "encryptionKey": "xyz",
    }
    await ws._handle_message(data)
    # Should not crash


@pytest.mark.asyncio
@patch("voltricx.pool.Pool._handle_node_failover", new_callable=AsyncMock)
async def test_handle_disconnect(mock_failover, mock_node):
    ws = Websocket(node=mock_node)
    ws.connect = AsyncMock()

    await ws._handle_disconnect()

    assert mock_node.status == NodeStatus.disconnected
    mock_node.client.dispatch.assert_called_with("voltricx_node_disconnected", mock_node)
    ws.connect.assert_called_once_with(silent=True)
    # Task created for failover


@pytest.mark.asyncio
async def test_close(mock_node):
    ws = Websocket(node=mock_node)
    mock_socket = AsyncMock()
    ws.socket = mock_socket
    ws._keep_alive_task = MagicMock()

    await ws.close()

    assert ws._closed is True
    ws._keep_alive_task.cancel.assert_called_once()
    mock_socket.close.assert_called_once()
    assert ws.socket is None


@pytest.mark.asyncio
@patch("voltricx.websocket.Websocket._handle_message", new_callable=AsyncMock)
@patch("voltricx.websocket.Websocket._handle_disconnect", new_callable=AsyncMock)
async def test_keep_alive_loop(mock_disconnect, mock_handle_msg, mock_node):
    ws = Websocket(node=mock_node)

    mock_msg1 = MagicMock()
    mock_msg1.type = aiohttp.WSMsgType.TEXT
    mock_msg1.json.return_value = {"op": "ready"}

    mock_msg2 = MagicMock()
    mock_msg2.type = aiohttp.WSMsgType.CLOSED

    mock_socket = AsyncMock()
    mock_socket.closed = False
    mock_socket.receive = AsyncMock(side_effect=[mock_msg1, mock_msg2])
    ws.socket = mock_socket

    await ws._keep_alive()

    mock_handle_msg.assert_called_once_with({"op": "ready"})
    mock_disconnect.assert_called_once()


@pytest.mark.asyncio
@patch("voltricx.websocket.Websocket._handle_disconnect", new_callable=AsyncMock)
async def test_keep_alive_exception(mock_disconnect, mock_node):
    ws = Websocket(node=mock_node)

    mock_socket = AsyncMock()
    mock_socket.closed = False
    mock_socket.receive = AsyncMock(side_effect=Exception("Read error"))
    ws.socket = mock_socket

    await ws._keep_alive()

    mock_disconnect.assert_called_once()
