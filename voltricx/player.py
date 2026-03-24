# The MIT License (MIT)
#
# Copyright (c) 2026-Present @JustNixx, @Dipendra-creator and RevvLabs
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from __future__ import annotations

import asyncio
import logging
import secrets
import time
from typing import TYPE_CHECKING, Any, cast

import discord
from discord.abc import Connectable
from discord.utils import MISSING

from .exceptions import (
    ChannelTimeoutException,
    InvalidChannelStateException,
    LavalinkException,
    NodeException,
    QueueEmpty,
)
from .filters import Filters
from .logger import voltricx_logger
from .queue import Queue
from .typings.enums import AutoPlayMode, NodeStatus, QueueMode, TrackEndReason
from .typings.events import TrackEndEvent, TrackStartEvent
from .typings.player import (
    PlayerState as PlayerStateModel,
)
from .typings.player import (
    UpdatePlayerPayload,
    UpdatePlayerTrack,
)
from .typings.track import Playable, Playlist

if TYPE_CHECKING:
    from discord.types.voice import GuildVoiceState as GuildVoiceStatePayload
    from discord.types.voice import VoiceServerUpdate as VoiceServerUpdatePayload

    from .node import Node

    type VocalGuildChannel = discord.VoiceChannel | discord.StageChannel

# Optional davey import for DAVE protocol (Discord E2EE audio)
try:
    import davey  # type: ignore[import-not-found]
except ImportError:
    davey = None

logger = logging.getLogger(__name__)


