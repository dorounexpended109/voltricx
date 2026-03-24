import asyncio
import importlib
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest
from discord.utils import MISSING

from voltricx.exceptions import (
    ChannelTimeoutException,
    InvalidChannelStateException,
    LavalinkLoadException,
    NodeException,
)
from voltricx.filters import Filters
from voltricx.player import Player
from voltricx.typings.enums import AutoPlayMode, NodeStatus, QueueMode, TrackEndReason
from voltricx.typings.events import TrackEndEvent, TrackStartEvent
from voltricx.typings.track import Playable, Playlist  # noqa: F401


def make_node(name):
    n = MagicMock()
    n.identifier = name
    n.uri = f"http://{name}:2333"
    n.status = NodeStatus.connected
    n.penalty = 0
    n.session_id = "sess"
    n._players = {}
    n.config = MagicMock(region="global")
    n._session = AsyncMock()
    n.load_tracks = AsyncMock(return_value={"loadType": "empty", "data": {}})
    n._destroy_player = AsyncMock()
    n._update_player = AsyncMock()
    n.client = MagicMock()
    n.players = {}
    return n


@pytest.mark.asyncio
async def test_node_request_non_dict_error():
    from voltricx.node import Node
    from voltricx.typings.node import NodeConfig

    config = NodeConfig(identifier="Test", uri="http://localhost:2333", password="youshallnotpass")
    node = Node(client=MagicMock(), config=config)
    node.session_id = "sess"

    mock_resp = MagicMock()
    mock_resp.status = 404
    mock_resp.json = AsyncMock(side_effect=TypeError("fail"))
    mock_resp.text = AsyncMock(return_value="error text")
    mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_resp.__aexit__ = AsyncMock(return_value=False)

    with patch.object(node._session, "request", return_value=mock_resp):
        with pytest.raises(NodeException, match="error text"):
            await node.request("GET", "test")

    mock_resp.status = 400
    mock_resp.json = AsyncMock(return_value={"not": "an error response"})
    with patch.object(node._session, "request", return_value=mock_resp):
        with pytest.raises(NodeException):
            await node.request("GET", "test")

    from voltricx.logger import voltricx_logger

    voltricx_logger.enabled = True
    mock_resp.status = 200
    mock_resp.json = AsyncMock(return_value={})
    with patch.object(node._session, "request", return_value=mock_resp):
        await node.request("GET", "test")

    node_info_data = {
        "version": {"semver": "4.0.0", "major": 4, "minor": 0, "patch": 0},
        "buildTime": 123,
        "git": {"branch": "main", "commit": "abc", "commitTime": 123},
        "jvm": "jvm",
        "lavaplayer": "lp",
        "sourceManagers": ["sm"],
        "filters": ["f"],
        "plugins": [],
    }
    track_data = {
        "encoded": "abc",
        "info": {
            "identifier": "id",
            "isSeekable": True,
            "author": "a",
            "length": 1,
            "isStream": False,
            "position": 0,
            "title": "t",
            "sourceName": "s",
            "uri": "u",
        },
    }

    with patch.object(
        node,
        "request",
        AsyncMock(side_effect=[node_info_data, node_info_data, {}, {}, {}, {}, track_data]),
    ):
        await node.fetch_info()
        await node.refresh_info()
        await node.fetch_stats()
        await node.fetch_players()
        await node.fetch_version()
        await node.update_session()
        await node.decode_track("abc")

    node_real = Node(client=MagicMock(), config=config)
    node_real.session_id = "sess"
    mock_resp.status = 200
    mock_resp.json = AsyncMock(return_value={})
    with patch.object(node_real._session, "request", return_value=mock_resp):
        await node_real._update_player(123, data={}, replace=False)
        await node_real._destroy_player(123)


