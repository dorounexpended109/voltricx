---
title: Queue
description: API reference for the Voltricx Queue class.
---

# `Queue`



`Queue` is a feature-rich, deque-backed track queue with support for loop modes, async waiting, history tracking, and direct index operations.

```python
queue = player.queue        # Main queue
history = player.queue.history  # History sub-queue
auto_q  = player.auto_queue     # Recommendations queue
```

---

## Constructor

```python
Queue(*, history: bool = True)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `history` | `bool` | `True` | Whether to create a history sub-queue |

---

## Properties

| Property | Type | Description |
|----------|------|-------------|
| `queue.mode` | `QueueMode` | Current playback mode |
| `queue.count` | `int` | Number of tracks in queue |
| `queue.is_empty` | `bool` | `True` if no tracks queued |
| `queue.loaded` | `Playable \| None` | Last track retrieved via `get()` |
| `queue.history` | `Queue \| None` | History sub-queue |

---

## Getting Tracks

### `queue.get()`

Remove and return the next track, respecting the current mode.

```python
track = queue.get()
```

**Raises:** `QueueEmpty` if the queue is empty and mode doesn't allow refilling.

---

### `queue.get_at()`

Remove and return the track at a specific index.

```python
track = queue.get_at(2)  # 0-based
```

---

### `queue.get_wait()`

Async: wait until a track is available, then return it.

```python
track = await queue.get_wait()
```

---

### `queue.peek()`

View a track without removing it.

```python
next_track = queue.peek(0)    # First track
later_track = queue.peek(5)   # Sixth track
```

**Raises:** `QueueEmpty` if empty.

---

### `queue.pop()`

Remove and return the **last** track (right side of deque).

```python
last_track = queue.pop()
```

---

## Adding Tracks

### `queue.put()`

Add one track, a playlist, or an iterable of tracks.

```python
count = queue.put(track)
count = queue.put(playlist)
count = queue.put([t1, t2, t3])
count = queue.put(track, atomic=False)  # Skip invalid items silently
```

**Returns:** `int` — number of tracks added.

---

### `queue.put_wait()`

Thread-safe async version of `put()`.

```python
count = await queue.put_wait(tracks)
```

---

### `queue.put_at()`

Insert a track at a specific index.

```python
queue.put_at(0, track)   # Insert at front
queue.put_at(3, track)   # Insert at index 3
```

---

### `queue.put_at_front()`

Shortcut to insert at the very front (next to play).

```python
queue.put_at_front(priority_track)
```

---

## Modifying the Queue

### `queue.remove()`

Remove occurrences of a track.

```python
removed = queue.remove(track)             # Remove first occurrence
removed = queue.remove(track, count=2)    # Remove up to 2
removed = queue.remove(track, count=None) # Remove all
```

**Returns:** `int` — number of tracks removed.

---

### `queue.delete()`

Remove the track at a specific index.

```python
queue.delete(2)  # Remove index 2
```

---

### `queue.swap()`

Swap two tracks by index.

```python
queue.swap(0, 4)  # Swap first and fifth track
```

---

### `queue.shuffle()`

Randomly shuffle all queued tracks.

```python
queue.shuffle()
```

---

### `queue.index()`

Find the index of a track.

```python
pos = queue.index(track)
```

---

### `queue.clear()`

Remove all tracks from the queue.

```python
queue.clear()
```

---

### `queue.reset()`

Full reset — clears tracks, history, mode, and cancels all waiters.

```python
queue.reset()
```

---

## Indexing & Iteration

```python
# Index
track = queue[0]
track = queue[-1]

# Slice
first_ten = queue[0:10]

# Set
queue[0] = different_track

# Delete
del queue[2]

# Iterate
for track in queue:
    print(track.title)

# Reversed
for track in reversed(queue):
    print(track.title)

# Length
print(len(queue))

# Boolean
if queue:
    print("Has tracks")
```

---

## Queue Modes

```python
from voltricx import QueueMode

queue.mode = QueueMode.normal    # Play through and stop
queue.mode = QueueMode.loop      # Loop the current track
queue.mode = QueueMode.loop_all  # Loop the full queue
```

When `loop_all` is active and the queue empties, `get()` automatically refills it from history.
