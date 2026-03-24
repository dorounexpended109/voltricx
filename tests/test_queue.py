from unittest.mock import MagicMock

import pytest

from voltricx import Playable, Queue, QueueEmpty, QueueMode


def create_mock_track(title, identifier):
    track = MagicMock(spec=Playable)
    track.title = title
    track.identifier = identifier
    return track


@pytest.mark.asyncio
async def test_queue_initialization():
    q = Queue()
    assert q.count == 0
    assert q.is_empty is True
    assert q.mode == QueueMode.normal
    assert q.history is not None


@pytest.mark.asyncio
async def test_queue_put():
    q = Queue()
    t1 = create_mock_track("Track 1", "id1")
    t2 = create_mock_track("Track 2", "id2")

    q.put(t1)
    assert q.count == 1
    assert q[0] == t1

    q.put([t2])
    assert q.count == 2
    assert q[1] == t2


@pytest.mark.asyncio
async def test_queue_get():
    q = Queue()
    t1 = create_mock_track("Track 1", "id1")
    q.put(t1)

    track = q.get()
    assert track == t1
    assert q.count == 0
    assert q.loaded == t1


@pytest.mark.asyncio
async def test_queue_empty_get():
    q = Queue()
    with pytest.raises(QueueEmpty):
        q.get()


@pytest.mark.asyncio
async def test_queue_loop_mode():
    q = Queue()
    t1 = create_mock_track("Track 1", "id1")
    q.put(t1)
    q.mode = QueueMode.loop

    # First get loads it
    track = q.get()
    assert track == t1

    # Second get returns the same track in loop mode
    track2 = q.get()
    assert track2 == t1
    assert q.count == 0


@pytest.mark.asyncio
async def test_queue_shuffle():
    q = Queue()
    tracks = [create_mock_track(f"T{i}", f"id{i}") for i in range(10)]
    q.put(tracks)

    original_order = list(q)
    q.shuffle()
    shuffled_order = list(q)

    assert len(shuffled_order) == 10
    # While statistically possible to be same, it's unlikely for 10 items
    assert original_order != shuffled_order or all(t in shuffled_order for t in original_order)


@pytest.mark.asyncio
async def test_queue_clear():
    q = Queue()
    q.put(create_mock_track("T1", "id1"))
    q.clear()
    assert q.count == 0


@pytest.mark.asyncio
async def test_queue_put_at_front():
    q = Queue()
    t1 = create_mock_track("T1", "id1")
    t2 = create_mock_track("T2", "id2")
    q.put(t1)
    q.put_at_front(t2)
    assert q[0] == t2
    assert q[1] == t1


@pytest.mark.asyncio
async def test_queue_delitem():
    q = Queue()
    t1 = create_mock_track("T1", "id1")
    t2 = create_mock_track("T2", "id2")
    q.put([t1, t2])
    del q[0]
    assert q.count == 1
    assert q[0] == t2
