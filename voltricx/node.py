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

import logging
from typing import TYPE_CHECKING, Any

import aiohttp
import discord

from .exceptions import LavalinkException, NodeException
from .logger import voltricx_logger
from .typings.enums import NodeStatus
from .typings.node import (
    CPUStats,
    ErrorResponse,
    FrameStats,
    MemoryStats,
    NodeConfig,
    NodeInfo,
)
from .typings.routeplanner import RoutePlannerFreeAddressPayload, RoutePlannerStatus
from .typings.track import Playable
from .websocket import Websocket

if TYPE_CHECKING:
    from .player import Player

logger: logging.Logger = logging.getLogger(__name__)


class Node:
    """
    Represents a connection to a Lavalink node.

    This class handles the REST API and coordinates the WebSocket connection.
    Built with high fidelity to the original logic, ensuring all features are preserved.
    """

    def __init__(
        self,
        *,
        config: NodeConfig,
        client: discord.Client,
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        self.config = config
        self.client = client
        self._session = session or aiohttp.ClientSession()

        self.status = NodeStatus.disconnected
        self.session_id: str | None = None

        self._players: dict[int, Player] = {}
        self._websocket: Websocket | None = None

        self.info: NodeInfo | None = None
        self.stats_memory: MemoryStats | None = None
        self.stats_cpu: CPUStats | None = None
        self.stats_frames: FrameStats | None = None
        self.playing_count: int = 0

    def __repr__(self) -> str:
        return (
            f"<Node identifier={self.identifier} status={self.status.value} "
            f"region={self.config.region} players={len(self._players)}>"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Node):
            return NotImplemented
        return self.identifier == other.identifier

    @property
    def identifier(self) -> str:
        return self.config.identifier

    @property
    def uri(self) -> str:
        return self.config.uri

    @property
    def headers(self) -> dict[str, str]:
        """Generate headers for Lavalink requests."""
        headers = {
            "Authorization": self.config.password,
            "User-Id": str(self.client.user.id if self.client.user else 0),
            "Client-Name": "Voltricx/Modern",
        }
        if self.session_id:
            headers["Session-Id"] = self.session_id
        return headers

    @property
    def players(self) -> dict[int, Player]:
        return self._players.copy()

    @property
    def penalty(self) -> float:
        """
        Calculate the load penalty for this node.
        Lower values indicate a healthier node.

        High-fidelity penalty logic ported from the original codebase.
        """
        if self.status != NodeStatus.connected or not self.stats_cpu:
            return 9e30  # Infinite penalty if not connected

        # CPU Penalty: Exponential increase based on system load
        cpu = (1.05 ** (100 * self.stats_cpu.system_load) * 10) - 10

        # Frame Penalty: Severe penalty for frame deficits or nulled frames
        if self.stats_frames:
            frames_deficit = 1.03 ** (500 * (self.stats_frames.deficit / 3000)) * 300 - 300
            frames_nulled = (1.03 ** (500 * (self.stats_frames.nulled / 3000)) * 300 - 300) * 2
        else:
            frames_deficit = 0
            frames_nulled = 0

        # Player Penalty: Linear cost per playing player
        players = self.playing_count * 1.5

        return cpu + frames_deficit + frames_nulled + players

    async def connect(self, *, silent: bool = False) -> None:
        """Initiate the WebSocket connection."""
        if self.status == NodeStatus.connected:
            return

        self.status = NodeStatus.connecting
        self._websocket = Websocket(node=self)
        try:
            await self._websocket.connect(silent=silent)
        except Exception as e:
            self.status = NodeStatus.disconnected
            if voltricx_logger.enabled and not silent:
                voltricx_logger.error(f"Failed to connect to Node {self.identifier}: {e}")
            raise

    async def disconnect(self, *, force: bool = False) -> None:
        """Close the connection and cleanup players."""
        if force:
            for player in self._players.copy().values():
                await player.disconnect()
            self._players.clear()
        elif self.session_id:
            # If not forcing, we should still try to destroy players on Lavalink side
            # to avoid "Channel is closed" errors when the socket shuts down.
            for guild_id in self._players:
                try:
                    await self._destroy_player(guild_id)
                except Exception:
                    # Best-effort cleanup: ignore errors if Lavalink is unreachable.
                    pass

        if self._websocket:
            await self._websocket.close()

        self.status = NodeStatus.disconnected
        self.session_id = None

    async def request(
        self,
        method: str,
        path: str,
        *,
        data: Any | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """Make a REST request to the Lavalink node with Pydantic error handling."""
        url = f"{self.uri.removesuffix('/')}/{path.lstrip('/')}"

        if voltricx_logger.enabled:
            voltricx_logger.outgoing(
                "REST request",
                node_id=self.identifier,
                method=method,
                path=path,
            )

        async with self._session.request(
            method, url, json=data, params=params, headers=self.headers
        ) as resp:
            if voltricx_logger.enabled:
                voltricx_logger.incoming(
                    "REST response",
                    node_id=self.identifier,
                    method=method,
                    path=path,
                    status=resp.status,
                )
            if resp.status == 204:
                return None

            try:
                raw_data = await resp.json()
            except (aiohttp.ContentTypeError, ValueError, TypeError) as exc:
                if resp.status >= 300:
                    raise NodeException(msg=await resp.text(), status=resp.status) from exc
                return await resp.text()

            if resp.status >= 300:
                try:
                    error_payload = ErrorResponse(**raw_data)
                    raise LavalinkException(data=error_payload)
                except (TypeError, ValueError) as exc:
                    raise NodeException(msg=str(raw_data), status=resp.status) from exc

            return raw_data

    # --- REST Coverage Methods ---

    async def fetch_info(self) -> NodeInfo:
        """Fetch node information."""
        data = await self.request("GET", "/v4/info")
        self.info = NodeInfo(**data)
        return self.info

    async def refresh_info(self) -> NodeInfo:
        """Alias for fetch_info for compatibility."""
        return await self.fetch_info()

    async def fetch_stats(self) -> dict[str, Any]:
        """Fetch current node stats."""
        return await self.request("GET", "/v4/stats")

    async def fetch_version(self) -> str:
        """Fetch Lavalink version."""
        return await self.request("GET", "/version")

    async def update_session(self, *, resuming: bool = True, resume_timeout: int = 60) -> Any:
        """Update session configuration (e.g. for resuming).

        Parameters
        ----------
        resuming: bool
            Whether the session should be resumable.
        resume_timeout: int
            How long (in seconds) Lavalink should wait for the client to reconnect
            before discarding the session. This is a server-side value, not a
            Python asyncio timeout.
        """
        if not self.session_id:
            raise NodeException("Cannot update session without a session ID.")

        data = {"resuming": resuming, "timeout": resume_timeout}
        return await self.request("PATCH", f"/v4/sessions/{self.session_id}", data=data)

    async def load_tracks(self, query: str) -> Any:
        """Fetch tracks from Lavalink."""
        params = {"identifier": query}
        return await self.request("GET", "/v4/loadtracks", params=params)

    async def decode_track(self, encoded: str) -> Playable:
        """Decode a base64 encoded track."""
        params = {"encodedTrack": encoded}
        data = await self.request("GET", "/v4/decodetrack", params=params)
        return Playable(**data)

    async def decode_tracks(self, encoded_list: list[str]) -> list[Playable]:
        """Decode a list of base64 encoded tracks."""
        data = await self.request("POST", "/v4/decodetracks", data=encoded_list)
        return [Playable(**t) for t in data]

    # --- RoutePlanner Methods ---

    async def fetch_routeplanner_status(self) -> RoutePlannerStatus | None:
        """Fetch RoutePlanner status."""
        try:
            data = await self.request("GET", "/v4/routeplanner/status")
            return RoutePlannerStatus(**data) if data else None
        except LavalinkException as e:
            if e.status == 404:
                return None
            raise

    async def free_address(self, address: str) -> None:
        """Unmark a failed address."""
        payload = RoutePlannerFreeAddressPayload(address=address)
        await self.request("POST", "/v4/routeplanner/free/address", data=payload.model_dump())

    async def free_all_addresses(self) -> None:
        """Unmark all failed addresses."""
        await self.request("POST", "/v4/routeplanner/free/all")

    # --- Player Helper Methods ---

    def get_player(self, guild_id: int) -> Player | None:
        return self._players.get(guild_id)

    async def fetch_player(self, guild_id: int) -> dict[str, Any] | None:
        """Fetch a specific player's state from Lavalink."""
        if not self.session_id:
            return None
        try:
            return await self.request("GET", f"/v4/sessions/{self.session_id}/players/{guild_id}")
        except LavalinkException as e:
            if e.status == 404:
                return None
            raise

    async def fetch_players(self) -> list[dict[str, Any]]:
        """Fetch all players from Lavalink."""
        if not self.session_id:
            return []
        return await self.request("GET", f"/v4/sessions/{self.session_id}/players")

    async def _update_player(
        self, guild_id: int, *, data: dict[str, Any], replace: bool = False
    ) -> Any:
        if not self.session_id:
            raise NodeException("Session ID missing. Node might not be ready.")
        query = {"noReplace": str(not replace).lower()}
        return await self.request(
            "PATCH",
            f"/v4/sessions/{self.session_id}/players/{guild_id}",
            data=data,
            params=query,
        )

    async def _destroy_player(self, guild_id: int) -> None:
        if not self.session_id:
            return
        await self.request("DELETE", f"/v4/sessions/{self.session_id}/players/{guild_id}")
