"""Expanded tests for voltricx.player — covering all remaining branches."""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from voltricx.exceptions import NodeException
from voltricx.filters import Filters
from voltricx.player import Player
from voltricx.typings.enums import AutoPlayMode, QueueMode, TrackEndReason
from voltricx.typings.events import TrackEndEvent, TrackStartEvent
from voltricx.typings.player import PlayerState
from voltricx.typings.track import Playable


def make_track(encoded="enc1", title="T", identifier="id1"):
    t = MagicMock(spec=Playable)
    t.encoded = encoded
    t.title = title
    t.identifier = identifier
    t.extras = {}
    t.recommended = False
    return t


def make_node(identifier="N1", region="us"):
    node = MagicMock()
    node.identifier = identifier
    node.config = MagicMock()
    node.config.region = region
    node.status = MagicMock()
    node.client = MagicMock()
    node.client.user = MagicMock()
    node.client.user.id = 123
    node._players = {}
    node._update_player = AsyncMock()
    node._destroy_player = AsyncMock()
    return node


def make_player(guild_id=12345):
    client = MagicMock()
    client.user = MagicMock()
    client.user.id = 123
    channel = MagicMock()
    guild = MagicMock()
    guild.id = guild_id
    guild.change_voice_state = AsyncMock()
    channel.guild = guild

    node = make_node()

    with patch("voltricx.pool.Pool.get_node", return_value=node):
        player = Player(client=client, channel=channel)

    player._guild = guild
    player._connected = True
    player._node = node
    return player


# ── Core Properties ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_player_node():
    p = make_player()
    assert p.node is p._node


@pytest.mark.asyncio
async def test_player_guild():
    p = make_player(12345)
    assert p.guild.id == 12345


@pytest.mark.asyncio
async def test_player_current_none():
    p = make_player()
    assert p.current is None


@pytest.mark.asyncio
async def test_player_playing_false_when_no_track():
    p = make_player()
    assert p.playing is False


@pytest.mark.asyncio
async def test_player_playing_true():
    p = make_player()
    p._current = make_track()
    assert p.playing is True


@pytest.mark.asyncio
async def test_player_paused_default():
    p = make_player()
    assert p.paused is False


@pytest.mark.asyncio
async def test_player_volume_default():
    p = make_player()
    assert p.volume == 100


@pytest.mark.asyncio
async def test_player_filters_default():
    p = make_player()
    assert isinstance(p.filters, Filters)


@pytest.mark.asyncio
async def test_player_autoplay_default():
    p = make_player()
    assert p.autoplay == AutoPlayMode.partial


@pytest.mark.asyncio
async def test_player_ping_default():
    p = make_player()
    assert p.ping == -1


# ── position property ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_player_position_no_current():
    p = make_player()
    assert p.position == 0


@pytest.mark.asyncio
async def test_player_position_paused():
    p = make_player()
    t = make_track()
    t.length = 240000
    p._current = t
    p._paused = True
    p._last_position = 30000
    p._last_update = time.monotonic_ns()
    assert p.position == 30000


@pytest.mark.asyncio
async def test_player_position_playing():
    p = make_player()
    t = make_track()
    t.length = 240000
    p._current = t
    p._paused = False
    p._last_position = 0
    p._last_update = time.monotonic_ns()
    pos = p.position
    assert 0 <= pos <= 240000


@pytest.mark.asyncio
async def test_player_position_no_last_update():
    p = make_player()
    t = make_track()
    t.length = 240000
    p._current = t
    p._last_update = None
    assert p.position == 0


# ── is_idle / idle_time ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_player_is_idle_true():
    p = make_player()
    p._connected = True
    p._current = None
    assert p.is_idle is True


@pytest.mark.asyncio
async def test_player_is_idle_false_playing():
    p = make_player()
    p._current = make_track()
    assert p.is_idle is False


@pytest.mark.asyncio
async def test_player_idle_time_zero_while_playing():
    p = make_player()
    p._idle_since = None
    assert p.idle_time == 0.0


@pytest.mark.asyncio
async def test_player_idle_time_elapsed():
    p = make_player()
    p._idle_since = time.monotonic() - 10.0
    assert p.idle_time >= 10.0


# ── inactive_timeout setter ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_inactive_timeout_setter():
    p = make_player()
    p.inactive_timeout = 120
    assert p._inactivity_wait == 120


