---
title: Enums
description: API reference for all Voltricx enumerations.
---

# Enums



All enums in Voltricx inherit from both `str` and `Enum`, meaning you can compare them directly against strings.

```python
from voltricx import QueueMode, AutoPlayMode, NodeStatus
```

---

## `QueueMode`

Controls how the Queue behaves when `get()` is called.

| Member | Value | Description |
|--------|-------|-------------|
| `QueueMode.normal` | `"normal"` | Play through tracks sequentially |
| `QueueMode.loop` | `"loop"` | Repeat the current track indefinitely |
| `QueueMode.loop_all` | `"loop_all"` | Loop the entire queue; refill from history when empty |

```python
player.queue.mode = voltricx.QueueMode.loop
player.queue.mode = voltricx.QueueMode.loop_all
player.queue.mode = voltricx.QueueMode.normal
```

---

## `AutoPlayMode`

Controls the AutoPlay recommendation engine.

| Member | Value | Description |
|--------|-------|-------------|
| `AutoPlayMode.enabled` | `"enabled"` | Actively fetch recommendations when queue empties |
| `AutoPlayMode.partial` | `"partial"` | Play through queue; no auto-recommendations |
| `AutoPlayMode.disabled` | `"disabled"` | Stop completely when queue is empty |

```python
player.autoplay = voltricx.AutoPlayMode.enabled
```

---

## `NodeStatus`

Represents the connection state of a `Node`.

| Member | Value | Description |
|--------|-------|-------------|
| `NodeStatus.connected` | `"connected"` | Node is online |
| `NodeStatus.connecting` | `"connecting"` | Handshake in progress |
| `NodeStatus.disconnected` | `"disconnected"` | Node is offline |

```python
if node.status == voltricx.NodeStatus.connected:
    print("Node is healthy!")
```

---

## `TrackEndReason`

Indicates why a track stopped playing. Received in the `on_voltricx_track_end` event.

| Member | Value | Description |
|--------|-------|-------------|
| `TrackEndReason.finished` | `"finished"` | Track played to natural end |
| `TrackEndReason.load_failed` | `"loadFailed"` | Track failed to load |
| `TrackEndReason.stopped` | `"stopped"` | Manually stopped |
| `TrackEndReason.replaced` | `"replaced"` | A new track replaced this one |
| `TrackEndReason.cleanup` | `"cleanup"` | Player cleanup |

---

## `LoadType`

Lavalink response load type. Used internally by `Pool.fetch_tracks()`.

| Member | Value | Description |
|--------|-------|-------------|
| `LoadType.track` | `"track"` | Single track loaded |
| `LoadType.playlist` | `"playlist"` | Playlist loaded |
| `LoadType.search` | `"search"` | Search results |
| `LoadType.empty` | `"empty"` | No results |
| `LoadType.error` | `"error"` | Load error |

---

## `EventType`

Lavalink WebSocket event types. Used internally.

| Member | Value |
|--------|-------|
| `EventType.track_start` | `"TrackStartEvent"` |
| `EventType.track_end` | `"TrackEndEvent"` |
| `EventType.track_exception` | `"TrackExceptionEvent"` |
| `EventType.track_stuck` | `"TrackStuckEvent"` |
| `EventType.websocket_closed` | `"WebSocketClosedEvent"` |

---

## `OpCode`

Lavalink WebSocket op codes. Used internally.

| Member | Value |
|--------|-------|
| `OpCode.ready` | `"ready"` |
| `OpCode.player_update` | `"playerUpdate"` |
| `OpCode.stats` | `"stats"` |
| `OpCode.event` | `"event"` |
| `OpCode.dave` | `"dave"` |

---

## `Severity`

Track load error severity levels.

| Member | Value |
|--------|-------|
| `Severity.common` | `"common"` |
| `Severity.suspicious` | `"suspicious"` |
| `Severity.fault` | `"fault"` |

---

## `RoutePlannerClass`

RoutePlanner implementation types.

| Member | Value |
|--------|-------|
| `RoutePlannerClass.rotating_ip` | `"RotatingIpRoutePlanner"` |
| `RoutePlannerClass.nano_ip` | `"NanoIpRoutePlanner"` |
| `RoutePlannerClass.rotating_nano_ip` | `"RotatingNanoIpRoutePlanner"` |
| `RoutePlannerClass.balancing_ip` | `"BalancingIpRoutePlanner"` |
