---
title: Events Reference
description: Complete reference for all Voltricx events.
---

# Events Reference



All events are dispatched via `discord.Client.dispatch()` and listened to with `@bot.event` or `@commands.Cog.listener()`.

---

## Quick Reference

| Event | Arguments | When |
|-------|-----------|------|
| `on_voltricx_node_ready` | `node` | Node WebSocket connected |
| `on_voltricx_node_disconnected` | `node` | Node WebSocket disconnected |
| `on_voltricx_failover` | `old_node, new_node, players` | Node failed, players migrated |
| `on_voltricx_track_start` | `player, track` | Track began playing |
| `on_voltricx_track_end` | `player, track, reason` | Track stopped |
| `on_voltricx_track_exception` | `player, track, exception` | Track raised an error |
| `on_voltricx_track_stuck` | `player, track, threshold` | Track stalled |
| `on_voltricx_websocket_closed` | `player, code, reason, by_remote` | Discord voice WS closed |
| `on_voltricx_inactive_player` | `player` | Idle timeout triggered |
| `on_voltricx_inactive_channel` | `player` | Empty channel tokens exhausted |

---

## Node Events

### `on_voltricx_node_ready`

```python
@bot.event
async def on_voltricx_node_ready(node: voltricx.Node) -> None:
    ...
```

Fired when a Lavalink node connects and its `ready` payload is received.

---

### `on_voltricx_node_disconnected`

```python
@bot.event
async def on_voltricx_node_disconnected(node: voltricx.Node) -> None:
    ...
```

Fired when a node loses its WebSocket connection.

---

### `on_voltricx_failover`

```python
@bot.event
async def on_voltricx_failover(
    old_node: voltricx.Node,
    new_node: voltricx.Node,
    players: list[voltricx.Player],
) -> None:
    ...
```

Fired when players are automatically migrated after a node failure.

---

## Track Events

### `on_voltricx_track_start`

```python
@bot.event
async def on_voltricx_track_start(
    player: voltricx.Player,
    track: voltricx.Playable,
) -> None:
    ...
```

---

### `on_voltricx_track_end`

```python
@bot.event
async def on_voltricx_track_end(
    player: voltricx.Player,
    track: voltricx.Playable,
    reason: voltricx.TrackEndReason,
) -> None:
    ...
```

---

### `on_voltricx_track_exception`

```python
@bot.event
async def on_voltricx_track_exception(
    player: voltricx.Player,
    track: voltricx.Playable,
    exception: Any,
) -> None:
    ...
```

---

### `on_voltricx_track_stuck`

```python
@bot.event
async def on_voltricx_track_stuck(
    player: voltricx.Player,
    track: voltricx.Playable,
    threshold: int,
) -> None:
    ...
```

`threshold` is the milliseconds after which Lavalink gives up and reports the track as stuck.

---

## Player Events

### `on_voltricx_websocket_closed`

```python
@bot.event
async def on_voltricx_websocket_closed(
    player: voltricx.Player,
    code: int,
    reason: str,
    by_remote: bool,
) -> None:
    ...
```

Fired when the Discord voice WebSocket is closed (separate from Lavalink's WS).

Common close codes:

| Code | Meaning |
|------|---------|
| 4006 | Session no longer valid |
| 4009 | Session timed out |
| 4011 | Server not found |
| 4014 | Disconnected (kicked, channel deleted, etc.) |
| 4016 | Unknown encryption mode |

---

### `on_voltricx_inactive_player`

```python
@bot.event
async def on_voltricx_inactive_player(player: voltricx.Player) -> None:
    await player.disconnect()
```

Fired when the player's `inactive_timeout` elapses with no active track.

---

### `on_voltricx_inactive_channel`

```python
@bot.event
async def on_voltricx_inactive_player(player: voltricx.Player) -> None:
    # Also covers empty-channel case
    await player.disconnect()
```

Fired when the voice channel has been empty for the configured number of track-end events (`NodeConfig.inactive_channel_tokens`).
