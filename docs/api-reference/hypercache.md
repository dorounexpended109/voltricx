---
title: HyperCache
description: API reference for the HyperCache dual-tier caching system.
---

# `HyperCache`



A dual-tier caching system combining an LRU query cache (L1) and an LFU track registry (L2) with frequency decay.

---

## Constructor

```python
HyperCache(
    query_capacity: int = 100,
    track_capacity: int = 1000,
    decay_factor: float = 0.5,
    decay_threshold: int = 1000,
)
```

| Parameter | Description |
|-----------|-------------|
| `query_capacity` | Max queries cached in L1 (LRU) |
| `track_capacity` | Max tracks cached in L2 (LFU) |
| `decay_factor` | Frequency multiplier on decay (0–1). Lower = faster decay |
| `decay_threshold` | Total hits before L2 applies a decay pass |

---

## Class Methods

### `HyperCache.from_config()`

Create a HyperCache from a config dict or `HyperCacheConfig` model.

```python
cache = HyperCache.from_config({
    "capacity": 200,
    "track_capacity": 2000,
    "decay_factor": 0.5,
    "decay_threshold": 1000,
})
```

---

## Instance Methods

### `cache.get_query()`

Retrieve tracks for a query string, hydrated from L2.

```python
tracks = cache.get_query("Bohemian Rhapsody")
# → list[Playable] or None
```

Returns `None` if the query is not cached or any track is missing from L2.

---

### `cache.put_query()`

Store a list of tracks for a query string.

```python
cache.put_query("Bohemian Rhapsody", [track1, track2])
```

---

### `cache.get_stats()`

Return current L1 and L2 counts.

```python
stats = cache.get_stats()
# → {"l1_queries": 42, "l2_tracks": 318}
```

---

### `cache.get_entries()`

Return a map of query → track title list for inspection.

```python
entries = cache.get_entries()
for query, titles in entries.items():
    print(f"{query!r}: {titles}")
```

---

### `cache.get_random_track()`

Return a random `Playable` from L2.

```python
track = cache.get_random_track()  # Playable | None
```

---

### `cache.resize()`

Resize cache tiers dynamically. Existing data is migrated.

```python
cache.resize(query_capacity=500, track_capacity=5000)
cache.resize(decay_factor=0.3, decay_threshold=500)
```

---

### `cache.resize_from_config()`

Resize using a config dict or model.

```python
cache.resize_from_config({"capacity": 500, "track_capacity": 5000})
```

---

## Internal Caches

### `LRUCache`

Least Recently Used cache. Internally wraps an `OrderedDict`.

```python
lru = LRUCache(capacity=100)
lru.put("key", value)
result = lru.get("key")   # Moves to end (recently used)
```

When at capacity, the **oldest** (least recently used) entry is evicted.

---

### `LFUCache`

Least Frequently Used cache with frequency decay.

```python
lfu = LFUCache(capacity=1000, decay_factor=0.5, decay_threshold=1000)
lfu.put("key", value)
result = lfu.get("key")   # Increments hit count
```

When at capacity, the entry with the **lowest hit frequency** is evicted. On every `decay_threshold` hits, all frequencies are multiplied by `decay_factor` to let newer popular items displace old ones.
