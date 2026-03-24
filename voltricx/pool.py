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
from collections.abc import Iterable
from typing import TYPE_CHECKING, Any, ClassVar

import discord

from .exceptions import InvalidNodeException, LavalinkLoadException
from .hypercache import HyperCache
from .logger import voltricx_logger
from .node import Node
from .typings.enums import LoadType, NodeStatus
from .typings.track import Playable, Playlist, TrackException

if TYPE_CHECKING:
    from .typings.common import HyperCacheConfig
    from .typings.node import NodeConfig

logger: logging.Logger = logging.getLogger(__name__)

# High-fidelity region map ported from original logic
REGIONS: dict[str, list[str]] = {
    "asia": [
        "bom",
        "maa",
        "nrt",
        "hnd",
        "sin",
        "kul",
        "bkk",
        "cgn",
        "icn",
        "hkg",
        "tpe",
        "syd",
        "mel",
        "akl",
    ],
    "eu": [
        "ams",
        "fra",
        "ber",
        "lhr",
        "lon",
        "cdg",
        "mad",
        "bcg",
        "waw",
        "mil",
        "rom",
        "arn",
        "hel",
        "osl",
        "cph",
        "prg",
        "bud",
        "vie",
    ],
    "us": [
        "iad",
        "atl",
        "mia",
        "bos",
        "jfk",
        "ord",
        "dfw",
        "lax",
        "sea",
        "sjc",
        "phx",
        "den",
    ],
    "southamerica": ["gru", "scl", "eze", "lim", "bog"],
    "africa": ["jnb", "cpt", "nbo"],
    "middleeast": ["dxb", "auh", "ruh", "tel"],
}