@pytest.mark.asyncio
async def test_player_disconnect_and_move():
    from voltricx.logger import voltricx_logger

    voltricx_logger.enabled = True

    n1 = make_node("N1")
    n1.session_id = "sess"
    guild = MagicMock(id=123)
    guild.change_voice_state = AsyncMock()

    from voltricx.pool import Pool

    Pool._Pool__nodes = {"N1": n1}

    with patch.dict("sys.modules", {"davey": None}):
        importlib.reload(importlib.import_module("voltricx.player"))

    from voltricx.player import Player

    p = Player(client=MISSING, channel=MagicMock(guild=guild), nodes=[n1])
    p._guild = guild

    new_chan_mock = MagicMock(id=456)
    new_chan_mock._get_voice_client_key = MagicMock(return_value=(123, 456))
    p.client.get_channel = MagicMock(return_value=new_chan_mock)

    new_channel = MagicMock(guild=guild, id=456)

    def setter(*a, **k):
        p._connected = True
        p._connection_event.set()

    new_channel.guild.change_voice_state = AsyncMock(side_effect=setter)

    await p.move_to(new_channel)
    await p.on_voice_state_update({"channel_id": 456, "guild_id": 123, "session_id": "sess"})
    assert p.channel.id == 456

    p._connected = False
    await p.disconnect()
    p._connected = True
    p._guild = None
    await p.disconnect()
    p._guild = guild
    await p.disconnect()

    p3 = Player(client=MagicMock(), channel=MagicMock(guild=guild), nodes=[n1])
    p3._guild = guild
    p3._guild.change_voice_state = AsyncMock()
    with patch.object(p3._connection_event, "wait", AsyncMock(side_effect=asyncio.TimeoutError)):
        with pytest.raises(ChannelTimeoutException):
            await p3.connect(reconnect=True, timeout=0.01)

    p3._connection_event.wait = AsyncMock()
    p3._connected = False
    with pytest.raises(ChannelTimeoutException):
        await p3.connect(reconnect=True, timeout=0.01)

    p._connected = False
    assert p._connected is False

    await p.on_voice_state_update({"channel_id": None, "guild_id": 123, "session_id": "sess"})
    p.inactive_timeout = 10
    p.inactive_timeout = None

    p2 = Player(client=MagicMock(), channel=MagicMock(guild=guild), nodes=[n1])
    p2._guild = guild
    p2._guild.change_voice_state = AsyncMock()
    with patch.object(p2, "_dispatch_voice_update", AsyncMock(side_effect=Exception("fail"))):
        await p2.on_voice_state_update({"channel_id": 1, "guild_id": 1, "session_id": "s"})

    p2._connection_event.set()
    p2._connected = True
    await p2.connect(reconnect=True)

    n2 = make_node("N2")
    n2.status = NodeStatus.connected
    await p.migrate_to(n2)

    n_busy = make_node("BUSY")
    n_busy.players = {1: 1, 2: 2}
    n_free = make_node("FREE")
    n_free.players = {}
    p_multi = Player(client=MagicMock(), channel=MagicMock(guild=guild), nodes=[n_busy, n_free])
    assert p_multi.node.identifier == "FREE"

    _ = p.ping
    p._ping = 10
    assert p.ping == 10

    _ = p.autoplay
    _ = p.is_idle
    _ = p.idle_time

    p._autoplay = AutoPlayMode.enabled
    track = Playable(
        encoded="enc",
        info={
            "identifier": "id",
            "isSeekable": True,
            "author": "a",
            "length": 1,
            "isStream": False,
            "position": 0,
            "title": "t",
            "sourceName": "s",
            "uri": "u",
        },
    )

    p.node._update_player = AsyncMock()
    await p.play(track, replace=True, filters=Filters(), populate=True)
    await p.play(None)

    p._current = None
    _ = p.position

    with pytest.raises(TypeError):
        await p.play("not a track")

    p._paused = True
    await p.pause(True)

    p._node = None
    with pytest.raises(AttributeError):
        await p.seek(1)
        await p.set_volume(50)
    p._node = n1

    await p.stop()
    p._autoplay = AutoPlayMode.enabled
    with patch.object(p.auto_queue, "get", MagicMock(return_value=track)):
        p.auto_queue._items.extend([track] * 10)
        await p._do_recommendation()

    p._autoplay = AutoPlayMode.enabled
    with patch.object(p, "_get_recommendation_seeds", return_value=[track]):
        with patch.object(Pool, "fetch_tracks", AsyncMock(return_value=[track])):
            await p._do_recommendation()

    # Hit handler methods
    event_start = TrackStartEvent(
        op="event", type="TrackStartEvent", guildId=str(guild.id), track=track
    )
    await p._handle_track_start(event_start)

    # End reasons
    event_end = TrackEndEvent(
        op="event",
        type="TrackEndEvent",
        guildId=str(guild.id),
        track=track,
        reason=TrackEndReason.finished,
    )
    p.queue.mode = QueueMode.loop
    await p._handle_track_end(event_end)
    p.queue.mode = QueueMode.loop_all
    await p._handle_track_end(event_end)
    p._autoplay = AutoPlayMode.enabled
    await p._handle_track_end(event_end)

    p._guild = None
    with pytest.raises(InvalidChannelStateException):
        await p.move_to(new_channel)
    p._guild = guild

    await p.on_voice_state_update({"channel_id": 456, "guild_id": 123, "session_id": "sess"})
    await p.on_voice_server_update({"token": "tok", "endpoint": "end", "guild_id": 123})

    await p._destroy()
    repr(p)


