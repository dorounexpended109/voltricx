"""Tests for Player edge cases covering remaining branches for 100% coverage."""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from voltricx.node import Node
from voltricx.player import Player
from voltricx.typings.enums import AutoPlayMode, NodeStatus, QueueMode, TrackEndReason
from voltricx.typings.events import TrackEndEvent
from voltricx.typings.player import PlayerState


@pytest.fixture(autouse=True)
def clean_pool():
    from voltricx.pool import Pool

    Pool._Pool__nodes = {}


def make_mock_node(identifier="N1"):
    node = AsyncMock(spec=Node)
    node.identifier = identifier
    node.status = NodeStatus.connected
    node._players = {}
    node.client = MagicMock()
    # Ensure _update_player returns None so it doesn't try to mock await magic
    node._update_player = AsyncMock(return_value=None)
    node._destroy_player = AsyncMock(return_value=None)
    return node


def make_mock_track(encoded="enc1", length=180000, identifier="id1"):
    from voltricx.typings.track import Playable, TrackInfo

    info = TrackInfo(
        identifier=identifier,
        isSeekable=True,
        author="Author",
        length=length,
        isStream=False,
        position=0,
        title="Title",
        sourceName="youtube",
    )
    return Playable(encoded=encoded, info=info)


def make_player():
    from voltricx.pool import Pool

    node1 = make_mock_node("N1")
    Pool._Pool__nodes["N1"] = node1

    client = MagicMock()
    channel = MagicMock()
    channel.guild = MagicMock()
    channel.guild.id = 12345
    return Player(client=client, channel=channel, nodes=[node1])


# --- Initialization / Node Selection Branches ---


@pytest.mark.asyncio
async def test_player_init_no_connected_nodes():
    node1 = make_mock_node("N1")
    node1.status = NodeStatus.disconnected

    from voltricx.pool import Pool

    Pool._Pool__nodes["N1"] = node1

    # Mocking internal __nodes directly to bypass property read checks
    with patch.dict(Pool._Pool__nodes, {"N1": node1}):
        client = MagicMock()
        channel = MagicMock()
        with pytest.raises(Exception, match="No connected nodes available in Pool"):
            Player(client=client, channel=channel, nodes=[node1])


@pytest.mark.asyncio
async def test_player_init_picks_lightest_node():
    from voltricx.pool import Pool

    node1 = make_mock_node("N1")
    node1._players = {1: MagicMock(), 2: MagicMock()}
    node2 = make_mock_node("N2")
    node2._players = {1: MagicMock()}

    Pool._Pool__nodes["N1"] = node1
    node2._players = {1: MagicMock()}

    Pool._Pool__nodes["N1"] = node1
    Pool._Pool__nodes["N2"] = node2

    with patch.dict(Pool._Pool__nodes, {"N1": node1, "N2": node2}):
        client = MagicMock()
        channel = MagicMock()

        # Test evaluates n.players (len(n._players)) inside init
        node1.players = {1: MagicMock(), 2: MagicMock()}
        node2.players = {1: MagicMock()}

        with patch("voltricx.pool.Pool.nodes", {"N1": node1, "N2": node2}):
            p = Player(client=client, channel=channel, nodes=[node1, node2])
            assert p._node is node2


# --- Properties & Simple Methods ---


@pytest.mark.asyncio
async def test_player_is_idle():
    p = make_player()
    p._connected = True
    p._current = None
    assert p.is_idle is True


@pytest.mark.asyncio
async def test_player_idle_time_live():
    p = make_player()
    p._idle_since = time.monotonic() - 5.0
    assert p.idle_time >= 5.0


@pytest.mark.asyncio
async def test_player_idle_time_none():
    p = make_player()
    p._idle_since = None
    assert p.idle_time == 0.0


@pytest.mark.asyncio
async def test_player_update_state():
    p = make_player()
    state = PlayerState(time=1000, position=5000, connected=True, ping=42)
    p._update_state(state)
    assert p._last_position == 5000
    assert p._ping == 42
    assert p._connected is False  # state ping/connected doesn't update p._connected


# --- Voice Update Flow ---


@pytest.mark.asyncio
async def test_on_voice_server_update_switches_node():
    from voltricx.pool import Pool

    node1 = make_mock_node("N1")
    node2 = make_mock_node("N2")
    Pool._Pool__nodes["N1"] = node1
    Pool._Pool__nodes["N2"] = node2

    # We mock region mapping logic
    with patch("voltricx.pool.Pool.region_from_endpoint", return_value="europe"):
        with patch("voltricx.pool.Pool.get_node", return_value=node2):
            p = Player(client=MagicMock(), channel=MagicMock(), nodes=[node1])
            p._guild = MagicMock()
            p._guild.id = 123
            p._node._players[123] = p

            # Connection event false, node should switch to ideal_node (node2)
            p._connected = False

            # Fake payload
            await p.on_voice_server_update({"token": "tok", "endpoint": "eu.discord.gg"})

            assert p._node is node2
            assert 123 in node2._players