class Pool:
    """
    Central manager for Lavalink nodes and global caching.

    Provides high-fidelity node selection, region mapping, and track search.
    """

    __nodes: ClassVar[dict[str, Node]] = {}
    __cache: ClassVar[HyperCache | None] = None
    _regions: ClassVar[dict[str, list[str]]] = REGIONS
    _tasks: ClassVar[set[asyncio.Task[Any]]] = set()
    _client: ClassVar[discord.Client | None] = None
    _default_search_source: ClassVar[str | None] = None

    @classmethod
    async def connect(
        cls,
        *,
        client: discord.Client,
        nodes: Iterable[NodeConfig],
        cache_config: dict[str, Any] | HyperCacheConfig | None = None,
        regions: dict[str, list[str]] | None = None,
        default_search_source: str | None = None,
    ) -> dict[str, Node]:
        """
        Connect to multiple Lavalink nodes and initialize global systems.
        """
        if regions:
            cls._regions = regions

        cls._client = client
        cls._default_search_source = default_search_source

        if cache_config:
            cls.__cache = HyperCache.from_config(cache_config)
            if voltricx_logger.enabled:
                voltricx_logger.system("HyperCache system initialized for Pool.")

        coros = []
        for config in nodes:
            node = Node(config=config, client=client)
            coros.append(cls._add_node(node))

        await asyncio.gather(*coros)

        # Wait up to 5 seconds for all nodes to show as connected
        deadline = asyncio.get_event_loop().time() + 5.0
        while asyncio.get_event_loop().time() < deadline:
            connected_nodes = [n for n in cls.__nodes.values() if n.status == NodeStatus.connected]
            if len(connected_nodes) == len(cls.__nodes):
                break
            await asyncio.sleep(0.5)

        cls._display_report()

        return cls.__nodes

    @classmethod
    async def _add_node(cls, node: Node) -> None:
        """Register and connect a Node."""
        if node.identifier in cls.__nodes:
            if voltricx_logger.enabled:
                voltricx_logger.warning(
                    f"Node identifier '{node.identifier}' already in use. Skipping."
                )
            return

        try:
            await node.connect()
            cls.__nodes[node.identifier] = node
        except Exception as e:  # pylint: disable=broad-exception-caught
            if voltricx_logger.enabled:
                voltricx_logger.error(f"Failed to connect Node {node.identifier}: {e}")

    @classmethod
    def _display_report(cls) -> None:
        """Cosmetic report of node connection statuses."""
        connected = [n for n in cls.__nodes.values() if n.status == NodeStatus.connected]
        total = len(cls.__nodes)

        print(
            f"\n\033[93m[Lavalink]\033[0m Node connection report "
            f"(\033[92m{len(connected)}\033[0m/\033[93m{total}\033[0m connected)\n"
        )
        for node in cls.__nodes.values():
            color = "\033[92m" if node.status == NodeStatus.connected else "\033[91m"
            status_text = "CONNECTED" if node.status == NodeStatus.connected else "FAILED"
            print(
                f"  {color}[{status_text}]\033[0m "
                f"\033[94m{node.identifier:<10}\033[0m "
                f"{color}{node.uri:<30}\033[0m "
                f"\033[2mregion=\033[0m\033[36m{node.config.region}\033[0m"
            )
        print("")

    @classmethod
    def get_node(cls, identifier: str | None = None, *, region: str | None = None) -> Node:
        """
        Retrieve a node by identifier or find the healthiest one.
        """
        if identifier:
            if identifier not in cls.__nodes:
                raise InvalidNodeException(f"Node '{identifier}' not found in Pool.")
            return cls.__nodes[identifier]

        connected_nodes = [n for n in cls.__nodes.values() if n.status == NodeStatus.connected]
        if not connected_nodes:
            raise InvalidNodeException("No connected nodes available in Pool.")

        if region:
            region_nodes = [n for n in connected_nodes if n.config.region == region]
            if region_nodes:
                return min(region_nodes, key=lambda n: n.penalty)
            if voltricx_logger.enabled:
                voltricx_logger.debug(
                    f"No nodes found for region '{region}'. Falling back to global selection."
                )

        return min(connected_nodes, key=lambda n: n.penalty)

    @classmethod
    def region_from_endpoint(cls, endpoint: str | None) -> str:
        """Map a Discord voice endpoint string to a region name."""
        if not endpoint:
            return "global"

        endpoint = endpoint.lower()
        for region, prefix_list in cls._regions.items():
            for prefix in prefix_list:
                if prefix in endpoint:
                    return region
        return "global"

    @classmethod
    def _prepare_query(cls, query: str) -> str:
        """Apply the default search source prefix to bare queries."""
        if not cls._default_search_source:
            return query
        if query.startswith("http") or ":" in query:
            return query
        if " " in query:
            return f'{cls._default_search_source}:"{query}"'
        return f"{cls._default_search_source}:{query}"

    @classmethod
    def _build_node_list(
        cls,
        *,
        region: str | None = None,
        preferred_node: Node | None = None,
    ) -> list[Node]:
        """Build a priority-sorted list of connected nodes for track loading."""
        connected = [n for n in cls.__nodes.values() if n.status == NodeStatus.connected]
        if region:
            connected = [n for n in connected if n.config.region == region]

        if preferred_node is not None and preferred_node.status == NodeStatus.connected:
            connected = [preferred_node] + [n for n in connected if n != preferred_node]

        if not connected:
            # Fallback: drop region filter and try all connected nodes
            connected = [n for n in cls.__nodes.values() if n.status == NodeStatus.connected]

        if not connected:
            raise InvalidNodeException("No connected nodes available in Pool.")

        connected.sort(key=lambda n: n.penalty)
        return connected

    @classmethod
    def _parse_track_result(
        cls, load_type: str, result_data: Any
    ) -> list[Playable] | Playlist | None:
        """Parse a Lavalink loadType response into a typed result, or None for error/empty."""
        if load_type == LoadType.track:
            return [Playable(**result_data)]
        if load_type == LoadType.playlist:
            return Playlist(**result_data)
        if load_type == LoadType.search:
            return [Playable(**t) for t in result_data]
        return None

    @classmethod
    def _get_cached_tracks(cls, query: str) -> list[Playable] | Playlist | None:
        """Check cache for existing tracks."""
        if cls.__cache:
            return cls.__cache.get_query(query)
        return None

    @classmethod
    async def _try_load_from_node(
        cls, target_node: Node, query: str
    ) -> tuple[list[Playable] | Playlist | None, Exception | None]:
        """Attempt to load tracks from a single node. Returns (result, exception)."""
        if voltricx_logger.enabled:
            voltricx_logger.debug(
                f"Attempting track load on node {target_node.identifier} with query: {query}"
            )

        try:
            data = await target_node.load_tracks(query)
            load_type = data.get("loadType")
            result_data = data.get("data", {})

            if load_type == LoadType.error:
                if voltricx_logger.enabled:
                    voltricx_logger.warning(
                        f"Node {target_node.identifier} failed track load: "
                        f"{result_data.get('message', 'Unknown error')}"
                    )
                return None, LavalinkLoadException(data=TrackException(**result_data))

            parsed = cls._parse_track_result(load_type, result_data)
            if parsed is not None:
                if voltricx_logger.enabled:
                    voltricx_logger.info(
                        f"Successfully loaded tracks from node {target_node.identifier}"
                    )
                return parsed, None

            return None, None

        except Exception as e:  # pylint: disable=broad-exception-caught
            if voltricx_logger.enabled:
                voltricx_logger.error(
                    f"Error loading tracks from node {target_node.identifier}: {e}"
                )
            return None, e

    @classmethod
    def _populate_cache(cls, query: str, result: list[Playable] | Playlist) -> None:
        """Store tracks in cache if caching is enabled."""
        if cls.__cache and result:
            cache_data = result if isinstance(result, list) else result.tracks
            cls.__cache.put_query(query, cache_data)

    @classmethod
    async def fetch_tracks(
        cls, query: str, *, region: str | None = None, node: Node | None = None
    ) -> list[Playable] | Playlist:
        """Fetch tracks from Lavalink with global cache support."""
        query = cls._prepare_query(query)

        # Tier 1: Cache Check
        cached = cls._get_cached_tracks(query)
        if cached:
            return cached

        # Tier 2: Lavalink Request
        target_nodes = cls._build_node_list(region=region, preferred_node=node)
        last_exception: Exception | None = None
        result: list[Playable] | Playlist = []

        for target_node in target_nodes:
            parsed, error = await cls._try_load_from_node(target_node, query)
            if parsed is not None:
                result = parsed
                break
            if error:
                last_exception = error

        if not result and last_exception:
            raise last_exception

        # Tier 3: Cache Population
        cls._populate_cache(query, result)

        return result

    @classmethod
    async def _failover_player(
        cls,
        player: Any,
        *,
        failed_node: Node,
        healthy_nodes: list[Node],
    ) -> None:
        """Migrate a single player to the best healthy node for its region."""
        endpoint = player._voice_state.get("endpoint")
        region = cls.region_from_endpoint(endpoint)
        region_candidates = [n for n in healthy_nodes if n.config.region == region]
        new_node = min(region_candidates or healthy_nodes, key=lambda n: n.penalty)

        if voltricx_logger.enabled:
            guild_id = getattr(player.guild, "id", "Unknown")
            voltricx_logger.node(
                f"Failing over player for guild {guild_id} "
                f"from {failed_node.identifier} to {new_node.identifier}"
            )

        try:
            await player.migrate_to(new_node)
        except Exception as e:  # pylint: disable=broad-exception-caught
            if voltricx_logger.enabled:
                guild_id = getattr(player.guild, "id", "Unknown")
                voltricx_logger.error(f"Failover failed for guild {guild_id}: {e}")

    @classmethod
    async def _handle_node_failover(cls, node: Node) -> None:
        """Deep port of the original failover logic to migrate players."""
        players = node.players
        if not players:
            return

        healthy_nodes: list[Node] = []
        for _ in range(50):
            healthy_nodes = [
                n for n in cls.__nodes.values() if n.status == NodeStatus.connected and n != node
            ]
            if healthy_nodes:
                break
            await asyncio.sleep(0.1)

        if not healthy_nodes:
            if voltricx_logger.enabled:
                voltricx_logger.warning(
                    f"Node {node.identifier} failing, but no candidate nodes "
                    f"available for failover."
                )
            return

        target_node = min(healthy_nodes, key=lambda n: n.penalty)
        if voltricx_logger.enabled:
            voltricx_logger.info(
                f"Failing over {len(players)} players from "
                f"{node.identifier} to {target_node.identifier}"
            )

        if cls._client:
            cls._client.dispatch("voltricx_failover", node, target_node, list(players.values()))

        for player in players.values():
            await cls._failover_player(player, failed_node=node, healthy_nodes=healthy_nodes)

    @classmethod
    async def close(cls) -> None:
        """Shutdown all nodes and clear systems."""
        for node in cls.__nodes.copy().values():
            await node.disconnect(force=True)
        cls.__nodes.clear()
        cls.__cache = None

    @classmethod
    def get_cache_stats(cls) -> dict[str, int]:
        """Expose current HyperCache stats if initialized."""
        cache = cls.__cache
        if cache:
            return cache.get_stats()
        return {"l1_queries": 0, "l2_tracks": 0}

    @classmethod
    def get_cache_entries(cls) -> dict[str, list[str]]:
        """Expose current HyperCache entries if initialized."""
        cache = cls.__cache
        if cache:
            return cache.get_entries()
        return {}

    @classmethod
    def get_random_cached_track(cls) -> Playable | None:
        """Retrieve a random track from the global HyperCache L2."""
        if cls.__cache:
            return cls.__cache.get_random_track()
        return None

    @classmethod
    def export_cache_data(cls) -> dict[str, Any]:
        """Export the full state of the HyperCache."""
        if not cls.__cache:
            return {"l1": {}, "l2": {}}

        return {
            "l1": cls.__cache.l1._data,  # LRU OrderedDict: query -> track_ids
            "l2": {
                tid: getattr(t, "title", str(t)) for tid, t in cls.__cache.l2._data.items()
            },  # ID -> Title
        }

    @classmethod
    def nodes(cls) -> dict[str, Node]:
        """Returns a snapshot of current node registry."""
        return cls.__nodes.copy()
