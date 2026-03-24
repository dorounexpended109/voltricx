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
import secrets
from collections import deque
from collections.abc import Iterable, Iterator
from typing import (
    SupportsIndex,
    overload,
)

from .exceptions import QueueEmpty
from .typings.enums import QueueMode
from .typings.track import Playable, Playlist

_QUEUE_EMPTY = "The queue is empty."


class Queue:
    """The default custom voltricx Queue designed specifically for :class:`voltricx.Player`."""

    def __init__(self, *, history: bool = True) -> None:
        self._items: deque[Playable] = deque()
        self._history: Queue | None = Queue(history=False) if history else None
        self._mode: QueueMode = QueueMode.normal
        self._loaded: Playable | None = None
        self._waiters: deque[asyncio.Future[None]] = deque()
        self._lock = asyncio.Lock()

    @property
    def mode(self) -> QueueMode:
        return self._mode

    @mode.setter
    def mode(self, value: QueueMode) -> None:
        self._mode = value

    @property
    def history(self) -> Queue | None:
        return self._history

    @property
    def count(self) -> int:
        return len(self._items)

    @property
    def is_empty(self) -> bool:
        return not bool(self._items)

    def __str__(self) -> str:
        return f"Queue(items={len(self._items)}, history={bool(self._history)})"

    def __repr__(self) -> str:
        return f"<Queue items={len(self._items)} history={self._history!r}>"

    def __bool__(self) -> bool:
        return bool(self._items)

    @overload
    def __getitem__(self, index: SupportsIndex) -> Playable: ...

    @overload
    def __getitem__(self, index: slice) -> list[Playable]: ...

    def __getitem__(self, index: SupportsIndex | slice) -> Playable | list[Playable]:
        if isinstance(index, slice):
            return list(self._items)[index]
        return self._items[index]

    def __setitem__(self, index: SupportsIndex, value: Playable) -> None:
        if not isinstance(value, Playable):
            raise TypeError("Only Playable objects can be added to the queue.")
        self._items[index] = value
        self._wakeup_next()

    def __delitem__(self, index: SupportsIndex | slice) -> None:
        if isinstance(index, slice):
            temp = list(self._items)
            del temp[index]
            self._items = deque(temp)
        else:
            # Single index deletion - using rotate and popleft for pure deque operation
            # or just list pop if it satisfies linter.
            temp = list(self._items)
            temp.pop(index)
            self._items = deque(temp)

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self) -> Iterator[Playable]:
        return iter(self._items)

    def __reversed__(self) -> Iterator[Playable]:
        return reversed(self._items)

    def _wakeup_next(self) -> None:
        while self._waiters:
            waiter = self._waiters.popleft()
            if not waiter.done():
                waiter.set_result(None)
                break

    def get(self) -> Playable:
        if self._mode is QueueMode.loop and self._loaded:
            return self._loaded

        if self._mode is QueueMode.loop_all and not self._items and self._history:
            self._items.extend(self._history._items)
            self._history.clear()

        if not self._items:
            raise QueueEmpty(_QUEUE_EMPTY)

        track = self._items.popleft()
        self._loaded = track
        return track

    def get_at(self, index: int) -> Playable:
        if not self._items:
            raise QueueEmpty(_QUEUE_EMPTY)

        # Deque doesn't support pop(index), so we rotate
        self._items.rotate(-index)
        track = self._items.popleft()
        self._items.rotate(index)

        self._loaded = track
        return track

    def pop(self) -> Playable:
        """Remove and return the last item from the queue (right side)."""
        if not self._items:
            raise QueueEmpty(_QUEUE_EMPTY)
        return self._items.pop()

    async def get_wait(self) -> Playable:
        while not self._items:
            loop = asyncio.get_running_loop()
            waiter = loop.create_future()
            self._waiters.append(waiter)
            try:
                await waiter
            except Exception:
                waiter.cancel()
                if waiter in self._waiters:
                    self._waiters.remove(waiter)
                raise
        return self.get()

    @staticmethod
    def _normalize_items(
        item: Playable | Playlist | Iterable[Playable],
    ) -> list[Playable]:
        """Coerce any supported input type into a flat list of Playable objects."""
        if isinstance(item, Playlist):
            return item.tracks
        if isinstance(item, Playable):
            return [item]
        if isinstance(item, Iterable) and not isinstance(item, str | bytes):
            return list(item)  # type: ignore
        return [item]  # type: ignore

    def put(
        self,
        item: Playable | Playlist | Iterable[Playable],
        *,
        atomic: bool = True,
    ) -> int:
        tracks = self._normalize_items(item)
        added = 0

        if atomic:
            for t in tracks:
                if not isinstance(t, Playable):
                    raise TypeError("All items must be Playable instances.")
            self._items.extend(tracks)
            added = len(tracks)
        else:
            for t in tracks:
                if isinstance(t, Playable):
                    self._items.append(t)
                    added += 1

        self._wakeup_next()
        return added

    async def put_wait(
        self,
        item: Playable | Playlist | Iterable[Playable],
        *,
        atomic: bool = True,
    ) -> int:
        async with self._lock:
            added = self.put(item, atomic=atomic)
            return added

    def put_at(self, index: int, item: Playable) -> None:
        if not isinstance(item, Playable):
            raise TypeError("Item must be a Playable instance.")
        self._items.insert(index, item)
        self._wakeup_next()

    def put_at_front(self, item: Playable) -> None:
        """Add an item to the very front of the queue."""
        self.put_at(0, item)

    def delete(self, index: int) -> None:
        # Deque doesn't support pop(index) well, using list conversion
        temp = list(self._items)
        temp.pop(index)
        self._items = deque(temp)

    def peek(self, index: int = 0) -> Playable:
        if not self._items:
            raise QueueEmpty(_QUEUE_EMPTY)
        return self._items[index]

    def swap(self, first: int, second: int) -> None:
        self._items[first], self._items[second] = (
            self._items[second],
            self._items[first],
        )

    def index(self, item: Playable) -> int:
        return self._items.index(item)

    def shuffle(self) -> None:
        temp = list(self._items)
        secrets.SystemRandom().shuffle(temp)
        self._items = deque(temp)

    def clear(self) -> None:
        self._items.clear()

    def reset(self) -> None:
        self.clear()
        if self._history:
            self._history.clear()
        for waiter in self._waiters:
            waiter.cancel()
        self._waiters.clear()
        self._mode = QueueMode.normal
        self._loaded = None

    def remove(self, item: Playable, *, count: int | None = 1) -> int:
        removed = 0
        if count is None:
            while True:
                try:
                    self._items.remove(item)
                    removed += 1
                except ValueError:
                    break
        else:
            for _ in range(count):
                try:
                    self._items.remove(item)
                    removed += 1
                except ValueError:
                    break
        return removed

    @property
    def loaded(self) -> Playable | None:
        return self._loaded

    @loaded.setter
    def loaded(self, value: Playable | None) -> None:
        if value is not None and not isinstance(value, Playable):
            raise TypeError("value must be a Playable instance or None.")
        self._loaded = value
