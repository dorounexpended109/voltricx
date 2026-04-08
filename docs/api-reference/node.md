---
title: Node
description: API reference for the Voltricx Node class.
---

# `Node`



`Node` represents a single connection to a Lavalink server. It wraps both the REST API and WebSocket connection.

You normally don't create `Node` instances directly — use `Pool.connect()` instead.

---

## Constructor

```python
node = voltricx.Node(
    config=voltricx.NodeConfig(...),
    client=bot,
    session=None,   # Optional aiohttp.ClientSession
)
```

---

## Properties

| Property | Type | Description |
|----------|------|-------------|
| `node.identifier` | `str` | Unique node name from `NodeConfig` |
| `node.uri` | `str` | Base HTTP URI |
| `node.status` | `NodeStatus` | Current connection status |
| `node.config` | `NodeConfig` | The configuration this node was created with |
| `node.players` | `dict[int, Player]` | Snapshot of guild_id → Player mappings |
| `node.penalty` | `float` | Load penalty score (lower = healthier) |
| `node.session_id` | `str \| None` | Active Lavalink session ID |
| `node.info` | `NodeInfo \| None` | Server info (after fetch_info()) |
| `node.stats_memory` | `MemoryStats \| None` | Memory stats from last stats event |
| `node.stats_cpu` | `CPUStats \| None` | CPU stats from last stats event |
| `node.stats_frames` | `FrameStats \| None` | Frame stats from last stats event |
| `node.playing_count` | `int` | Number of actively playing players |

---

## Connection Methods

### `node.connect()`

Initiate the WebSocket connection.

```python
await node.connect()
await node.connect(silent=True)  # Suppress error output
```

---

### `node.disconnect()`

Close the connection and optionally destroy all players.

```python
await node.disconnect()
await node.disconnect(force=True)  # Also destroy all players
```

---

## REST Methods

### `node.fetch_info()`

Fetch and cache detailed server information.

```python
info = await node.fetch_info()
print(info.version.semver)        # "4.0.8"
print(info.source_managers)       # ["youtube", "soundcloud", ...]
print(info.filters)               # ["equalizer", "timescale", ...]
```

**Returns:** `NodeInfo`

---

### `node.fetch_stats()`

Fetch raw stats from the Lavalink server.

```python
stats = await node.fetch_stats()
```

**Returns:** `dict[str, Any]`

---

### `node.fetch_version()`

Fetch the Lavalink server version string.

```python
version = await node.fetch_version()
print(version)  # "4.0.8"
```

**Returns:** `str`

---

### `node.update_session()`

Update the session's resume configuration.

```python
await node.update_session(resuming=True, timeout=60)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `resuming` | `bool` | `True` | Enable session resuming |
| `timeout` | `int` | `60` | How long Lavalink holds state for resuming (seconds) |

---

### `node.load_tracks()`

Fetch raw track data from Lavalink.

```python
data = await node.load_tracks("dzsearch:Bohemian Rhapsody")
```

**Returns:** `Any` (raw Lavalink response)

---

### `node.decode_track()`

Decode a base64-encoded track string into a `Playable`.

```python
track = await node.decode_track("QAAAjQIAJ...")
```

**Returns:** `Playable`

---

### `node.decode_tracks()`

Decode a list of encoded track strings.

```python
tracks = await node.decode_tracks(["QAAAjQIAJ...", "QAAAdQIAA..."])
```

**Returns:** `list[Playable]`

---

## RoutePlanner Methods

### `node.fetch_routeplanner_status()`

Fetch current RoutePlanner status.

```python
status = await node.fetch_routeplanner_status()
if status:
    print(f"RoutePlanner type: {status.cls}")
```

**Returns:** `RoutePlannerStatus | None`

---

### `node.free_address()`

Unmark a specific IP address as failing.

```python
await node.free_address("203.0.113.1")
```

---

### `node.free_all_addresses()`

Reset all failing RoutePlanner addresses.

```python
await node.free_all_addresses()
```

---

## Player Methods

### `node.get_player()`

Retrieve a player by guild ID (returns `None` if not found).

```python
player = node.get_player(guild_id)
```

---

### `node.fetch_player()`

Fetch a player's state directly from Lavalink.

```python
state = await node.fetch_player(guild_id)
```

**Returns:** `dict[str, Any] | None`

---

### `node.fetch_players()`

Fetch all players on this node from Lavalink.

```python
all_players = await node.fetch_players()
```

**Returns:** `list[dict[str, Any]]`
