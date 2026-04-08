---
title: Type Definitions
description: Pydantic models and type definitions used across Voltricx.
---

# Type Definitions



Voltricx uses [Pydantic v2](https://docs.pydantic.dev/latest/) for all data models, providing automatic validation, serialisation, and IDE autocompletion.

---

## Node Types (`voltricx.typings.node`)

### `NodeConfig`

Configuration model for a Lavalink node.

```python
config = voltricx.NodeConfig(
    identifier="Main",
    uri="http://localhost:2333",
    password="youshallnotpass",
    region="us",
    heartbeat=15.0,
    resume_timeout=60,
)
```

| Field | Type | Default |
|-------|------|---------|
| `identifier` | `str` | required |
| `uri` | `str` | required |
| `password` | `str` | required |
| `region` | `str \| None` | `"global"` |
| `heartbeat` | `float` | `15.0` |
| `retries` | `int \| None` | `None` |
| `resume_timeout` | `int` | `60` |
| `inactive_player_timeout` | `int \| None` | `300` |
| `inactive_channel_tokens` | `int \| None` | `3` |

---

### `NodeInfo`

```python
info = await node.fetch_info()
info.version.semver       # "4.0.8"
info.source_managers      # ["youtube", "soundcloud", ...]
info.filters              # ["equalizer", "timescale", ...]
info.plugins              # [Plugin(name="...", version="...")]
info.git.branch           # "main"
```

---

### `MemoryStats`

```python
mem = node.stats_memory
mem.free        # bytes
mem.used        # bytes
mem.allocated   # bytes
mem.reservable  # bytes
```

---

### `CPUStats`

```python
cpu = node.stats_cpu
cpu.cores          # int
cpu.system_load    # float (0.0–1.0)
cpu.lavalink_load  # float (0.0–1.0)
```

---

### `FrameStats`

```python
frames = node.stats_frames
frames.sent     # frames sent per minute
frames.nulled   # nulled frames per minute
frames.deficit  # frame deficit per minute
```

---

### `ErrorResponse`

Internal model for Lavalink error payloads.

| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | `int` | Unix millisecond timestamp |
| `status` | `int` | HTTP status code |
| `error` | `str` | Error type string |
| `trace` | `str \| None` | Java stack trace |
| `message` | `str` | Human-readable message |
| `path` | `str` | API path |

---

## Track Types (`voltricx.typings.track`)

### `TrackInfo`

Frozen model embedded in `Playable.info`.

| Field | Type |
|-------|------|
| `identifier` | `str` |
| `is_seekable` | `bool` |
| `author` | `str` |
| `length` | `int` (ms) |
| `is_stream` | `bool` |
| `position` | `int` (ms) |
| `title` | `str` |
| `uri` | `str \| None` |
| `artwork_url` | `str \| None` |
| `isrc` | `str \| None` |
| `source_name` | `str` |

---

## Common Types (`voltricx.typings.common`)

### `HyperCacheConfig`

```python
from voltricx.typings.common import HyperCacheConfig

config = HyperCacheConfig(
    capacity=100,
    track_capacity=1000,
    decay_factor=0.5,
    decay_threshold=1000,
)
```

### `TrackException`

```python
exception.message   # str
exception.severity  # Severity enum
exception.cause     # str
```

---

## Event Types (`voltricx.typings.events`)

### `TrackStartEvent`

```python
event.op        # "event"
event.type      # EventType.track_start
event.guild_id  # str
event.track     # Playable
```

### `TrackEndEvent`

```python
event.op        # "event"
event.type      # EventType.track_end
event.guild_id  # str
event.track     # Playable
event.reason    # TrackEndReason
```

### `TrackExceptionEvent`

```python
event.track     # Playable
event.exception # TrackException
```

### `TrackStuckEvent`

```python
event.track          # Playable
event.threshold_ms   # int
```

### `WebSocketClosedEvent`

```python
event.code      # int
event.reason    # str
event.by_remote # bool
```

---

## RoutePlanner Types (`voltricx.typings.routeplanner`)

### `RoutePlannerStatus`

```python
status = await node.fetch_routeplanner_status()
if status:
    status.cls           # RoutePlannerClass enum
    status.details       # implementation details
    status.failing_addresses  # list of failed IPs
```
