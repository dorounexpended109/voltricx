---
title: Pool
description: API reference for the Pool class — the central node manager.
---

# `Pool`



The `Pool` is a **class-level singleton** that manages all Lavalink node connections, load balancing, failover, and the global HyperCache.

```python
import voltricx

await voltricx.Pool.connect(client=bot, nodes=[config])
```

All methods are `@classmethod` — you never instantiate Pool directly.

---

## Methods

### `Pool.connect()`

Connect to one or more Lavalink nodes and initialise global systems.

```python
nodes = await voltricx.Pool.connect(
    client=bot,
    nodes=[voltricx.NodeConfig(...)],
    cache_config={"capacity": 100, "track_capacity": 1000},
    regions=None,
    default_search_source="dzsearch",
)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `client` | `discord.Client` | Your bot/client instance |
| `nodes` | `Iterable[NodeConfig]` | Node configurations to connect |
| `cache_config` | `dict \| HyperCacheConfig \| None` | HyperCache configuration. `None` disables caching |
| `regions` | `dict[str, list[str]] \| None` | Override the built-in region map |
| `default_search_source` | `str \| None` | Default search prefix (e.g. `"ytsearch"`, `"dzsearch"`) |

**Returns:** `dict[str, Node]` — a snapshot of all registered nodes.

---

### `Pool.get_node()`

Retrieve a node by identifier or select the healthiest one automatically.

```python
# Auto-select: lowest penalty score
node = voltricx.Pool.get_node()

# By identifier
node = voltricx.Pool.get_node("EU")

# Region-aware selection
node = voltricx.Pool.get_node(region="us")
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `identifier` | `str \| None` | Node identifier. `None` = auto-select |
| `region` | `str \| None` | Prefer nodes in this region |

**Returns:** `Node`

**Raises:** `InvalidNodeException` — if no connected nodes are available.

---

### `Pool.fetch_tracks()`

Search for tracks or resolve a URL. Results are automatically cached.

```python
results = await voltricx.Pool.fetch_tracks("Bohemian Rhapsody")
results = await voltricx.Pool.fetch_tracks("dzsearch:Bohemian Rhapsody")
results = await voltricx.Pool.fetch_tracks("https://youtube.com/watch?v=...")
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `query` | `str` | Search query or URL |
| `region` | `str \| None` | Prefer nodes from this region |
| `node` | `Node \| None` | Use a specific node instead of auto-selecting |

**Returns:** `list[Playable] | Playlist`

**Raises:** `InvalidNodeException`, `LavalinkLoadException`

!!! tip "Search Sources"
    Common source prefixes: `ytsearch` (YouTube), `dzsearch` (Deezer), `scsearch` (SoundCloud), `spsearch` (Spotify).

---

### `Pool.nodes()`

Return a snapshot of all registered nodes.

```python
all_nodes = voltricx.Pool.nodes()
# → {"Main": <Node ...>, "EU": <Node ...>}
```

**Returns:** `dict[str, Node]`

---

### `Pool.region_from_endpoint()`

Map a Discord voice endpoint string to a region name.

```python
region = voltricx.Pool.region_from_endpoint("us-east1-b.discord.media:443")
# → "us"
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `endpoint` | `str \| None` | Discord voice endpoint |

**Returns:** `str` — region name or `"global"`

---

### `Pool.get_cache_stats()`

Return current HyperCache hit counts.

```python
stats = voltricx.Pool.get_cache_stats()
# → {"l1_queries": 42, "l2_tracks": 318}
```

**Returns:** `dict[str, int]`

---

### `Pool.get_cache_entries()`

Return a mapping of cached queries to their track titles.

```python
entries = voltricx.Pool.get_cache_entries()
for query, titles in entries.items():
    print(f"{query}: {titles}")
```

**Returns:** `dict[str, list[str]]`

---

### `Pool.get_random_cached_track()`

Retrieve a random track from the HyperCache L2 (Track Registry).

```python
track = voltricx.Pool.get_random_cached_track()
if track:
    await player.play(track)
```

**Returns:** `Playable | None`

---

### `Pool.export_cache_data()`

Export the full HyperCache state for debugging or persistence.

```python
data = voltricx.Pool.export_cache_data()
# → {"l1": {...}, "l2": {...}}
```

**Returns:** `dict[str, Any]`

---

### `Pool.close()`

Disconnect all nodes and shut down the Pool cleanly.

```python
await voltricx.Pool.close()
```

Always call this in your bot's `close()` method.