@pytest.mark.asyncio
async def test_on_voice_state_update_no_channel():
    p = make_player()
    with patch.object(p, "_destroy", new_callable=AsyncMock) as mock_destroy:
        await p.on_voice_state_update({"channel_id": None})
        mock_destroy.assert_called_once()


@pytest.mark.asyncio
async def test_on_voice_state_update_with_channel():
    p = make_player()
    mock_channel = MagicMock()
    p.client.get_channel.return_value = mock_channel

    await p.on_voice_state_update({"channel_id": "999", "session_id": "sess123"})
    assert p._connected is True
    assert p._voice_state["channel_id"] == "999"
    assert p._voice_state["voice"]["session_id"] == "sess123"
    assert p.channel is mock_channel


@pytest.mark.asyncio
async def test_dispatch_voice_update_incomplete():
    p = make_player()
    p._voice_state = {"voice": {"token": "t"}}
    # Should safely return
    await p._dispatch_voice_update()
    p._node._update_player.assert_not_called()


@pytest.mark.asyncio
async def test_dispatch_voice_update_complete():
    p = make_player()
    p._voice_state = {
        "channel_id": "999",
        "voice": {"token": "t", "endpoint": "e", "session_id": "s"},
    }
    await p._dispatch_voice_update()
    p._node._update_player.assert_called_once()
    assert p._connected is True
    assert p._connection_event.is_set()


# --- Switch Node ---


@pytest.mark.asyncio
async def test_switch_node_same():
    p = make_player()
    await p.switch_node(p._node)
    # Should return early
    assert p._connected is False


@pytest.mark.asyncio
async def test_switch_node_success():
    p = make_player()
    old_node = p._node
    old_node._players[p._guild.id] = p

    new_node = make_mock_node("N2")
    new_node._update_player = AsyncMock()

    p._dispatch_voice_update = AsyncMock()

    await p.switch_node(new_node)

    assert p._node is new_node
    assert p._guild.id not in old_node._players
    assert p._guild.id in new_node._players
    p._dispatch_voice_update.assert_called_once()
    new_node._update_player.assert_called_once()


# --- Destroy & Disconnected Wait ---


@pytest.mark.asyncio
async def test_destroy():
    p = make_player()
    p._connected = True
    p._node._players[p._guild.id] = p
    p._node._destroy_player = AsyncMock()
    p.cleanup = MagicMock()

    await p._destroy()

    assert p._connected is False
    assert p._guild.id not in p._node._players
    p._node._destroy_player.assert_called_once_with(p._guild.id)


@pytest.mark.asyncio
async def test_disconnected_wait_ignored():
    p = make_player()
    p._connected = True
    # Non-4014 code should just return
    await p._disconnected_wait(1000, True)
    assert p._connected is True


@pytest.mark.asyncio
async def test_disconnected_wait_timeout_reconnects_fails():
    p = make_player()
    p._connected = True
    p._destroy = AsyncMock()

    # Simulate a fast timeout using patch
    with patch("asyncio.timeout"):
        # We don't need to mock wait, just the result
        pass  # The default wait will raise TimeoutError if not set, or we can just mock wait

    p._reconnecting.wait = AsyncMock(side_effect=asyncio.TimeoutError)

    await p._disconnected_wait(4014, True)

    assert p._connected is False
    p._destroy.assert_called_once()


# --- Track End and Autoplay Logic ---


@pytest.mark.asyncio
async def test_handle_track_end_loop_mode():
    p = make_player()
    p.queue.mode = QueueMode.loop

    t = make_mock_track()
    p.queue.loaded = t
    p.play = AsyncMock()

    # Finished reason
    event = TrackEndEvent(
        op="event",
        type="TrackEndEvent",
        track=t,
        reason=TrackEndReason.finished,
        guildId="123",
    )
    await p._handle_track_end(event)

    p.play.assert_called_once_with(t, add_history=False)


@pytest.mark.asyncio
async def test_handle_track_end_autoplay_disabled():
    p = make_player()
    p._autoplay = AutoPlayMode.disabled
    p._start_inactivity_check = MagicMock()

    event = TrackEndEvent(
        op="event",
        type="TrackEndEvent",
        track=make_mock_track(),
        reason=TrackEndReason.finished,
        guildId="123",
    )
    await p._handle_track_end(event)

    p._start_inactivity_check.assert_called_once()


