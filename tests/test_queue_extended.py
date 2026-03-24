"""Expanded tests for voltricx.queue — covering all remaining branches."""

import asyncio
from unittest.mock import MagicMock

import pytest

from voltricx.exceptions import QueueEmpty
from voltricx.queue import Queue
from voltricx.typings.enums import QueueMode
from voltricx.typings.track import Playable


def make_track(encoded="enc", title="T"):
    t = MagicMock(spec=Playable)
    t.encoded = encoded
    t.title = title
    return t


# ── __str__ / __repr__ ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_queue_str():
    q = Queue()
    assert "Queue" in str(q)


@pytest.mark.asyncio
async def test_queue_repr():
    q = Queue()
    assert "Queue" in repr(q)


@pytest.mark.asyncio
async def test_queue_bool_empty():
    q = Queue()
    assert bool(q) is False


@pytest.mark.asyncio
async def test_queue_bool_nonempty():
    q = Queue()
    q.put(make_track())
    assert bool(q) is True


# ── Iteration ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_queue_iter():
    q = Queue()
    t1, t2 = make_track("e1"), make_track("e2")
    q.put([t1, t2])
    items = list(q)
    assert t1 in items and t2 in items


@pytest.mark.asyncio
async def test_queue_reversed():
    q = Queue()
    t1, t2 = make_track("e1"), make_track("e2")
    q.put([t1, t2])
    items = list(reversed(q))
    assert items[0] == t2
    assert items[1] == t1


# ── __setitem__ ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_queue_setitem():
    q = Queue()
    t1, t2 = make_track("e1"), make_track("e2")
    q.put([t1, t2])
    q[0] = t2
    assert q[0] == t2


@pytest.mark.asyncio
async def test_queue_setitem_type_error():
    q = Queue()
    q.put(make_track())
    with pytest.raises(TypeError):
        q[0] = "not a track"  # type: ignore


# ── __delitem__ slice ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_queue_delitem_slice():
    q = Queue()
    tracks = [make_track(f"e{i}") for i in range(4)]
    q.put(tracks)
    del q[1:3]
    assert q.count == 2


# ── loop_all mode ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_queue_loop_all_refills_from_history():
    q = Queue()
    t1, t2 = make_track("e1"), make_track("e2")
    # Fake put into history directly
    q._history._items.extend([t1, t2])
    q.mode = QueueMode.loop_all
    # Queue is empty — should refill from history
    track = q.get()
    assert track in (t1, t2)


# ── get_at ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_queue_get_at():
    q = Queue()
    t1, t2, t3 = make_track("e1"), make_track("e2"), make_track("e3")
    q.put([t1, t2, t3])
    result = q.get_at(1)
    assert result == t2
    assert q.count == 2


@pytest.mark.asyncio
async def test_queue_get_at_empty():
    q = Queue()
    with pytest.raises(QueueEmpty):
        q.get_at(0)


# ── pop ────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_queue_pop():
    q = Queue()
    t1, t2 = make_track("e1"), make_track("e2")
    q.put([t1, t2])
    result = q.pop()
    assert result == t2
    assert q.count == 1


@pytest.mark.asyncio
async def test_queue_pop_empty():
    q = Queue()
    with pytest.raises(QueueEmpty):
        q.pop()


# ── get_wait ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_queue_get_wait_immediate():
    q = Queue()
    t = make_track()
    q.put(t)
    result = await q.get_wait()
    assert result == t


@pytest.mark.asyncio
async def test_queue_get_wait_waits_for_item():
    q = Queue()
    t = make_track()

    async def delayed_put():
        await asyncio.sleep(0.01)
        q.put(t)

    asyncio.create_task(delayed_put())
    result = await q.get_wait()
    assert result == t


# ── put_wait ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_queue_put_wait():
    q = Queue()
    t = make_track()
    added = await q.put_wait(t)
    assert added == 1
    assert q.count == 1


# ── put with non-Playable in non-atomic mode ───────────────────────────────


@pytest.mark.asyncio
async def test_queue_put_non_atomic_skips_invalid():
    q = Queue()
    t = make_track()
    # non-atomic with a bad item should skip the bad one
    added = q.put([t, "invalid"], atomic=False)  # type: ignore
    assert added == 1


@pytest.mark.asyncio
async def test_queue_put_atomic_raises_on_invalid():
    q = Queue()
    t = make_track()
    with pytest.raises(TypeError):
        q.put([t, "invalid"], atomic=True)  # type: ignore


# ── put iterable that isn't a list ────────────────────────────────────────


@pytest.mark.asyncio
async def test_queue_put_generator():
    q = Queue()
    t1, t2 = make_track("e1"), make_track("e2")
    added = q.put(iter([t1, t2]))
    assert added == 2


# ── put_at / put_at_front ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_queue_put_at():
    q = Queue()
    t1, t2, t3 = make_track("e1"), make_track("e2"), make_track("e3")
    q.put([t1, t2])
    q.put_at(1, t3)
    assert q[1] == t3


@pytest.mark.asyncio
async def test_queue_put_at_type_error():
    q = Queue()
    q.put(make_track())
    with pytest.raises(TypeError):
        q.put_at(0, "bad")  # type: ignore


# ── delete ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_queue_delete():
    q = Queue()
    t1, t2, t3 = make_track("e1"), make_track("e2"), make_track("e3")
    q.put([t1, t2, t3])
    q.delete(1)
    assert q.count == 2
    assert q[0] == t1
    assert q[1] == t3


# ── peek ───────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_queue_peek():
    q = Queue()
    t = make_track()
    q.put(t)
    assert q.peek() == t
    assert q.count == 1


@pytest.mark.asyncio
async def test_queue_peek_empty():
    q = Queue()
    with pytest.raises(QueueEmpty):
        q.peek()


# ── swap ───────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_queue_swap():
    q = Queue()
    t1, t2 = make_track("e1"), make_track("e2")
    q.put([t1, t2])
    q.swap(0, 1)
    assert q[0] == t2
    assert q[1] == t1


# ── index ──────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_queue_index():
    q = Queue()
    t = make_track()
    q.put(t)
    assert q.index(t) == 0


# ── remove ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_queue_remove():
    q = Queue()
    t = make_track()
    q.put([t, t])
    removed = q.remove(t)
    assert removed == 1


@pytest.mark.asyncio
async def test_queue_remove_all():
    q = Queue()
    t = make_track()
    q.put([t, t, t])
    removed = q.remove(t, count=None)
    assert removed == 3


@pytest.mark.asyncio
async def test_queue_remove_not_found():
    q = Queue()
    t1, t2 = make_track("e1"), make_track("e2")
    q.put(t1)
    removed = q.remove(t2)
    assert removed == 0


# ── reset ──────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_queue_reset():
    q = Queue()
    t = make_track()
    q.put(t)
    q.mode = QueueMode.loop
    q._loaded = t
    q.reset()
    assert q.count == 0
    assert q.mode == QueueMode.normal
    assert q.loaded is None


# ── loaded setter ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_queue_loaded_setter():
    q = Queue()
    t = make_track()
    q.loaded = t
    assert q.loaded == t


@pytest.mark.asyncio
async def test_queue_loaded_setter_none():
    q = Queue()
    q.loaded = None
    assert q.loaded is None


@pytest.mark.asyncio
async def test_queue_loaded_setter_type_error():
    q = Queue()
    with pytest.raises(TypeError):
        q.loaded = "not a playable"  # type: ignore


# ── history=False variant ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_queue_no_history():
    q = Queue(history=False)
    assert q.history is None
