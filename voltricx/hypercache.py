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

import secrets
from collections import OrderedDict
from collections.abc import Hashable
from typing import Any, Union

from .typings.common import HyperCacheConfig


class BaseCache[T]:
    """Base class for cache implementations."""

    def __init__(self, capacity: int):
        self.capacity = capacity
        self._data: dict[Hashable, Any] = {}

    def __len__(self) -> int:
        return len(self._data)

    def __contains__(self, key: Hashable) -> bool:
        return key in self._data

    def __getitem__(self, key: Hashable) -> Any:
        if key not in self._data:
            raise KeyError(key)
        return self._data[key]

    def __setitem__(self, key: Hashable, value: Any) -> None:
        self._data[key] = value

    def clear(self) -> None:
        self._data.clear()


class LRUCache[T](BaseCache[T]):
    """Least Recently Used Cache implementation."""

    def __init__(self, capacity: int):
        super().__init__(capacity)
        self._data: OrderedDict[Hashable, Any] = OrderedDict()  # type: ignore[assignment]

    def __getitem__(self, key: Hashable) -> T:
        if key not in self._data:
            raise KeyError(key)
        self._data.move_to_end(key)
        return self._data[key]

    def __setitem__(self, key: Hashable, value: T) -> None:
        if key in self._data:
            self._data.move_to_end(key)
        self._data[key] = value
        if len(self._data) > self.capacity:
            self._data.popitem(last=False)  # type: ignore

    def get(self, key: Hashable) -> T | None:
        if key not in self._data:
            return None
        self._data.move_to_end(key)
        return self._data[key]

    def put(self, key: Hashable, value: T) -> None:
        self[key] = value


class LFUCache[T](BaseCache[T]):
    """Least Frequently Used Cache implementation with Aging/Decay."""

    def __init__(self, capacity: int, decay_factor: float = 0.5, decay_threshold: int = 1000):
        super().__init__(capacity)
        self._frequencies: dict[Hashable, int] = {}
        self.decay_factor = decay_factor
        self.decay_threshold = decay_threshold
        self._total_hits = 0

    def _apply_decay(self):
        """Reduces all frequency counts to allow new items to surface."""
        for key in self._frequencies:
            self._frequencies[key] = int(self._frequencies[key] * self.decay_factor)
        self._total_hits = 0

    def get(self, key: Hashable) -> T | None:
        if key not in self._data:
            return None

        self._total_hits += 1
        if self._total_hits >= self.decay_threshold:
            self._apply_decay()

        self._frequencies[key] = self._frequencies.get(key, 0) + 1
        return self._data[key]

    def put(self, key: Hashable, value: T) -> None:
        if key not in self._data and len(self._data) >= self.capacity:
            # Evict the least frequent
            if self._frequencies:
                lfu_key = min(self._frequencies.keys(), key=lambda k: self._frequencies[k])
                self._data.pop(lfu_key, None)
                self._frequencies.pop(lfu_key, None)

        self._data[key] = value
        self._frequencies[key] = self._frequencies.get(key, 0) + 1


class HyperCache:
    """
    Dual-Tiered Cache System.
    L1: QueryCache (LRU) - Maps search queries to track IDs.
    L2: TrackRegistry (LFU) - Stores actual track objects with hit decay.
    """

    def __init__(
        self,
        query_capacity: int = 100,
        track_capacity: int = 1000,
        decay_factor: float = 0.5,
        decay_threshold: int = 1000,
    ):
        self.l1 = LRUCache[list[str]](query_capacity)
        self.l2 = LFUCache[Any](
            capacity=track_capacity,
            decay_factor=decay_factor,
            decay_threshold=decay_threshold,
        )

    def get_query(self, query: str) -> list[Any] | None:
        """Get tracks for a query, hydrating from L2."""
        track_ids = self.l1.get(query)
        if not track_ids:
            return None

        tracks = []
        for tid in track_ids:
            track = self.l2.get(tid)
            if track:
                tracks.append(track)
            else:
                # If a track is missing from L2, the entire query cache result is stale-ish
                # or we just return what we have. Most robust is to return None and re-fetch.
                return None
        return tracks

    def put_query(self, query: str, tracks: list[Any]) -> None:
        """Store query results and update track registry."""

        track_ids = []
        for track in tracks:
            # We assume tracks have an 'encoded' field as a unique ID
            if hasattr(track, "encoded"):
                tid = track.encoded
                track_ids.append(tid)
                self.l2.put(tid, track)
            else:
                # Fallback if not a Playable object
                continue

        if track_ids:
            self.l1.put(query, track_ids)

    def get_stats(self) -> dict[str, int]:
        """Return current cache sizes for verification."""
        return {"l1_queries": len(self.l1), "l2_tracks": len(self.l2)}

    def get_entries(self) -> dict[str, list[str]]:
        """Return a mapping of queries to track titles for inspection."""
        results = {}
        for query, track_ids in self.l1._data.items():
            titles = []
            for tid in track_ids:
                track = self.l2.get(tid)
                if track:
                    # Prefer title from Playable object, fallback to tid
                    titles.append(getattr(track, "title", str(tid)))
            results[str(query)] = titles
        return results

    def get_random_track(self) -> Any | None:
        """Retrieve a random track from the L2 cache (TrackRegistry)."""
        if not self.l2._data:
            return None
        return secrets.choice(list(self.l2._data.values()))

    @classmethod
    def from_config(cls, config: Union[dict[str, Any], HyperCacheConfig]) -> "HyperCache":
        """Create a HyperCache instance from a config dictionary or model."""
        if isinstance(config, dict):
            config = HyperCacheConfig(**config)

        return cls(
            query_capacity=config.capacity,
            track_capacity=config.track_capacity,
            decay_factor=config.decay_factor,
            decay_threshold=config.decay_threshold,
        )

    def resize_from_config(self, config: Union[dict[str, Any], HyperCacheConfig]):
        """Resize the cache using a config dictionary or model."""
        if isinstance(config, dict):
            config = HyperCacheConfig(**config)

        self.resize(
            query_capacity=config.capacity,
            track_capacity=config.track_capacity,
            decay_factor=config.decay_factor,
            decay_threshold=config.decay_threshold,
        )

    def resize(
        self,
        query_capacity: int | None = None,
        track_capacity: int | None = None,
        decay_factor: float | None = None,
        decay_threshold: int | None = None,
    ):
        """Resizes the cache tiers and updates decay settings."""
        if query_capacity is not None:
            new_l1 = LRUCache[list[str]](query_capacity)
            for k, v in self.l1._data.items():
                new_l1.put(k, v)
            self.l1 = new_l1

        # Capture current L2 settings if not provided
        df = decay_factor if decay_factor is not None else self.l2.decay_factor
        dt = decay_threshold if decay_threshold is not None else self.l2.decay_threshold
        cap = track_capacity if track_capacity is not None else self.l2.capacity

        if any(v is not None for v in [track_capacity, decay_factor, decay_threshold]):
            new_l2 = LFUCache[Any](capacity=cap, decay_factor=df, decay_threshold=dt)
            for k, v in self.l2._data.items():
                new_l2.put(k, v)
            self.l2 = new_l2
