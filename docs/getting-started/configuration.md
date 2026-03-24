---
title: Configuration
description: Full reference for NodeConfig, Pool.connect(), and HyperCache settings.
---

# Configuration

## NodeConfig

`NodeConfig` is a Pydantic model that holds the connection parameters for a single Lavalink node.

```python
import voltricx

config = voltricx.NodeConfig(
    identifier="Main",
    uri="http://localhost:2333",
    password="youshallnotpass",
    region="us",
    heartbeat=15.0,
    retries=None,
    resume_timeout=60,
    inactive_player_timeout=300,
    inactive_channel_tokens=3,
)
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `identifier` | `str` | — | Unique name for this node (e.g. `"Main"`, `"EU-1"`) |
| `uri` | `str` | — | HTTP base URI of the Lavalink server (e.g. `"http://localhost:2333"`) |
| `password` | `str` | — | Lavalink server password |
| `region` | `str \| None` | `"global"` | Geographic region for smart routing. See [region list](#regions) |
| `heartbeat` | `float` | `15.0` | WebSocket heartbeat interval in seconds |
| `retries` | `int \| None` | `None` | Max reconnection attempts. `None` = unlimited |
| `resume_timeout` | `int` | `60` | Seconds Lavalink holds state for a resumable session |
| `inactive_player_timeout` | `int \| None` | `300` | Seconds before an idle player auto-disconnects (`None` to disable) |
| `inactive_channel_tokens` | `int \| None` | `3` | Track-end events allowed while channel is empty before disconnect |

---

## Pool.connect()

`Pool.connect()` initialises the entire node system. Call it once in `setup_hook`.

```python
await voltricx.Pool.connect(
    client=bot,
    nodes=[config1, config2],
    cache_config={
        "capacity": 100,
        "track_capacity": 1000,
        "decay_factor": 0.5,
        "decay_threshold": 1000,
    },
    regions=None,           # Override the built-in region map
    default_search_source="dzsearch",
)
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `client` | `discord.Client` | — | Your bot instance |
| `nodes` | `Iterable[NodeConfig]` | — | One or more node configs to connect |
| `cache_config` | `dict \| HyperCacheConfig \| None` | `None` | HyperCache settings. `None` disables caching |
| `regions` | `dict[str, list[str]] \| None` | `None` | Custom region map (replaces built-in) |
| `default_search_source` | `str \| None` | `None` | Prefix added to plain-text queries (e.g. `"ytsearch"`) |

---

## HyperCache Config

HyperCache uses a dual-tier design (L1 LRU query cache + L2 LFU track registry) to minimise redundant API calls.

```python
cache_config = {
    "capacity": 100,          # Max cached queries in L1 (LRU)
    "track_capacity": 1000,   # Max cached tracks in L2 (LFU)
    "decay_factor": 0.5,      # Frequency decay multiplier (0–1)
    "decay_threshold": 1000,  # Total hits before decay is applied
}
```

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `capacity` | `int` | `100` | Max number of unique queries stored in L1 |
| `track_capacity` | `int` | `1000` | Max tracks stored in L2 |
| `decay_factor` | `float` | `0.5` | On decay event, each track's hit count is multiplied by this value. Lower = faster decay |
| `decay_threshold` | `int` | `1000` | Total cache hits before a decay pass runs |

!!! tip "Tuning the cache"
    For bots serving many unique queries, increase `capacity` and `track_capacity`.
    Set `decay_factor` closer to `1.0` to make popular tracks stay cached longer.

---

## Regions

Voltricx maps Discord's voice endpoint hostnames to these region keys for proximity-based node selection:

| Region Key | Covered Endpoints |
|-----------|------------------|
| `asia` | `bom`, `maa`, `nrt`, `hnd`, `sin`, `kul`, `bkk`, `hkg`, `tpe`, `syd`, `mel`, `akl` |
| `eu` | `ams`, `fra`, `ber`, `lhr`, `cdg`, `mad`, `waw`, `mil`, `arn`, `hel`, `osl`, `cph` |
| `us` | `iad`, `atl`, `mia`, `bos`, `jfk`, `ord`, `dfw`, `lax`, `sea`, `sjc` |
| `southamerica` | `gru`, `scl`, `eze`, `lim`, `bog` |
| `africa` | `jnb`, `cpt`, `nbo` |
| `middleeast` | `dxb`, `auh`, `ruh`, `tel` |
| `global` | Fallback for any unrecognised endpoint |

### Custom Region Map

```python
await voltricx.Pool.connect(
    client=bot,
    nodes=[...],
    regions={
        "my-region": ["custom-endpoint-prefix"],
    }
)
```

---

## Logger Configuration

Voltricx ships with a structured logger for debugging:

```python
import voltricx

voltricx.voltricx_logger.enable()
voltricx.voltricx_logger.set_level("DEBUG")   # "DEBUG", "INFO", "WARNING", "ERROR"
```

To disable logging (default):

```python
voltricx.voltricx_logger.disable()
```

---

## Environment Variables Pattern

For production bots, use environment variables:

```env title=".env"
TOKEN=your_discord_token

NODE_1_URI=http://lavalink1:2333
NODE_1_PASSWORD=strongpassword
NODE_1_REGION=us

NODE_2_URI=http://lavalink2:2333
NODE_2_PASSWORD=strongpassword2
NODE_2_REGION=eu
```

```python title="bot.py"
import os
from dotenv import load_dotenv
import voltricx

load_dotenv()

async def setup_hook(self):
    nodes = []
    for i in range(1, 10):
        uri = os.getenv(f"NODE_{i}_URI")
        password = os.getenv(f"NODE_{i}_PASSWORD")
        region = os.getenv(f"NODE_{i}_REGION", "global")
        if uri and password:
            nodes.append(voltricx.NodeConfig(
                identifier=f"Node-{i}",
                uri=uri,
                password=password,
                region=region,
            ))

    await voltricx.Pool.connect(client=self, nodes=nodes)
```