class Player(discord.VoiceProtocol):
    """
    High-fidelity Voltricx Player (Deep Port).

    This class restores the 1500-line fidelity of the original implementation
    while leveraging modern Pydantic models and async patterns.
    """

    def __init__(
        self,
        client: discord.Client = MISSING,
        channel: Connectable = MISSING,
        *,
        nodes: list[Node] | None = None,
    ) -> None:
        super().__init__(client, channel)
        self.client = client
        self.channel: VocalGuildChannel | Connectable = channel
        self._guild: discord.Guild | None = (
            getattr(channel, "guild", None) if channel is not MISSING else None
        )

        self._node: Node
        from .pool import Pool

        if not nodes:
            self._node = Pool.get_node()
        else:
            connected_nodes = [n for n in nodes if n.status is NodeStatus.connected]
            if not connected_nodes:
                self._node = Pool.get_node()
            else:
                self._node = sorted(connected_nodes, key=lambda n: len(n.players))[0]

        if self.client is MISSING and self._node.client:
            self.client = self._node.client

        self._voice_state: dict[str, Any] = {"voice": {}}
        self._player_state: PlayerStateModel | None = None

        self._last_update: int | None = None
        self._last_position: int = 0
        self._ping: int = -1

        self._connected: bool = False
        self._connection_event: asyncio.Event = asyncio.Event()

        self._current: Playable | None = None
        self._original: Playable | None = None
        self._previous: Playable | None = None

        self.queue: Queue = Queue()
        self.auto_queue: Queue = Queue()

        self._volume: int = 100
        self._paused: bool = False

        self._autoplay: AutoPlayMode = AutoPlayMode.partial
        self._auto_cutoff: int = 20
        self._auto_weight: int = 3
        self._auto_lock: asyncio.Lock = asyncio.Lock()
        self._error_count: int = 0

        self._inactive_channel_limit: int | None = None
        self._inactive_channel_count: int = self._inactive_channel_limit or 0
        self._inactivity_task: asyncio.Task | None = None
        self._inactivity_wait: int | None = 300
        # Monotonic timestamp of when the player last transitioned to idle.
        # None means the player is either playing or has never gone idle yet.
        self._idle_since: float | None = None

        self._filters: Filters = Filters()
        self._reconnecting: asyncio.Event = asyncio.Event()
        self._reconnecting.set()

        self._dave_session: Any = None
        self.home: discord.TextChannel | None = None

    @property
    def node(self) -> Node:
        return self._node

    @property
    def guild(self) -> discord.Guild | None:
        return self._guild

    @property
    def current(self) -> Playable | None:
        return self._current

    @property
    def playing(self) -> bool:
        return self._connected and self.current is not None

    @property
    def paused(self) -> bool:
        return self._paused

    @property
    def volume(self) -> int:
        return self._volume

    @property
    def filters(self) -> Filters:
        return self._filters

    @property
    def ping(self) -> int:
        return self._ping

    @property
    def autoplay(self) -> AutoPlayMode:
        return self._autoplay

    @property
    def position(self) -> int:
        """Accurate position calculation with nanosecond precision."""
        if self.current is None or not self.playing:
            return 0
        if not self._connected or self._last_update is None:
            return 0
        if self._paused:
            return self._last_position

        position_ms = (
            int((time.monotonic_ns() - self._last_update) / 1_000_000) + self._last_position
        )
        return min(position_ms, self.current.length)

    @property
    def inactive_timeout(self) -> int:
        """Seconds of idle time allowed before the player auto-disconnects.

        Returns 0 when auto-disconnect is disabled (``_inactivity_wait`` is
        ``None`` or ``0``).  Set this property to reconfigure the timeout at
        any time — even while the player is already idle.
        """
        return self._inactivity_wait or 0

    @inactive_timeout.setter
    def inactive_timeout(self, value: int | None) -> None:
        """Update the inactivity timeout (seconds).  Pass ``None`` or ``0`` to
        disable auto-disconnect while still allowing idle-time tracking.

        If the player is already idle when this is called, the running
        countdown is restarted with the new value so the change takes effect
        immediately.
        """
        self._inactivity_wait = value
        # If the player is currently idle, restart the countdown so the
        # new timeout value applies right away.
        if self._idle_since is not None:
            # Cancel any existing task without clearing _idle_since
            if self._inactivity_task:
                self._inactivity_task.cancel()
                self._inactivity_task = None
            if value:
                self._inactivity_task = asyncio.create_task(self._inactivity_runner(value))

    @property
    def is_idle(self) -> bool:
        """``True`` when the player is connected but not playing anything.

        This reflects actual playback state regardless of whether
        ``inactive_timeout`` is configured.
        """
        return self._connected and self._current is None

    @property
    def idle_time(self) -> float:
        """Seconds the player has been continuously idle.

        Returns ``0.0`` while a track is playing or if the player has
        never gone idle in this session.  The clock starts the moment the
        last track finishes (or autoplay/queue runs dry) and resets to
        ``0.0`` the moment a new track begins.

        Example usage in a bot::

            if player.idle_time > 60:
                await ctx.send("Bot has been idle for over a minute!")
        """
        if self._idle_since is None:
            return 0.0
        return time.monotonic() - self._idle_since

    def _update_state(self, state: PlayerStateModel) -> None:
        self._player_state = state
        self._last_update = time.monotonic_ns()
        self._last_position = state.position
        self._ping = state.ping

    # --- Discord VoiceProtocol Implementation ---

    async def on_voice_server_update(self, data: VoiceServerUpdatePayload) -> None:
        self._voice_state["voice"]["token"] = data["token"]
        self._voice_state["voice"]["endpoint"] = data["endpoint"]

        endpoint = data.get("endpoint")
        if endpoint and not self._connected:
            from .pool import Pool

            region = Pool.region_from_endpoint(endpoint)
            ideal_node = Pool.get_node(region=region)
            if ideal_node != self._node and self._guild:
                self._node._players.pop(self._guild.id, None)
                self._node = ideal_node
                self._node._players[self._guild.id] = self

        await self._dispatch_voice_update()

    async def on_voice_state_update(self, data: GuildVoiceStatePayload) -> None:
        channel_id = data["channel_id"]
        if not channel_id:
            await self._destroy()
            return

        self._connected = True
        self._voice_state["channel_id"] = str(channel_id)
        self._voice_state["voice"]["session_id"] = data["session_id"]
        self.channel = cast("VocalGuildChannel", self.client.get_channel(int(channel_id)))

    async def _dispatch_voice_update(self) -> None:
        if not self._guild:
            return

        voice = self._voice_state["voice"]
        if not all(k in voice for k in ("session_id", "token", "endpoint")):
            return

        payload = {
            "voice": {
                "token": voice["token"],
                "endpoint": voice["endpoint"],
                "sessionId": voice["session_id"],
            }
        }
        if self._voice_state.get("channel_id"):
            payload["voice"]["channelId"] = self._voice_state["channel_id"]

        try:
            await self._node._update_player(self._guild.id, data=payload)
            self._connected = True
            self._connection_event.set()
            if voltricx_logger.enabled:
                voltricx_logger.player(
                    f"Dispatched voice state for guild {self._guild.id} "
                    f"to node {self._node.identifier}"
                )
        except (NodeException, LavalinkException) as e:
            # Set the event even on error to break the wait; _connected stays False.
            self._connection_event.set()
            await self.disconnect()
            if voltricx_logger.enabled:
                voltricx_logger.error(
                    f"Failed to dispatch voice update for guild {self._guild.id}: {e}"
                )

    async def connect(
        self,
        *,
        timeout: float = 10.0,
        reconnect: bool,  # Required by discord.VoiceProtocol interface; not used internally.
        self_deaf: bool = False,
        self_mute: bool = False,
    ) -> None:
        del reconnect  # Intentionally unused — part of the VoiceProtocol signature.
        if self.channel is MISSING:
            raise InvalidChannelStateException("Player tried to connect without a valid channel.")

        if not self._guild:
            self._guild = getattr(self.channel, "guild", None)

        if self._guild:
            self._node._players[self._guild.id] = self
            await self._guild.change_voice_state(
                channel=self.channel,  # pyright: ignore[reportArgumentType]
                self_mute=self_mute,
                self_deaf=self_deaf,
            )

        try:
            async with asyncio.timeout(timeout):
                await self._connection_event.wait()

            if not self._connected:
                raise ChannelTimeoutException(
                    f"Connection to {self.channel} failed during voice dispatch."
                )
            # NOTE: do NOT call _start_inactivity_check() here.
            # The idle countdown must only begin once a song finishes and
            # the queue/autoplay is exhausted (_handle_track_end already does
            # this).  Starting it at connect-time caused the bot to disconnect
            # users who joined the channel before issuing any play command.
        except TimeoutError as exc:
            raise ChannelTimeoutException(
                f"Connection to {self.channel} timed out after {timeout}s."
            ) from exc

    async def move_to(self, channel: VocalGuildChannel | None, *, timeout: float = 10.0) -> None:
        if not self._guild:
            raise InvalidChannelStateException("Player tried to move without a valid guild.")

        self._connection_event.clear()
        self._reconnecting.clear()

        await self._guild.change_voice_state(channel=channel)
        if channel is None:
            self._reconnecting.set()
            return

        try:
            async with asyncio.timeout(timeout):
                await self._connection_event.wait()
        except TimeoutError as exc:
            raise ChannelTimeoutException(f"Move to {channel} timed out after {timeout}s.") from exc
        finally:
            self._reconnecting.set()

    async def disconnect(self, **_kwargs: Any) -> None:
        if self._guild is not None:
            await self._destroy()
            if self._guild.id in self._node._players:
                del self._node._players[self._guild.id]
            await self._guild.change_voice_state(channel=None)

    async def migrate_to(self, node: Node) -> None:
        """Migrate this player to another node (failover)."""
        if self._guild is None or self._node == node:
            return

        old_node = self._node
        if self._guild.id in old_node._players:
            del old_node._players[self._guild.id]

        self._node = node
        self._node._players[self._guild.id] = self

        if self._voice_state:
            await self._dispatch_voice_update()

        if self.current:
            # Re-play the current track on the new node to resume state
            await self.play(self.current, replace=True, start=self.position, add_history=False)

    # --- Playback Controls ---

    async def play(
        self,
        track: Playable | None,
        *,
        replace: bool = True,
        start: int = 0,
        end: int | None = None,
        volume: int | None = None,
        paused: bool | None = None,
        add_history: bool = True,
        filters: Filters | None = None,
        populate: bool = False,
        max_populate: int = 5,
    ) -> Playable | None:
        if not self._guild:
            raise NodeException("Player is not connected to a guild.")

        vol = volume if volume is not None else self._volume
        original_vol = self._volume
        self._volume = vol

        if replace or not self._current:
            self._current = track
            self._original = track

        old_previous = self._previous
        self._previous = self._current

        pause = paused if paused is not None else self._paused
        self._paused = pause

        if filters:
            self._filters = filters

        if track is None:
            # Stop playback: Lavalink v4 requires track: {encoded: null} to stop
            payload = {"track": {"encoded": None}}
            await self._node._update_player(self._guild.id, data=payload, replace=True)
            return None

        self.queue.loaded = track
        payload = UpdatePlayerPayload(
            track=UpdatePlayerTrack(encoded=track.encoded, userData=track.extras)
            if track.extras
            else UpdatePlayerTrack(encoded=track.encoded),
            position=start,
            endTime=end,
            volume=vol,
            paused=pause,
            filters=self._filters.to_dict() or None,
        )

        try:
            await self._node._update_player(
                self._guild.id,
                data=payload.model_dump(by_alias=True, exclude_none=True),
                replace=replace,
            )
        except Exception:
            self.queue.loaded = old_previous
            self._current = old_previous
            self._original = None  # Or old_original if we track it
            self._previous = old_previous
            self._volume = original_vol
            raise

        if add_history and self.queue.history:
            self.queue.history.put(track)

        if populate:
            await self._do_recommendation(populate_track=track, max_population=max_populate)

        if voltricx_logger.enabled:
            voltricx_logger.player(f"Playing: {track.title} in guild {self._guild.id}")

        return track

    async def stop(self) -> None:
        await self.skip(force=True)

    async def skip(self, *, force: bool = True) -> Playable | None:
        if not self._guild:
            return None

        old = self.current
        next_track = None

        if self.queue:
            try:
                next_track = self.queue.get()
            except QueueEmpty:
                pass

        if next_track:
            await self.play(next_track, replace=True)
        else:
            if force:
                self.queue.loaded = None
                self._current = None
            await self.play(None, replace=True)

        return old

    async def pause(self, value: bool) -> None:
        if self._guild:
            await self._node._update_player(self._guild.id, data={"paused": value})
            self._paused = value

    async def seek(self, position: int = 0) -> None:
        if self._guild:
            await self._node._update_player(self._guild.id, data={"position": position})

    async def set_volume(self, value: int = 100) -> None:
        vol = max(min(value, 1000), 0)
        if self._guild:
            await self._node._update_player(self._guild.id, data={"volume": vol})
            self._volume = vol

    async def set_filters(self, filters: Filters | None = None, *, seek: bool = False) -> None:
        if not filters:
            filters = Filters()
        self._filters = filters
        if self._guild:
            payload: dict[str, Any] = {"filters": filters.to_dict()}
            if seek:
                payload["position"] = self.position
            await self._node._update_player(self._guild.id, data=payload)

    # --- Internal Event Handlers ---

    async def _handle_track_start(self, event: TrackStartEvent) -> None:
        self._current = event.track
        self.queue.loaded = event.track
        self._inactive_channel_count = self._inactive_channel_limit or 0
        self._stop_inactivity_check()

    def _update_error_count(self, reason: TrackEndReason) -> bool:
        """Update error counter based on end reason. Returns True if should abort."""
        if reason == TrackEndReason.replaced:
            self._error_count = 0
            return True
        if reason == TrackEndReason.load_failed:
            self._error_count += 1
        else:
            self._error_count = 0
        return False

    async def _advance_queue(self, finished_track: Playable | None) -> None:
        """Advance playback: loop, queue, or autoplay."""
        if self.queue.mode is QueueMode.loop and finished_track:
            await self.play(finished_track, add_history=False)
            return

        if (
            self.queue.mode is QueueMode.loop_all
            or self._autoplay is AutoPlayMode.partial
            or self.queue
        ):
            next_track: Playable | None = None
            try:
                next_track = self.queue.get()
            except QueueEmpty:
                pass
            if next_track:
                await self.play(next_track)
            else:
                self._start_inactivity_check()
            return

        if self._autoplay is AutoPlayMode.enabled:
            async with self._auto_lock:
                try:
                    await self._do_recommendation()
                except Exception:  # pylint: disable=broad-exception-caught
                    self._start_inactivity_check()

    async def _handle_track_end(self, event: TrackEndEvent) -> None:
        if self._handle_inactive_channel():
            return

        # Save the track that just finished BEFORE clearing state,
        # so loop mode can replay it.
        finished_track: Playable | None = self.queue.loaded or self._current

        if event.reason != TrackEndReason.replaced:
            self._current = None
            self.queue.loaded = None

        if self._autoplay is AutoPlayMode.disabled:
            self._start_inactivity_check()
            return

        if self._error_count >= 3:
            self._start_inactivity_check()
            return

        if self._update_error_count(event.reason):
            return

        await self._advance_queue(finished_track)

    # --- Recommendations & AutoPlay ---

    def _get_recommendation_seeds(self, populate_track: Playable | None) -> list[Playable]:
        weighted_history = list(self.queue.history) if self.queue.history else []
        weighted_history = weighted_history[: max(5, 5 * self._auto_weight)]
        weighted_upcoming = list(self.auto_queue)[: max(3, int(5 * self._auto_weight / 3))]
        choices = weighted_history + weighted_upcoming + [self.current]

        seeds = [t for t in choices if t is not None]
        secrets.SystemRandom().shuffle(seeds)
        if populate_track:
            seeds.insert(0, populate_track)
        return seeds

    def _build_recommendation_query(self, seeds: list[Playable]) -> str:
        """Build a Lavalink search query from the first recommendation seed."""
        seed = seeds[0]
        if seed.identifier.isdigit():
            # Numeric ID (e.g. Deezer) — YouTube RD links won't work; fall back to text.
            return f"{seed.title} {seed.author}"
        return f"https://www.youtube.com/watch?v={seed.identifier}&list=RD{seed.identifier}"

    async def _fill_auto_queue(
        self, query: str, limit: int, populate_track: Playable | None
    ) -> None:
        """Fetch tracks from Pool and populate the auto-queue up to *limit* items."""
        from .pool import Pool

        try:
            results = await Pool.fetch_tracks(query, node=self._node)
            tracks = results.tracks if isinstance(results, Playlist) else results
            added = 0
            for track in tracks:
                in_history = self.queue.history and track in self.queue.history._items
                if in_history or track in self.queue._items:
                    continue
                track.recommended = True
                self.auto_queue.put(track)
                added += 1
                if added >= limit:
                    break

            if not self.current and not populate_track and self.auto_queue:
                next_t = self.auto_queue.get()
                await self.play(next_t, add_history=False)
        except Exception as e:  # pylint: disable=broad-exception-caught
            if voltricx_logger.enabled:
                voltricx_logger.error(f"Recommendation failed: {e}")

    async def _do_recommendation(
        self,
        populate_track: Playable | None = None,
        max_population: int | None = None,
    ) -> None:
        if not self._guild:
            return

        # Tier 1: Cache-based Autoplay (User Requested)
        if self._autoplay is AutoPlayMode.enabled and not populate_track:
            from .pool import Pool

            track = Pool.get_random_cached_track()
            if track:
                if voltricx_logger.enabled:
                    voltricx_logger.player(
                        f"Autoplay (Cache): Picking random track '{track.title}'"
                    )
                await self.play(track, add_history=False)
                return

        limit = max_population or self._auto_cutoff
        if len(self.auto_queue) > self._auto_cutoff and not populate_track:
            track = self.auto_queue.get()
            await self.play(track, add_history=False)
            return

        seeds = self._get_recommendation_seeds(populate_track)
        if not seeds:
            return

        query = self._build_recommendation_query(seeds)
        await self._fill_auto_queue(query, limit, populate_track)

    # --- Inactivity Logic ---

    def _handle_inactive_channel(self) -> bool:
        if not self.channel:
            return False
        members = getattr(self.channel, "members", [])
        members = [m for m in members if not getattr(m, "bot", False)]
        if not members:
            self._inactive_channel_count -= 1
        else:
            self._inactive_channel_count = self._inactive_channel_limit or 0

        if self._inactive_channel_limit and self._inactive_channel_count <= 0:
            self.client.dispatch("voltricx_inactive_player", self)
            return True
        return False

    def _start_inactivity_check(self) -> None:
        # Record the exact moment the player went idle — always, even when
        # auto-disconnect is disabled — so idle_time / is_idle stay accurate.
        if self._idle_since is None:
            self._idle_since = time.monotonic()

        # Only launch the countdown task when a timeout is configured and
        # no task is already running.
        if not self._inactivity_task and self._inactivity_wait:
            self._inactivity_task = asyncio.create_task(
                self._inactivity_runner(self._inactivity_wait)
            )

    def _stop_inactivity_check(self) -> None:
        # Cancel any pending auto-disconnect countdown.
        if self._inactivity_task:
            self._inactivity_task.cancel()
            self._inactivity_task = None
        # Reset the idle clock — the player is active again.
        self._idle_since = None

    async def _inactivity_runner(self, wait: int) -> None:
        try:
            await asyncio.sleep(wait)
            # Guard: a track may have started while we slept (race condition).
            if self._current is not None:
                return
            self.client.dispatch("voltricx_inactive_player", self)
        except asyncio.CancelledError:
            raise  # Must be re-raised so asyncio can properly cancel the task.

    # --- Internal Cleanup ---

    async def _disconnected_wait(self, code: int, by_remote: bool) -> None:
        """
        Internal task to wait for reconnection if the Voice WebSocket was closed.

        Specifically handles code 4014 (Remote Disconnect) which often happens
        during region changes or kicks.
        """
        if code != 4014 or not by_remote:
            return

        self._connected = False
        self._connection_event.clear()

        # Wait up to 10 seconds for Discord to reconnect us or for the user to move the bot
        try:
            async with asyncio.timeout(10.0):
                await self._reconnecting.wait()
        except TimeoutError:
            if voltricx_logger.enabled:
                voltricx_logger.player(
                    f"Reconnection timed out for guild "
                    f"{self._guild.id if self._guild else 'unknown'} (code {code})"
                )

        if self._connected:
            return

        await self._destroy()

    async def _destroy(self) -> None:
        """Internal cleanup for the player and its node association."""
        if not self._guild:
            return

        self._connected = False
        self._connection_event.clear()
        self._stop_inactivity_check()

        if self._guild.id in self._node._players:
            del self._node._players[self._guild.id]

        self._current = None
        self.queue.loaded = None

        try:
            await self._node._destroy_player(self._guild.id)
        except LavalinkException as exc:
            if voltricx_logger.enabled:
                voltricx_logger.error(f"Failed to destroy player for guild {self._guild.id}: {exc}")

        # Clear guild._voice_client so discord.py knows we're disconnected
        self.cleanup()

    async def switch_node(self, node: Node) -> None:
        if self._node == node or not self._guild:
            return

        self._node._players.pop(self._guild.id, None)

        self._node = node
        node._players[self._guild.id] = self
        self._connected = False
        self._connection_event.clear()

        await self._dispatch_voice_update()

        payload = UpdatePlayerPayload(
            filters=self._filters.to_dict(),
            position=self.position,
            volume=self._volume,
            paused=self._paused,
        )
        await node._update_player(
            self._guild.id,
            data=payload.model_dump(by_alias=True, exclude_none=True),
            replace=True,
        )

    # --- DAVE Protocol ---

    async def _on_dave_protocol_change(self, _payload: Any) -> None:
        if not davey:
            return
        # High-fidelity DAVE handshake would go here if library was fully integrated.

    async def _on_dave_prepare_transition(self, _payload: Any) -> None:
        # High-fidelity DAVE transition logic — to be implemented when davey is integrated.
        ...
