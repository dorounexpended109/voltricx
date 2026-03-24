---
title: Error Handling
description: Understanding and handling Voltricx exceptions.
---

# Error Handling

Voltricx uses a clear exception hierarchy rooted at `VoltricxException`. All errors can be caught with a single broad `except voltricx.VoltricxException` block, or handled individually for fine-grained control.

## Exception Hierarchy

```
VoltricxException (base)
├── NodeException             # Generic node/REST errors
├── LavalinkException         # Lavalink API error responses
├── LavalinkLoadException     # Track loading failures
├── InvalidNodeException      # Node not found / no nodes available
├── ChannelTimeoutException   # Voice connect timeout
├── InvalidChannelStateException # Invalid channel on connect
└── QueueEmpty                # Tried to get() from empty queue
```

---

## VoltricxException

The base exception. Catch this to handle **all** Voltricx errors at once.

```python
try:
    await player.play(track)
except voltricx.VoltricxException as e:
    await ctx.send(f"An error occurred: {e}")
```

---

## NodeException

Raised on generic REST failures or when the session ID is missing.

```python
try:
    await node.fetch_info()
except voltricx.NodeException as e:
    print(f"Node error (HTTP {e.status}): {e}")
```

| Attribute | Type | Description |
|-----------|------|-------------|
| `e.status` | `int \| None` | HTTP status code if applicable |

---

## LavalinkException

Raised when the Lavalink server returns a structured error response (HTTP 4xx/5xx).

```python
try:
    data = await node.load_tracks("invalid://query")
except voltricx.LavalinkException as e:
    print(f"Lavalink error {e.status}: {e.error}")
    print(f"Path: {e.path}")
```

| Attribute | Type | Description |
|-----------|------|-------------|
| `e.timestamp` | `int` | Unix timestamp of the error |
| `e.status` | `int` | HTTP status code |
| `e.error` | `str` | Error type (e.g. `"Not Found"`) |
| `e.trace` | `str \| None` | Stack trace from Lavalink (debug mode) |
| `e.path` | `str` | API path that failed |

---

## LavalinkLoadException

Raised when Lavalink's `loadType` is `"error"` (track could not be loaded).

```python
try:
    results = await voltricx.Pool.fetch_tracks("https://bad.url/track")
except voltricx.LavalinkLoadException as e:
    print(f"Load failed: {e.message} (Severity: {e.severity})")
```

| Attribute | Type | Description |
|-----------|------|-------------|
| `e.message` | `str` | Human-readable error message |
| `e.severity` | `str` | `"common"`, `"suspicious"`, or `"fault"` |
| `e.cause` | `str` | Root cause string |

---

## InvalidNodeException

Raised when requesting a node that doesn't exist, or when the Pool has no connected nodes.

```python
try:
    node = voltricx.Pool.get_node("NonExistent")
except voltricx.InvalidNodeException as e:
    print(f"Node error: {e}")
```

---

## ChannelTimeoutException

Raised when connecting to a voice channel times out (default: 10 seconds).

```python
try:
    player = await channel.connect(cls=voltricx.Player)
except voltricx.ChannelTimeoutException:
    await ctx.send("❌ Connection timed out. Is the bot in a restricted channel?")
```

---

## InvalidChannelStateException

Raised when the player tries to connect without a valid channel set.

```python
try:
    await player.connect(timeout=10.0, reconnect=True)
except voltricx.InvalidChannelStateException as e:
    print(f"Channel state error: {e}")
```

---

## QueueEmpty

Raised when calling `queue.get()` on an empty queue.

```python
from voltricx import QueueEmpty

try:
    track = player.queue.get()
except QueueEmpty:
    await ctx.send("The queue is empty!")
```

---

## Global Error Handler

A recommended pattern using discord.py's command error handler:

```python
@bot.event
async def on_command_error(ctx: commands.Context, error: Exception):
    # Unwrap CommandInvokeError
    error = getattr(error, "original", error)

    if isinstance(error, voltricx.ChannelTimeoutException):
        await ctx.send("❌ Voice channel connection timed out.")
    elif isinstance(error, voltricx.InvalidNodeException):
        await ctx.send("❌ No Lavalink nodes are available right now.")
    elif isinstance(error, voltricx.LavalinkLoadException):
        await ctx.send(f"❌ Could not load track: `{error.message}`")
    elif isinstance(error, voltricx.QueueEmpty):
        await ctx.send("❌ The queue is empty.")
    elif isinstance(error, voltricx.VoltricxException):
        await ctx.send(f"❌ Music error: {error}")
    elif isinstance(error, commands.CheckFailure):
        await ctx.send(f"❌ {error}")
    else:
        raise error
```
