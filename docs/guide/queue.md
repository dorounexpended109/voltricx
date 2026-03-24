---
title: Queue Management
description: Using the Voltricx Queue — adding tracks, modes, shuffling, history, and async operations.
---

# Queue Management

Every `Player` has a `queue` property which is an instance of `voltricx.Queue`. The queue is backed by a `collections.deque` and supports indexing, slicing, iteration, and async waiting.

```python
player: voltricx.Player = ctx.voice_client
queue = player.queue
```

---

## Adding Tracks

```python
from voltricx import Playable, Playlist, Queue

# Add a single track
queue.put(track)

# Add a playlist (all its tracks)
queue.put(playlist)

# Add an iterable of tracks
queue.put([track1, track2, track3])

# Add to the front (play next)
queue.put_at_front(track)

# Add at a specific index
queue.put_at(2, track)
```

### Async put (thread-safe)

```python
added = await queue.put_wait(tracks)
```

---

## Retrieving Tracks

```python
# Get and remove the next track (respects loop mode)
track = queue.get()

# Wait until a track is available, then get it
track = await queue.get_wait()

# Peek without removing
track = queue.peek(0)   # First item
```

`queue.get()` respects the current `QueueMode`:

- **`normal`** — gets and removes the next track
- **`loop`** — re-returns the currently loaded track (`queue.loaded`)
- **`loop_all`** — when the queue empties, refills it from history

---

## Queue Modes

```python
from voltricx import QueueMode

queue.mode = QueueMode.normal    # Default — play through and stop
queue.mode = QueueMode.loop      # Repeat the current track
queue.mode = QueueMode.loop_all  # Repeat the entire queue
```

---

## Queue Properties

| Property | Type | Description |
|----------|------|-------------|
| `queue.mode` | `QueueMode` | Current playback mode |
| `queue.count` | `int` | Number of queued tracks |
| `queue.is_empty` | `bool` | `True` if no tracks queued |
| `queue.loaded` | `Playable \| None` | The last track retrieved via `get()` |
| `queue.history` | `Queue \| None` | The track history sub-queue |

---

## Indexing and Slicing

Queue supports standard Python list operations:

```python
# Get by index (0-based)
first_track = queue[0]
last_track  = queue[-1]

# Slice
next_five = queue[0:5]

# Set by index
queue[0] = different_track

# Delete by index
del queue[2]
```

---

## Manipulation

```python
# Shuffle all queued tracks randomly
queue.shuffle()

# Remove a specific track
removed = queue.remove(track)                # Removes first occurrence
removed = queue.remove(track, count=None)    # Removes all occurrences

# Remove by index
queue.delete(3)

# Swap two positions
queue.swap(0, 3)   # Swap index 0 and index 3

# Find position of a track
idx = queue.index(track)

# Pop from the back
track = queue.pop()
```

---

## Clearing and Resetting

```python
queue.clear()   # Remove all queued tracks (keeps history and mode)
queue.reset()   # Full reset: clears tracks, history, mode, waiters
```

---

## History

The `queue.history` is itself a `Queue` (without its own history). Tracks are added to history automatically when played.

```python
# Show last 10 played tracks (most recent first)
history = list(reversed(player.queue.history))[:10]
for track in history:
    print(track.title)

# Play a previous track
try:
    player.queue.history.pop()   # Remove "current" from history
    prev = player.queue.history.pop()  # Get the previous one
    player.queue.put_at_front(prev)
    await player.skip(force=True)
except Exception:
    await ctx.send("No previous track in history.")
```

---

## Auto Queue (Recommendations)

`player.auto_queue` is a separate `Queue` populated by the AutoPlay engine. You can inspect it:

```python
for track in player.auto_queue:
    print(f"  Recommended: {track.title}")
```

---

## Iteration

```python
for track in player.queue:
    print(track.title)

# Reversed
for track in reversed(player.queue):
    print(track.title)

# Length
print(f"Queue has {len(player.queue)} tracks")

# Boolean check
if player.queue:
    print("Queue has items")
```

---

## Full Queue Command Example

```python
@bot.command(name="queue", aliases=["q"])
async def queue_cmd(ctx: commands.Context, page: int = 1):
    player: voltricx.Player = ctx.voice_client
    if not player or not player.queue:
        return await ctx.send("The queue is empty.")

    per_page = 10
    total    = len(player.queue)
    pages    = (total + per_page - 1) // per_page
    page     = max(1, min(page, pages))

    start = (page - 1) * per_page
    tracks = player.queue[start : start + per_page]

    lines = [f"`{start + i + 1}.` {t.title} — {t.author}" for i, t in enumerate(tracks)]
    now = player.current

    embed = discord.Embed(
        title="📋 Queue",
        description="\n".join(lines),
        color=0x7c3aed,
    )
    embed.set_footer(text=f"Page {page}/{pages} • {total} tracks • Mode: {player.queue.mode.value}")
    if now:
        embed.set_author(name=f"▶ Now: {now.title}", icon_url=now.artwork)

    await ctx.send(embed=embed)
```
