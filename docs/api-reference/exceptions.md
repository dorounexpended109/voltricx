---
title: Exceptions
description: API reference for all Voltricx exception classes.
---

# Exceptions



All Voltricx exceptions inherit from `VoltricxException`, making it easy to catch them all with a single `except` block.

## Exception Hierarchy

```
Exception
└── VoltricxException
    ├── NodeException
    ├── LavalinkException
    ├── LavalinkLoadException
    ├── InvalidNodeException
    ├── ChannelTimeoutException
    ├── InvalidChannelStateException
    └── QueueEmpty
```

---

## `VoltricxException`

**Base class** for all Voltricx errors.

```python
try:
    await player.play(track)
except voltricx.VoltricxException as e:
    print(f"Error: {e}")
```

Also exported as `RevvLinkException` for backwards compatibility.

---

## `NodeException`

Raised on generic node REST failures or when the session ID is missing.

```python
try:
    await node.fetch_info()
except voltricx.NodeException as e:
    print(f"HTTP {e.status}: {e}")
```

| Attribute | Type | Description |
|-----------|------|-------------|
| `e.status` | `int \| None` | HTTP status code |

---

## `LavalinkException`

Raised when the Lavalink server returns a structured error object (HTTP 4xx/5xx).

```python
try:
    data = await node.load_tracks("bad://query")
except voltricx.LavalinkException as e:
    print(f"{e.status} {e.error} at {e.path}")
```

| Attribute | Type | Description |
|-----------|------|-------------|
| `e.timestamp` | `int` | Unix millisecond timestamp |
| `e.status` | `int` | HTTP status code |
| `e.error` | `str` | Error name (e.g. `"Not Found"`) |
| `e.trace` | `str \| None` | Java stack trace (when Lavalink trace enabled) |
| `e.path` | `str` | API endpoint that failed |

---

## `LavalinkLoadException`

Raised when `Pool.fetch_tracks()` receives a `loadType: "error"` response.

```python
try:
    results = await voltricx.Pool.fetch_tracks("https://restricted.url/")
except voltricx.LavalinkLoadException as e:
    print(f"Load failed ({e.severity}): {e.message}")
    print(f"Cause: {e.cause}")
```

| Attribute | Type | Description |
|-----------|------|-------------|
| `e.message` | `str` | Human-readable error message |
| `e.severity` | `str` | `"common"`, `"suspicious"`, or `"fault"` |
| `e.cause` | `str` | Root cause description |

#### Severity Levels

| Severity | Meaning |
|----------|---------|
| `common` | Normal failures (video unavailable, geo-restricted, etc.) |
| `suspicious` | Potential bot detection or rate limiting |
| `fault` | Internal Lavalink error; may require server restart |

---

## `InvalidNodeException`

Raised when:
- A named node identifier is not found in the Pool
- No connected nodes are available

```python
try:
    node = voltricx.Pool.get_node("NonExistent")
except voltricx.InvalidNodeException as e:
    print(f"Node error: {e}")
```

---

## `ChannelTimeoutException`

Raised when connecting to a voice channel times out (default: 10 seconds).

```python
try:
    player = await channel.connect(cls=voltricx.Player)
except voltricx.ChannelTimeoutException:
    await ctx.send("❌ Connection timed out!")
```

---

## `InvalidChannelStateException`

Raised when the player attempts to connect or move without a valid channel.

```python
try:
    await player.connect(timeout=10.0, reconnect=True)
except voltricx.InvalidChannelStateException as e:
    print(f"Channel error: {e}")
```

---

## `QueueEmpty`

Raised when calling `queue.get()` or `queue.peek()` on an empty queue.

```python
from voltricx import QueueEmpty

try:
    track = player.queue.get()
except QueueEmpty:
    await ctx.send("The queue is empty!")
```

---

## Global Error Handler Pattern

```python
@bot.event
async def on_command_error(ctx, error):
    error = getattr(error, "original", error)

    if isinstance(error, voltricx.ChannelTimeoutException):
        return await ctx.send("❌ Voice channel connection timed out.")
    if isinstance(error, voltricx.InvalidNodeException):
        return await ctx.send("❌ No Lavalink nodes available.")
    if isinstance(error, voltricx.LavalinkLoadException):
        return await ctx.send(f"❌ Could not load: `{error.message}`")
    if isinstance(error, voltricx.QueueEmpty):
        return await ctx.send("❌ The queue is empty.")
    if isinstance(error, voltricx.VoltricxException):
        return await ctx.send(f"❌ Music error: {error}")
    raise error
```
