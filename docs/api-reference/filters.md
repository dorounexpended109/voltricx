---
title: Filters
description: API reference for Voltricx audio filter classes.
---

# Filters



## `Filters`

The top-level container for all audio filters. Every `Player` has a `Filters` instance at `player.filters`.

```python
filters = player.filters           # Get current filters
filters = voltricx.Filters()       # Create empty filters
```

### Constructor

```python
Filters(data: dict[str, Any] | None = None)
```

### Attributes

| Attribute | Type | Default |
|-----------|------|---------|
| `filters.volume` | `float` | `1.0` |
| `filters.equalizer` | `Equalizer` | Flat (all gains 0.0) |
| `filters.karaoke` | `Karaoke` | Default |
| `filters.timescale` | `Timescale` | 1.0 speed/pitch/rate |
| `filters.tremolo` | `Tremolo` | Default |
| `filters.vibrato` | `Vibrato` | Default |
| `filters.rotation` | `Rotation` | 0 Hz |
| `filters.distortion` | `Distortion` | Default |
| `filters.channel_mix` | `ChannelMix` | L→L=1, R→R=1 |
| `filters.low_pass` | `LowPass` | 20.0 smoothing |
| `filters.plugin_filters` | `PluginFilters` | Empty |

### Methods

#### `filters.reset()`

Reset all filters to defaults. Returns `self` for chaining.

```python
filters.reset()
```

#### `filters.set_filters()`

Set multiple filters at once using keyword arguments.

```python
filters.set_filters(timescale={"speed": 1.3, "pitch": 1.3}, reset=False)
```

#### `filters.to_dict()`

Serialize only non-default filters to a Lavalink-compatible payload.

```python
payload = filters.to_dict()
# → {"timescale": {"speed": 1.3, "pitch": 1.3}}
```

#### `Filters.from_filters()`

Class method: create a `Filters` object with pre-set values.

```python
filters = voltricx.Filters.from_filters(
    timescale={"speed": 1.3, "pitch": 1.3},
)
```

---

## `Equalizer`

15-band parametric equalizer. Band `0` = deepest bass, `14` = highest treble.

```python
filters.equalizer.set_band(band=0, gain=0.25)
filters.equalizer.set(bands=[{"band": 0, "gain": 0.25}])
filters.equalizer.reset()

payload = filters.equalizer.payload  # list of {"band": int, "gain": float}
```

| Method | Description |
|--------|-------------|
| `set_band(band, gain)` | Set gain for a specific band |
| `set(bands)` | Set all bands (resets unspecified bands to 0) |
| `reset()` | Flatten all bands back to 0.0 |

**Gain range:** `-0.25` (muted) to `1.0` (doubled volume)

---

## `Karaoke`

Vocal elimination via equalization.

```python
filters.karaoke.set(level=1.0, mono_level=1.0, filter_band=220.0, filter_width=100.0)
filters.karaoke.reset()
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `level` | `float` | `1.0` | Vocal removal strength |
| `mono_level` | `float` | `1.0` | Mono level |
| `filter_band` | `float` | `220.0` | Center frequency (Hz) |
| `filter_width` | `float` | `100.0` | Filter width |

---

## `Timescale`

Changes speed, pitch, and rate independently.

```python
filters.timescale.set(speed=1.3, pitch=1.3, rate=1.0)
filters.timescale.reset()
```

| Parameter | Range | Default |
|-----------|-------|---------|
| `speed` | > 0.0 | `1.0` |
| `pitch` | > 0.0 | `1.0` |
| `rate` | > 0.0 | `1.0` |

---

## `Tremolo`

Oscillates volume at a set frequency.

```python
filters.tremolo.set(frequency=2.0, depth=0.5)
filters.tremolo.reset()
```

| Parameter | Range | Default |
|-----------|-------|---------|
| `frequency` | 0–14 Hz | `2.0` |
| `depth` | 0.0–1.0 | `0.5` |

---

## `Vibrato`

Oscillates pitch at a set frequency.

```python
filters.vibrato.set(frequency=2.0, depth=0.5)
filters.vibrato.reset()
```

| Parameter | Range | Default |
|-----------|-------|---------|
| `frequency` | 0–14 Hz | `2.0` |
| `depth` | 0.0–1.0 | `0.5` |

---

## `Rotation`

Stereo panning / 8D audio effect.

```python
filters.rotation.set(rotation_hz=0.2)
filters.rotation.reset()
```

| Parameter | Default |
|-----------|---------|
| `rotation_hz` | `0.0` |

---

## `Distortion`

Applies mathematical distortion.

```python
filters.distortion.set(
    sin_offset=0.0, sin_scale=1.0,
    cos_offset=0.0, cos_scale=1.0,
    tan_offset=0.0, tan_scale=1.0,
    offset=0.0, scale=1.0
)
filters.distortion.reset()
```

---

## `ChannelMix`

Controls how left and right channels are blended.

```python
filters.channel_mix.set(
    left_to_left=1.0,
    left_to_right=0.0,
    right_to_left=0.0,
    right_to_right=1.0,
)
filters.channel_mix.reset()
```

---

## `LowPass`

Attenuates frequencies above the cutoff.

```python
filters.low_pass.set(smoothing=20.0)
filters.low_pass.reset()
```

---

## `PluginFilters`

Pass arbitrary data to Lavalink plugins.

```python
filters.plugin_filters.set(my_plugin={"key": "value"})
payload = filters.plugin_filters.payload  # dict
filters.plugin_filters.reset()
```