@pytest.mark.asyncio
async def test_handle_track_end_load_failed_increments_error():
    p = make_player()
    p.queue.mode = QueueMode.normal
    p._autoplay = AutoPlayMode.partial

    event = TrackEndEvent(
        op="event",
        type="TrackEndEvent",
        track=make_mock_track(),
        reason=TrackEndReason.load_failed,
        guildId="123",
    )
    await p._handle_track_end(event)

    assert p._error_count == 1


@pytest.mark.asyncio
async def test_handle_track_end_error_limit_reached():
    p = make_player()
    p._error_count = 3
    p._start_inactivity_check = MagicMock()

    event = TrackEndEvent(
        op="event",
        type="TrackEndEvent",
        track=make_mock_track(),
        reason=TrackEndReason.finished,
        guildId="123",
    )
    await p._handle_track_end(event)

    p._start_inactivity_check.assert_called_once()


@pytest.mark.asyncio
async def test_handle_track_end_loop_all():
    p = make_player()
    p.queue.mode = QueueMode.loop_all
    t1 = make_mock_track("enc1")
    t2 = make_mock_track("enc2")
    p.queue.put(t1)
    p.queue.put(t2)

    p.play = AsyncMock()
    event = TrackEndEvent(
        op="event",
        type="TrackEndEvent",
        track=make_mock_track(),
        reason=TrackEndReason.finished,
        guildId="123",
    )

    await p._handle_track_end(event)

    p.play.assert_called_once()
    assert p.play.call_args[0][0].encoded == "enc1"


@pytest.mark.asyncio
async def test_do_recommendation_cache_play():
    p = make_player()
    p._autoplay = AutoPlayMode.enabled
    p.play = AsyncMock()
    t = make_mock_track()

    with patch("voltricx.pool.Pool.get_random_cached_track", return_value=t):
        await p._do_recommendation()

    p.play.assert_called_once_with(t, add_history=False)


@pytest.mark.asyncio
async def test_do_recommendation_from_auto_queue():
    p = make_player()
    p._autoplay = (
        AutoPlayMode.disabled
    )  # Auto queue bypasses enabled check if it has items > cutoff
    p._auto_cutoff = 1
    t1 = make_mock_track("enc1")
    t2 = make_mock_track("enc2")
    p.auto_queue.put(t1)
    p.auto_queue.put(t2)

    p.play = AsyncMock()

    await p._do_recommendation()

    p.play.assert_called_once_with(t1, add_history=False)


# --- DAVE and Play Edge Cases ---


@pytest.mark.asyncio
async def test_dave_protocol_change():
    p = make_player()
    # Dummy to ensure it covers the branches
    await p._on_dave_protocol_change({})
    await p._on_dave_prepare_transition({})


@pytest.mark.asyncio
async def test_play_stop_sets_null_track():
    p = make_player()
    p._node._update_player = AsyncMock()

    res = await p.play(None)

    assert res is None
    p._node._update_player.assert_called_once_with(
        p._guild.id, data={"track": {"encoded": None}}, replace=True
    )


@pytest.mark.asyncio
async def test_play_update_player_raises_rollback():
    p = make_player()
    p._node._update_player = AsyncMock(side_effect=Exception("API Error"))
    p._volume = 50
    t = make_mock_track()
    p._previous = make_mock_track("prev")

    with pytest.raises(Exception, match="API Error"):
        await p.play(t, volume=100)

    # verify rollback
    assert p._volume == 50
    assert p.queue.loaded.encoded == "prev"


@pytest.mark.asyncio
async def test_skip_force_with_empty_queue():
    p = make_player()
    p.play = AsyncMock()

    await p.skip(force=True)

    p.play.assert_called_once_with(None, replace=True)
    assert p._current is None
    assert p.queue.loaded is None


@pytest.mark.asyncio
async def test_inactivity_runner_active():
    p = make_player()
    p._current = make_mock_track()
    p.client.dispatch = MagicMock()

    await p._inactivity_runner(0)

    # Should return early because _current is not None
    p.client.dispatch.assert_not_called()


@pytest.mark.asyncio
async def test_inactivity_runner_inactive():
    p = make_player()
    p._current = None
    p.client.dispatch = MagicMock()

    await p._inactivity_runner(0)

    p.client.dispatch.assert_called_once_with("voltricx_inactive_player", p)


@pytest.mark.asyncio
async def test_handle_inactive_channel_limit_reached():
    p = make_player()
    p._inactive_channel_limit = 1
    p._inactive_channel_count = 1

    # Mock channel with no non-bot members
    mock_channel = MagicMock()
    mock_member = MagicMock()
    mock_member.bot = True
    mock_channel.members = [mock_member]
    p.channel = mock_channel

    p.client.dispatch = MagicMock()

    res = p._handle_inactive_channel()

    assert res is True
    p.client.dispatch.assert_called_once_with("voltricx_inactive_player", p)
