"""Tests for voltricx.hypercache — targeting 100% branch coverage."""

from unittest.mock import MagicMock

from voltricx.hypercache import BaseCache, HyperCache, LFUCache, LRUCache

# ── BaseCache ──────────────────────────────────────────────────────────────


def test_base_cache_len():
    c = BaseCache(capacity=5)
    assert len(c) == 0


def test_base_cache_clear():
    c = BaseCache(capacity=5)
    c._data["a"] = 1
    c.clear()
    assert len(c) == 0


# ── LRUCache ───────────────────────────────────────────────────────────────


def test_lru_cache_put_and_get():
    c = LRUCache(capacity=3)
    c.put("a", 1)
    assert c.get("a") == 1


def test_lru_cache_miss_returns_none():
    c = LRUCache(capacity=3)
    assert c.get("missing") is None


def test_lru_cache_evicts_lru_on_overflow():
    c = LRUCache(capacity=2)
    c.put("a", 1)
    c.put("b", 2)
    c.put("c", 3)  # "a" should be evicted
    assert c.get("a") is None
    assert c.get("b") == 2
    assert c.get("c") == 3


def test_lru_cache_move_to_end_on_get():
    c = LRUCache(capacity=2)
    c.put("a", 1)
    c.put("b", 2)
    c.get("a")  # access "a" so it's recently used
    c.put("c", 3)  # should evict "b"
    assert c.get("b") is None
    assert c.get("a") == 1


def test_lru_cache_update_existing_key():
    c = LRUCache(capacity=3)
    c.put("a", 1)
    c.put("a", 99)  # update existing
    assert c.get("a") == 99
    assert len(c) == 1


# ── LFUCache ───────────────────────────────────────────────────────────────


def test_lfu_cache_put_and_get():
    c = LFUCache(capacity=5)
    c.put("x", "val")
    assert c.get("x") == "val"


def test_lfu_cache_miss_returns_none():
    c = LFUCache(capacity=5)
    assert c.get("missing") is None


def test_lfu_cache_evicts_least_frequent():
    c = LFUCache(capacity=2)
    c.put("a", 1)
    c.put("b", 2)
    c.get("b")  # b has freq 2, a has freq 1
    c.put("c", 3)  # should evict "a"
    assert c.get("a") is None
    assert c.get("b") == 2
    assert c.get("c") == 3


def test_lfu_cache_decay():
    c = LFUCache(capacity=10, decay_factor=0.5, decay_threshold=3)
    c.put("a", 1)
    # trigger decay by hitting the threshold
    for _ in range(3):
        c.get("a")
    # Frequencies should be halved; just ensure no crash and data intact
    assert c.get("a") == 1


# ── HyperCache ────────────────────────────────────────────────────────────


def _make_playable(encoded="enc1", title="Track 1"):
    track = MagicMock()
    track.encoded = encoded
    track.title = title
    return track


def test_hypercache_put_and_get_query():
    hc = HyperCache()
    t1 = _make_playable("enc1", "T1")
    t2 = _make_playable("enc2", "T2")
    hc.put_query("mysearch", [t1, t2])
    result = hc.get_query("mysearch")
    assert result is not None
    assert len(result) == 2


def test_hypercache_cache_miss():
    hc = HyperCache()
    assert hc.get_query("unknown") is None


def test_hypercache_stale_l2_returns_none():
    """If query in L1 but track missing from L2, return None."""
    hc = HyperCache()
    t = _make_playable("enc99", "Stale")
    hc.put_query("q", [t])
    hc.l2.clear()  # wipe L2 to simulate stale
    assert hc.get_query("q") is None


def test_hypercache_get_stats():
    hc = HyperCache()
    t = _make_playable()
    hc.put_query("q", [t])
    stats = hc.get_stats()
    assert stats["l1_queries"] == 1
    assert stats["l2_tracks"] == 1


def test_hypercache_get_entries():
    hc = HyperCache()
    t = _make_playable("encA", "Song A")
    hc.put_query("queryA", [t])
    entries = hc.get_entries()
    assert "queryA" in entries
    assert "Song A" in entries["queryA"]


def test_hypercache_get_random_track():
    hc = HyperCache()
    t = _make_playable()
    hc.put_query("q", [t])
    track = hc.get_random_track()
    assert track is not None


def test_hypercache_get_random_track_empty():
    hc = HyperCache()
    assert hc.get_random_track() is None


def test_hypercache_from_config_dict():
    hc = HyperCache.from_config({"capacity": 50, "track_capacity": 500})
    assert hc.l1.capacity == 50
    assert hc.l2.capacity == 500


def test_hypercache_from_config_model():
    from voltricx.typings.common import HyperCacheConfig

    cfg = HyperCacheConfig(capacity=20, track_capacity=200)
    hc = HyperCache.from_config(cfg)
    assert hc.l1.capacity == 20
    assert hc.l2.capacity == 200


def test_hypercache_resize():
    hc = HyperCache(query_capacity=10, track_capacity=100)
    t = _make_playable("r1", "Resize Test")
    hc.put_query("q", [t])
    hc.resize(query_capacity=5, track_capacity=50)
    # Data should be preserved
    assert hc.get_query("q") is not None
    assert hc.l1.capacity == 5
    assert hc.l2.capacity == 50


def test_hypercache_resize_from_config():
    hc = HyperCache()
    hc.resize_from_config({"capacity": 25, "track_capacity": 250})
    assert hc.l1.capacity == 25


def test_hypercache_put_skips_non_playable():
    """Tracks without 'encoded' are silently skipped."""
    hc = HyperCache()
    obj = MagicMock(spec=[])  # no 'encoded' attribute
    hc.put_query("q", [obj])
    assert hc.get_query("q") is None
