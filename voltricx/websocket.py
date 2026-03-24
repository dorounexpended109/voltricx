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
from typing import TYPE_CHECKING, Any, cast

import aiohttp
from pydantic import TypeAdapter, ValidationError

from .backoff import Backoff
from .typings.enums import NodeStatus, OpCode
from .typings.events import (
    EventPayload,
    TrackEndEvent,
    TrackExceptionEvent,
    TrackStartEvent,
    TrackStuckEvent,
    WebSocketClosedEvent,
)
from .typings.websocket import (
    DAVEPrepareTransitionEvent,
    DAVEProtocolChangeEvent,
    PlayerUpdateOp,
    ReadyOp,
    StatsOp,
    WebSocketPayload,
)

if TYPE_CHECKING:
    from .node import Node

logger: logging.Logger = logging.getLogger(__name__)

# Pre-compute TypeAdapter for performance
PAYLOAD_ADAPTER = TypeAdapter(WebSocketPayload)


class Websocket:
    """
    Handles the WebSocket connection to a Lavalink node.

    Includes robust Pydantic-validated parsing, exponential backoff,
    and high-fidelity failover.
    """

    def __init__(self, node: Node) -> None:
        self.node = node
        self.socket: aiohttp.ClientWebSocketResponse | None = None
        self.backoff = Backoff(base=1, maximum=60)

        self._keep_alive_task: asyncio.Task | None = None
        self._tasks: set[asyncio.Task] = set()
        self._closed = False

    async def connect(self, *, silent: bool = False) -> None:
        """Establish the WebSocket connection with retry logic."""
        if self._closed:
            return

        uri = f"{self.node.uri.replace('http', 'ws', 1).removesuffix('/')}/v4/websocket"
        headers = self.node.headers

        # Lavalink Resume Support
        if self.node.session_id:
            headers["Session-Id"] = self.node.session_id

        while True:
            try:
                self.socket = await self.node._session.ws_connect(uri, headers=headers)
                if not silent:
                    logger.info(f"Connected to Lavalink WebSocket: {self.node.identifier}")
                self.backoff.reset()

                self._keep_alive_task = asyncio.create_task(self._keep_alive())
                break
            except Exception as e:
                delay = self.backoff.calculate()
                if not silent:
                    logger.error(
                        f"WebSocket connection failed for {self.node.identifier}: {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                await asyncio.sleep(delay)

    async def _keep_alive(self) -> None:
        """Main loop to receive and process WebSocket messages."""
        while self.socket and not self.socket.closed:
            try:
                msg = await self.socket.receive()

                if msg.type == aiohttp.WSMsgType.TEXT:
                    await self._handle_message(msg.json())
                elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                    break
            except Exception as e:
                logger.error(f"Error in WebSocket loop for {self.node.identifier}: {e}")
                break

        if not self._closed:
            await self._handle_disconnect()

    async def _handle_message(self, data: dict[str, Any]) -> None:
        """Validate and dispatch incoming messages using Pydantic."""
        try:
            payload = PAYLOAD_ADAPTER.validate_python(data)
        except ValidationError as e:
            logger.error(f"Failed to validate Lavalink payload: {e}")
            return

        op = getattr(payload, "op", None)

        if op == OpCode.ready:
            # Need to cast because TypeAdapter might not narrow properly with Annotated
            p = cast(ReadyOp, payload)
            self.node.session_id = p.session_id
            self.node.status = NodeStatus.connected
            logger.info(f"Node {self.node.identifier} is READY. Session ID: {self.node.session_id}")
            self.node.client.dispatch("voltricx_node_ready", self.node)

        elif op == OpCode.stats:
            p = cast(StatsOp, payload)
            self.node.stats_memory = p.memory
            self.node.stats_cpu = p.cpu
            self.node.stats_frames = p.frame_stats
            self.node.playing_count = p.playing_players
            self.node.client.dispatch("voltricx_node_stats", self.node)

        elif op == OpCode.player_update:
            p = cast(PlayerUpdateOp, payload)
            player = self.node.get_player(int(p.guild_id))
            if player:
                player._update_state(p.state)

        elif op == OpCode.event:
            await self._handle_event(cast(Any, payload))

        elif op == "dave":
            await self._handle_dave(cast(Any, payload))

    async def _handle_event(self, event: EventPayload) -> None:
        """Dispatch Lavalink events to the appropriate player and client."""
        player = self.node.get_player(int(event.guild_id))

        if isinstance(event, TrackStartEvent):
            if player:
                player.client.dispatch("voltricx_track_start", player, event.track)

        elif isinstance(event, TrackEndEvent):
            if player:
                await player._handle_track_end(event)
                player.client.dispatch("voltricx_track_end", player, event.track, event.reason)

        elif isinstance(event, TrackExceptionEvent):
            if player:
                player.client.dispatch(
                    "voltricx_track_exception", player, event.track, event.exception
                )

        elif isinstance(event, TrackStuckEvent):
            if player:
                player.client.dispatch(
                    "voltricx_track_stuck", player, event.track, event.threshold_ms
                )

        elif isinstance(event, WebSocketClosedEvent) and player:
            player.client.dispatch(
                "voltricx_websocket_closed",
                player,
                event.code,
                event.reason,
                event.by_remote,
            )
            task = asyncio.create_task(player._disconnected_wait(event.code, event.by_remote))
            self._tasks.add(task)
            task.add_done_callback(self._tasks.discard)

    async def _handle_dave(self, payload: Any) -> None:
        """Process DAVE protocol events."""
        player = self.node.get_player(int(payload.guild_id))
        if not player:
            return

        if isinstance(payload, DAVEProtocolChangeEvent):
            await player._on_dave_protocol_change(payload)
        elif isinstance(payload, DAVEPrepareTransitionEvent):
            await player._on_dave_prepare_transition(payload)

    async def _handle_disconnect(self) -> None:
        """Trigger failover and attempt reconnection on disconnect."""
        logger.warning(
            f"WebSocket disconnected from {self.node.identifier}. Triggering failover..."
        )
        self.node.status = NodeStatus.disconnected

        # Trigger High-Fidelity Failover (deferred import to avoid circular dependency)
        from .pool import Pool

        task = asyncio.create_task(Pool._handle_node_failover(self.node))
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

        # Dispatch Event
        self.node.client.dispatch("voltricx_node_disconnected", self.node)

        # Reconnect silently
        await self.connect(silent=True)

    async def close(self) -> None:
        """Gracefully close the WebSocket connection."""
        self._closed = True
        if self._keep_alive_task:
            self._keep_alive_task.cancel()

        if self.socket:
            await self.socket.close()

        self.socket = None
        logger.info(f"WebSocket closed for {self.node.identifier}")
