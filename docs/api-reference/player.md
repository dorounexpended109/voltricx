---
title: Player
description: API reference for the Voltricx Player class.
---

# `Player`



`Player` extends `discord.VoiceProtocol` and is the primary interface for controlling audio playback in a guild.

```python
player: voltricx.Player = await channel.connect(cls=voltricx.Player)
```

---

## Constructor

```python
Player(
    client: discord.Client = MISSING,
    channel: Connectable = MISSING,
    *,
    nodes: list[Node] | None = None
)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `client` | `discord.Client` | Bot client (auto-provided by discord.py) |
| `channel` | `Connectable` | Voice channel (auto-provided by discord.py) |
| `nodes` | `list[Node] \| None` | Preferred nodes; auto-selects if `None` |

---

## Properties

| Property | Type | Description |
|----------|------|-------------|
| `player.node` | `Node` | The Lavalink node handling this player |
| `player.guild` | `Guild \| None` | The guild this player belongs to |
| `player.channel` | `VoiceChannel \| StageChannel` | Current voice channel |
| `player.current` | `Playable \| None` | Track currently being played |
| `player.playing` | `bool` | `True` if connected and a track is active |
| `player.paused` | `bool` | `True` if playback is paused |
| `player.volume` | `int` | Current volume level (0–1000) |
| `player.position` | `int` | Current track position in milliseconds |
| `player.ping` | `int` | WebSocket round-trip latency in ms |
| `player.filters` | `Filters` | Active audio filter configuration |
| `player.autoplay` | `AutoPlayMode` | AutoPlay mode |
| `player.queue` | `Queue` | The main track queue |
| `player.auto_queue` | `Queue` | Recommendation queue (AutoPlay) |
| `player.home` | `TextChannel \| None` | Text channel for event notifications |
| `player.inactive_timeout` | `int` | Idle seconds before auto-disconnect (0 = disabled) |
| `player.is_idle` | `bool` | `True` if connected but not playing |
| `player.idle_time` | `float` | Seconds the player has been continuously idle |

---

## Playback Methods

### `player.play()`

Play a track (or stop playback if `track=None`).

```python
await player.play(track)
await player.play(track, replace=False, start=30_000)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `track` | `Playable` | — | Track to play |
| `replace` | `bool` | `True` | Replace current track immediately |
| `start` | `int` | `0` | Start position (ms) |
| `end` | `int \| None` | `None` | End position (ms) |
| `volume` | `int \| None` | `None` | Override volume |
| `paused` | `bool \| None` | `None` | Start in paused state |
| `add_history` | `bool` | `True` | Add to queue history |
| `filters` | `Filters \| None` | `None` | Apply specific filters |
| `populate` | `bool` | `False` | Pre-populate auto_queue |
| `max_populate` | `int` | `5` | Max tracks to add to auto_queue |

**Returns:** `Playable | None`

---

### `player.skip()`

Skip the current track. Plays the next queued track if available.

```python
await player.skip()
await player.skip(force=True)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `force` | `bool` | `True` | Force skip even if no next track |

**Returns:** `Playable | None` — the track that was playing before the skip.

---

### `player.stop()`

Stop playback (alias for `skip(force=True)`).

```python
await player.stop()
```

---

### `player.pause()`

Pause or resume playback.

```python
await player.pause(True)   # Pause
await player.pause(False)  # Resume
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `value` | `bool` | `True` to pause, `False` to resume |

---

### `player.seek()`

Seek to a position in milliseconds.

```python
await player.seek(30_000)  # Seek to 30s
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `position` | `int` | `0` | Position in milliseconds |

---

### `player.set_volume()`

Set the player volume.

```python
await player.set_volume(80)   # 80%
await player.set_volume(200)  # Double (200%)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `value` | `int` | `100` | Volume level (0–1000) |

---

### `player.set_filters()`

Apply audio filters to the player.

```python
filters = voltricx.Filters()
filters.timescale.set(speed=1.3)
await player.set_filters(filters)
await player.set_filters(filters, seek=True)  # Re-sync position too
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `filters` | `Filters \| None` | `None` | Filters to apply (`None` resets to default) |
| `seek` | `bool` | `False` | Re-send current position after applying filters |

---

## Connection Methods

### `player.connect()`

Initiate the voice connection. Usually called automatically via `channel.connect()`.

```python
await player.connect(timeout=10.0, reconnect=True, self_deaf=True)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `timeout` | `float` | `10.0` | Connection timeout in seconds |
| `reconnect` | `bool` | — | (discord.py param) whether to reconnect on disconnect |
| `self_deaf` | `bool` | `False` | Whether the bot should deafen itself |
| `self_mute` | `bool` | `False` | Whether the bot should mute itself |

**Raises:** `ChannelTimeoutException`, `InvalidChannelStateException`

---

### `player.move_to()`

Move the player to a different voice channel.

```python
new_channel = bot.get_channel(CHANNEL_ID)
await player.move_to(new_channel)
await player.move_to(None)  # Disconnect
```

---

### `player.disconnect()`

Disconnect from the voice channel and clean up.

```python
await player.disconnect()
```

---

### `player.migrate_to()`

Manually migrate this player to a different Lavalink node.

```python
target = voltricx.Pool.get_node("EU")
await player.migrate_to(target)
```

---

### `player.switch_node()`

Switch to a different node and resume state.

```python
await player.switch_node(new_node)
```

---

## Inactivity

```python
# Set timeout (seconds)
player.inactive_timeout = 300   # 5 minutes
player.inactive_timeout = 0     # Disable

# Check idle state
print(player.is_idle)       # bool
print(player.idle_time)     # seconds as float
```

Listen with:
```python
@bot.event
async def on_voltricx_inactive_player(player: voltricx.Player):
    await player.disconnect()
```