@pytest.mark.asyncio
async def test_pool_and_queue_extra():
    from voltricx.pool import Pool
    from voltricx.typings.common import HyperCacheConfig
    from voltricx.typings.node import NodeConfig

    Pool._Pool__nodes = {}

    async def mock_connect(self):
        self.status = NodeStatus.connected

    with patch("voltricx.node.Node.connect", mock_connect):
        await Pool.connect(
            client=MagicMock(),
            nodes=[NodeConfig(identifier="P1", uri="http://localhost:2333", password="pw")],
            cache_config=HyperCacheConfig(),
        )

    n_slow = make_node("SLOW")
    n_slow.status = NodeStatus.disconnected

    async def gradual_connect():
        await asyncio.sleep(0.1)
        n_slow.status = NodeStatus.connected

    with patch.dict("voltricx.pool.Pool._Pool__nodes", {"SLOW": n_slow}):
        asyncio.create_task(gradual_connect())
        await Pool.connect(client=MagicMock(), nodes=[])

    Pool._Pool__nodes = {}  # Clear everything for fresh mocks
    n1 = make_node("F1")
    n1.status = NodeStatus.connected
    Pool._Pool__nodes["F1"] = n1

    err_data = {
        "message": "fail",
        "severity": "common",
        "cause": "c",
        "causeStackTrace": "stack",
    }
    with patch.object(Pool, "get_node", return_value=n1):
        with patch.object(
            n1,
            "load_tracks",
            AsyncMock(return_value={"loadType": "error", "data": err_data}),
        ):
            with pytest.raises(LavalinkLoadException):
                await Pool.fetch_tracks("q", node=None)

    with patch("voltricx.pool.Pool.get_node", return_value=n1):
        p1 = Player(client=MagicMock(), channel=MagicMock(guild=MagicMock(id=123)), nodes=[n1])
    n1.players[123] = p1
    with patch.dict("voltricx.pool.Pool._Pool__nodes", {"F1": n1, "F2": make_node("F2")}):
        Pool.get_node("F2").status = NodeStatus.connected
        p1._node = n1
        await Pool._handle_node_failover(n1)

    Pool.get_cache_stats()
    Pool.get_cache_entries()
    Pool.get_random_cached_track()
    Pool.get_node(region="global")
    Pool.export_cache_data()
    with patch.object(Pool, "close", AsyncMock()):
        await Pool.close()

    from voltricx.queue import Queue

    track = Playable(
        encoded="enc",
        info={
            "identifier": "id",
            "isSeekable": True,
            "author": "a",
            "length": 1,
            "isStream": False,
            "position": 0,
            "title": "t",
            "sourceName": "s",
            "uri": "u",
        },
    )
    q = Queue()
    q.put(track)
    _ = q[0]
    _ = q[0:1]
    _ = reversed(q)
    q._history.put([track] * 300)
    q.history.clear()
    q.put([track])
    q.pop()
    q.pop()


@pytest.mark.asyncio
async def test_utils_extra():
    from voltricx.utils import build_basic_layout

    build_basic_layout("desc", title="t", accent_color=discord.Color.red())
    build_basic_layout("desc", image_url="http://img")


@pytest.mark.asyncio
async def test_track_extra():
    from voltricx.typings.track import Playable  # noqa: F401

    info = {
        "identifier": "id",
        "isSeekable": True,
        "author": "a",
        "length": 1,
        "isStream": False,
        "position": 0,
        "title": "t",
        "sourceName": "s",
        "uri": "u",
    }
    t = Playable(encoded="enc", info=info)
    t.model_copy()
    _ = t.recommended
    # Call setter directly because model is frozen
    Playable.extras.fset(t, {"b": 2})
    p = Playlist(info={"name": "p", "selectedTrack": -1}, tracks=[t])
    _ = p.name
    _ = p.selected
    # Playlist is not frozen, but let's be safe
    Playlist.extras.fset(p, {"a": 1})
    p_sel = Playlist(info={"name": "p", "selectedTrack": 0}, tracks=[t])
    assert p_sel.selected == 0


@pytest.mark.asyncio
async def test_main_script_logic():
    with patch("sys.argv", ["voltricx", "--version"]):
        import voltricx.__main__

        with patch("sys.stdout", MagicMock()):
            with patch("subprocess.check_output", return_value=b"java version 1.8\r\nline 2"):
                importlib.reload(voltricx.__main__)