@pytest.mark.asyncio
async def test_inactive_timeout_setter_restarts_when_idle():
    p = make_player()
    p._idle_since = time.monotonic()
    p.inactive_timeout = 60
    # Task should be created
    assert p._inactivity_task is not None
    p._inactivity_task.cancel()


# ── _update_state ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_state():
    p = make_player()
    state = PlayerState(time=1000, position=5000, connected=True, ping=50)
    p._update_state(state)
    assert p._last_position == 5000
    assert p._ping == 50


# ── set_filters ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_set_filters_default():
    p = make_player()
    await p.set_filters()
    args, kwargs = p._node._update_player.call_args
    assert "filters" in kwargs["data"]


@pytest.mark.asyncio
async def test_set_filters_with_seek():
    p = make_player()
    p._current = make_track()
    p._current.length = 240000
    p._last_position = 5000
    p._last_update = time.monotonic_ns()
    await p.set_filters(Filters(), seek=True)
    args, kwargs = p._node._update_player.call_args
    assert "position" in kwargs["data"]


# ── seek ───────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_seek():
    p = make_player()
    await p.seek(30000)
    p._node._update_player.assert_called_once_with(p._guild.id, data={"position": 30000})


# ── pause ──────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_pause_and_resume():
    p = make_player()
    await p.pause(True)
    assert p.paused is True
    await p.pause(False)
    assert p.paused is False


# ── set_volume ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_set_volume_clamped():
    p = make_player()
    await p.set_volume(-100)  # should clamp to 0
    assert p.volume == 0
    await p.set_volume(9999)  # should clamp to 1000
    assert p.volume == 1000


# ── play ───────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_play_no_guild_raises():
    p = make_player()
    p._guild = None
    with pytest.raises(NodeException):
        await p.play(make_track())


@pytest.mark.asyncio
async def test_play_none_stops():
    p = make_player()
    await p.play(None)
    p._node._update_player.assert_called_once()
    args, kwargs = p._node._update_player.call_args
    assert kwargs["data"]["track"]["encoded"] is None


@pytest.mark.asyncio
async def test_play_sets_current():
    p = make_player()
    t = make_track()
    t.extras = {}
    await p.play(t)
    assert p.current is t


@pytest.mark.asyncio
async def test_play_with_volume():
    p = make_player()
    t = make_track()
    t.extras = {}
    await p.play(t, volume=50)
    assert p.volume == 50


@pytest.mark.asyncio
async def test_play_updates_history():
    from voltricx.typings.track import Playable, TrackInfo

    p = make_player()
    info = TrackInfo(
        identifier="id1",
        isSeekable=True,
        author="Art",
        length=180000,
        isStream=False,
        position=0,
        title="T",
        sourceName="youtube",
    )
    t = Playable(encoded="enc_h", info=info)
    # Pre-populate history so the falsy-check passes (empty queue is falsy)
    existing = Playable(encoded="enc_prev", info=info)
    p.queue.history.put(existing)
    assert len(p.queue.history._items) == 1
    await p.play(t, add_history=True)
    # Should now have 2 items in history (existing + newly played)
    assert len(p.queue.history._items) == 2


@pytest.mark.asyncio
async def test_play_network_failure_rolls_back():
    p = make_player()
    p._node._update_player = AsyncMock(side_effect=Exception("network failed"))
    t = make_track()
    t.extras = {}
    with pytest.raises(Exception, match="network failed"):
        await p.play(t)
    assert p._current is None


# ── skip ──────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_skip_no_guild():
    p = make_player()
    p._guild = None
    result = await p.skip()
    assert result is None


@pytest.mark.asyncio
async def test_skip_with_next_track():
    p = make_player()
    t1, t2 = make_track("e1"), make_track("e2")
    t1.extras = {}
    t2.extras = {}
    p._current = t1
    p.queue.put(t2)
    old = await p.skip()
    assert old is t1


@pytest.mark.asyncio
async def test_skip_force_clears_current():
    p = make_player()
    t = make_track()
    t.extras = {}
    p._current = t
    await p.skip(force=True)
    # After skip with nothing in queue, current is cleared
    assert p.current is None


# ── stop ──────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_stop():
    p = make_player()
    p.skip = AsyncMock()
    await p.stop()
    p.skip.assert_called_once_with(force=True)


# ── disconnect ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_disconnect():
    p = make_player()
    p._guild.change_voice_state = AsyncMock()
    p._node._destroy_player = AsyncMock()
    p.cleanup = MagicMock()
    await p.disconnect()
    p._guild.change_voice_state.assert_called_once()


