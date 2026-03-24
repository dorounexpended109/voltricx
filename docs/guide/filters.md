---
title: Audio Filters
description: Apply Equalizer, Timescale, Karaoke, Vibrato, Rotation, and more with Voltricx Filters.
---

# Audio Filters

Voltricx wraps all Lavalink v4 audio filters in clean, chainable Python classes. You can combine multiple filters simultaneously.

## Overview

| Filter | Class | Effect |
|--------|-------|--------|
| Equalizer | `Filters.equalizer` | Adjust individual frequency bands |
| Karaoke | `Karaoke` | Remove or isolate vocals |
| Timescale | `Timescale` | Change speed, pitch, and rate |
| Tremolo | `Tremolo` | Oscillate volume rapidly |
| Vibrato | `Vibrato` | Oscillate pitch |
| Rotation | `Rotation` | Stereo panning / 8D audio |
| Distortion | `Distortion` | Audio distortion effects |
| ChannelMix | `ChannelMix` | Mix left/right channels |
| LowPass | `LowPass` | Suppress high frequencies |

---

## Getting & Setting Filters

```python
# Get the current Filters object
filters = player.filters

# Apply filters back to the player
await player.set_filters(filters)
```

To reset all filters:

```python
await player.set_filters(voltricx.Filters())
```

---

## Equalizer

15 bands from `0` (deepest bass) to `14` (highest treble). Gain: `-0.25` (muted) to `1.0` (doubled).

```python
filters = player.filters

# Set a specific band
filters.equalizer.set_band(band=0, gain=0.25)   # Boost bass

# Set multiple bands at once (resets others to 0)
filters.equalizer.set(bands=[
    {"band": 0, "gain": 0.25},
    {"band": 1, "gain": 0.20},
    {"band": 2, "gain": 0.15},
])

# Reset to flat
filters.equalizer.reset()

await player.set_filters(filters)
```

### Preset: Bass Boost

```python
filters = player.filters
for i in range(4):  # Bands 0-3 = bass
    filters.equalizer.set_band(band=i, gain=0.25)
await player.set_filters(filters)
```

---

## Timescale

Changes speed, pitch, and rate independently.

```python
filters = player.filters

# Nightcore (faster + higher pitch)
filters.timescale.set(speed=1.3, pitch=1.3)

# Vaporwave (slower + lower pitch)
filters.timescale.set(speed=0.8, pitch=0.8)

# Chipmunk (high pitch, normal speed)
filters.timescale.set(speed=1.0, pitch=1.5)

# Deep voice (low pitch, normal speed)
filters.timescale.set(speed=1.0, pitch=0.6)

# Slow motion (half speed, keep pitch)
filters.timescale.set(speed=0.5, rate=0.5)

# Reset
filters.timescale.reset()

await player.set_filters(filters)
```

| Parameter | Range | Default |
|-----------|-------|---------|
| `speed` | > 0.0 | `1.0` |
| `pitch` | > 0.0 | `1.0` |
| `rate` | > 0.0 | `1.0` |

---

## Karaoke

Uses equalization to eliminate part of the audio spectrum, typically targeting vocals.

```python
filters = player.filters

# Enable karaoke
filters.karaoke.set(
    level=1.0,          # Vocal removal strength (0.0–1.0)
    mono_level=1.0,     # Mono level (0.0–1.0)
    filter_band=220.0,  # Filter center frequency (Hz)
    filter_width=100.0, # Filter width
)

# Disable
filters.karaoke.reset()

await player.set_filters(filters)
```

---

## Tremolo

Oscillates the volume at a set frequency to create a shuddering effect.

```python
filters = player.filters
filters.tremolo.set(frequency=4.0, depth=0.75)
await player.set_filters(filters)
```

| Parameter | Range | Default |
|-----------|-------|---------|
| `frequency` | 0.0–14.0 Hz | `2.0` |
| `depth` | 0.0–1.0 | `0.5` |

---

## Vibrato

Like tremolo but oscillates pitch instead of volume.

```python
filters = player.filters
filters.vibrato.set(frequency=4.0, depth=0.5)
await player.set_filters(filters)
```

| Parameter | Range | Default |
|-----------|-------|---------|
| `frequency` | 0.0–14.0 Hz | `2.0` |
| `depth` | 0.0–1.0 | `0.5` |

---

## Rotation (8D Audio)

Rotates the audio around the stereo field — when listened to with headphones, gives a 3D "8D" effect.

```python
filters = player.filters
filters.rotation.set(rotation_hz=0.2)   # Rotation speed in Hz
await player.set_filters(filters)
```

| Parameter | Default |
|-----------|---------|
| `rotation_hz` | `0.0` (off) |

---

## Distortion

Applies mathematical distortion using sin/cos/tan functions.

```python
filters = player.filters
filters.distortion.set(
    sin_offset=0.0,
    sin_scale=1.0,
    cos_offset=0.0,
    cos_scale=1.0,
    tan_offset=0.0,
    tan_scale=1.0,
    offset=0.0,
    scale=1.0,
)
await player.set_filters(filters)
```

---

## ChannelMix

Controls how the left and right channels are mixed. Perfect for mono audio or creative panning.

```python
filters = player.filters

# Force mono (both channels = mix of L+R)
filters.channel_mix.set(
    left_to_left=0.5,
    left_to_right=0.5,
    right_to_left=0.5,
    right_to_right=0.5,
)

# Full left (L only)
filters.channel_mix.set(left_to_left=1.0, left_to_right=0.0,
                         right_to_left=1.0, right_to_right=0.0)

await player.set_filters(filters)
```

| Parameter | Range | Default |
|-----------|-------|---------|
| `left_to_left` | 0.0–1.0 | `1.0` |
| `left_to_right` | 0.0–1.0 | `0.0` |
| `right_to_left` | 0.0–1.0 | `0.0` |
| `right_to_right` | 0.0–1.0 | `1.0` |

---

## LowPass

Attenuates frequencies above the cutoff — smoothing out harsh high-end.

```python
filters = player.filters
filters.low_pass.set(smoothing=20.0)
await player.set_filters(filters)
```

| Parameter | Default |
|-----------|---------|
| `smoothing` | `20.0` |

---

## Plugin Filters

Pass arbitrary data to Lavalink plugins:

```python
filters = player.filters
filters.plugin_filters.set(deezer={"someKey": "someValue"})
await player.set_filters(filters)
```

---

## Chaining Filters

All filter `set()` and `reset()` methods return `self`, enabling chaining:

```python
filters = voltricx.Filters()
filters.timescale.set(speed=1.3, pitch=1.3)
filters.tremolo.set(frequency=3.0, depth=0.5)
filters.rotation.set(rotation_hz=0.1)
await player.set_filters(filters)
```

---

## Creating from Scratch

```python
filters = voltricx.Filters.from_filters(
    timescale={"speed": 1.3, "pitch": 1.3},
)
await player.set_filters(filters)
```

---

## Seek After Filter

When applying timescale, you may want to re-sync the position:

```python
await player.set_filters(filters, seek=True)
```

---

## Toggle Helper Pattern

```python
async def toggle_nightcore(player: voltricx.Player):
    filters = player.filters
    if filters.timescale.speed > 1.0:
        filters.timescale.reset()
        label = "OFF"
    else:
        filters.timescale.set(speed=1.3, pitch=1.3)
        label = "ON"
    await player.set_filters(filters)
    return label
```
