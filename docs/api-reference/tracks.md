---
title: Playable & Playlist
description: API reference for Playable and Playlist track models.
---

# `Playable` & `Playlist`



## `Playable`

Represents a single audio track from Lavalink. Built on a frozen Pydantic v2 model.

```python
track: voltricx.Playable = results[0]
print(f"{track.title} by {track.author} [{track.length // 1000}s]")
```

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `track.encoded` | `str` | Base64-encoded track identifier |
| `track.identifier` | `str` | Source-specific track ID |
| `track.title` | `str` | Track title |
| `track.author` | `str` | Artist/channel name |
| `track.length` | `int` | Total duration in milliseconds |
| `track.uri` | `str \| None` | URL of the track |
| `track.artwork` | `str \| None` | Thumbnail/artwork URL |
| `track.isrc` | `str \| None` | International Standard Recording Code |
| `track.source` | `str` | Source name (e.g. `"youtube"`, `"deezer"`) |
| `track.is_seekable` | `bool` | Whether the track supports seeking |
| `track.is_stream` | `bool` | `True` for live streams |
| `track.position` | `int` | Track start position (usually 0) |
| `track.extras` | `dict[str, Any]` | Custom user data attached to the track |
| `track.recommended` | `bool` | `True` if added by AutoPlay recommendations |
| `track.plugin_info` | `dict[str, Any]` | Plugin-specific metadata |

### Methods

#### `Playable.search()`

Class method for searching tracks directly.

```python
results = await voltricx.Playable.search("Never Gonna Give You Up")
results = await voltricx.Playable.search("https://youtube.com/watch?v=...", source="ytsearch")
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | `str` | — | Search term or URL |
| `source` | `str` | `"dzsearch"` | Search source prefix |
| `node` | `Node \| None` | `None` | Specific node to use |

**Returns:** `list[Playable] | Playlist`

### Comparison & Hashing

Two `Playable` objects are considered equal if their `encoded` strings **or** `identifier` values match:

```python
if track1 == track2:
    print("Same track!")

tracks_set = {track1, track2}  # Hashable
```

### Setting Extras

```python
track.extras = {"requested_by": ctx.author.id}
print(track.extras["requested_by"])
```

---

## `Playlist`

Represents a collection of tracks (from a playlist URL or album).

```python
results = await voltricx.Pool.fetch_tracks("https://www.youtube.com/playlist?list=...")

if isinstance(results, voltricx.Playlist):
    print(f"Playlist: {results.name}")
    print(f"Tracks: {len(results)}")
    print(f"Selected track index: {results.selected}")
```

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `playlist.name` | `str` | Playlist name |
| `playlist.selected` | `int` | Index of the "selected" track in the playlist |
| `playlist.tracks` | `list[Playable]` | All tracks in the playlist |
| `playlist.extras` | `dict[str, Any]` | Custom user data |
| `playlist.plugin_info` | `dict[str, Any]` | Plugin-specific metadata |

### Iteration

```python
for track in playlist:
    print(track.title)

# Length
print(len(playlist))

# Index access
first = playlist[0]
```

### Adding to Queue

```python
# Add all tracks
count = player.queue.put(playlist)
print(f"Added {count} tracks")
```

---

## `TrackInfo`

Internal frozen model holding raw track metadata. Accessed via `track.info`:

```python
info = track.info
print(info.source_name)   # "youtube"
print(info.is_stream)     # False
```

---

## Type Aliases

| Alias | Type |
|-------|------|
| `Search` | `list[Playable] \| Playlist` |
| `LoadTracksResult` | Union of all result types with `load_type` discriminator |