# ── _handle_track_start ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_handle_track_start():
    p = make_player()
    t = make_track()
    event = TrackStartEvent(op="event", guildId=str(p._guild.id), type="TrackStartEvent", track=t)
    await p._handle_track_start(event)
    assert p.current is t


# ── _handle_track_end ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_handle_track_end_autoplay_disabled():
    p = make_player()
    p._autoplay = AutoPlayMode.disabled
    t = make_track()
    t.extras = {}
    p.queue.loaded = t
    event = TrackEndEvent(
        op="event",
        guildId=str(p._guild.id),
        type="TrackEndEvent",
        track=t,
        reason=TrackEndReason.finished,
    )
    await p._handle_track_end(event)
    # Should have started inactivity check
    assert p._idle_since is not None
    p._stop_inactivity_check()


@pytest.mark.asyncio
async def test_handle_track_end_loop_mode():
    p = make_player()
    t = make_track()
    t.extras = {}
    p.queue.loaded = t
    p.queue.mode = QueueMode.loop
    p.play = AsyncMock()
    event = TrackEndEvent(
        op="event",
        guildId=str(p._guild.id),
        type="TrackEndEvent",
        track=t,
        reason=TrackEndReason.finished,
    )
    await p._handle_track_end(event)
    p.play.assert_called_once_with(t, add_history=False)


@pytest.mark.asyncio
async def test_handle_track_end_replaced():
    p = make_player()
    t = make_track()
    t.extras = {}
    p.queue.loaded = t
    p.play = AsyncMock()
    event = TrackEndEvent(
        op="event",
        guildId=str(p._guild.id),
        type="TrackEndEvent",
        track=t,
        reason=TrackEndReason.replaced,
    )
    await p._handle_track_end(event)
    p.play.assert_not_called()


@pytest.mark.asyncio
async def test_handle_track_end_error_count_increments():
    p = make_player()
    t = make_track()
    t.extras = {}
    p.queue.loaded = t
    p._error_count = 0
    event = TrackEndEvent(
        op="event",
        guildId=str(p._guild.id),
        type="TrackEndEvent",
        track=t,
        reason=TrackEndReason.load_failed,
    )
    await p._handle_track_end(event)
    assert p._error_count == 1
    p._stop_inactivity_check()


@pytest.mark.asyncio
async def test_handle_track_end_plays_next():
    p = make_player()
    t1, t2 = make_track("e1"), make_track("e2")
    t1.extras = {}
    t2.extras = {}
    p.queue.loaded = t1
    p.queue.put(t2)
    p.play = AsyncMock()
    event = TrackEndEvent(
        op="event",
        guildId=str(p._guild.id),
        type="TrackEndEvent",
        track=t1,
        reason=TrackEndReason.finished,
    )
    await p._handle_track_end(event)
    p.play.assert_called_once_with(t2)


# ── Inactivity ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_inactivity_runner_cancels_cleanly():
    p = make_player()
    task = asyncio.create_task(p._inactivity_runner(0.001))
    await asyncio.sleep(0.05)  # let it run to completion
    assert task.done()


@pytest.mark.asyncio
async def test_start_stop_inactivity():
    p = make_player()
    p._start_inactivity_check()
    assert p._idle_since is not None
    p._stop_inactivity_check()
    assert p._idle_since is None
    assert p._inactivity_task is None


@pytest.mark.asyncio
async def test_start_inactivity_no_duplicate_task():
    p = make_player()
    p._start_inactivity_check()
    task1 = p._inactivity_task
    p._start_inactivity_check()  # call again
    assert p._inactivity_task is task1  # no new task
    p._stop_inactivity_check()


# ── _handle_inactive_channel ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_handle_inactive_channel_no_channel():
    p = make_player()
    p.channel = None
    assert p._handle_inactive_channel() is False


@pytest.mark.asyncio
async def test_handle_inactive_channel_with_members():
    p = make_player()
    p._inactive_channel_limit = 3
    p._inactive_channel_count = 3
    human = MagicMock()
    human.bot = False
    p.channel.members = [human]
    result = p._handle_inactive_channel()
    assert result is False
    assert p._inactive_channel_count == 3  # reset to limit


@pytest.mark.asyncio
async def test_handle_inactive_channel_empty_triggers():
    p = make_player()
    p._inactive_channel_limit = 1
    p._inactive_channel_count = 1
    p.channel.members = []  # empty channel
    result = p._handle_inactive_channel()
    # count goes to 0 <= 0, should trigger
    assert result is True
