---
title: Events
description: All Voltricx events dispatched through discord.py's event system.
---

# Events

Voltricx dispatches events through discord.py's standard event system using `client.dispatch()`. Listen to them with `@bot.event` or `@commands.Cog.listener()`.

---

## Node Events

### `on_voltricx_node_ready`

Fired when a node successfully connects and its WebSocket handshake is complete.

```python
@bot.event
async def on_voltricx_node_ready(node: voltricx.Node):
    print(f"✅ Node {node.identifier!r} is ready!")
```

| Argument | Type | Description |
|----------|------|-------------|
| `node` | `Node` | The node that just connected |

---

### `on_voltricx_node_disconnected`

Fired when a node's WebSocket connection is lost.

```python
@bot.event
async def on_voltricx_node_disconnected(node: voltricx.Node):
    print(f"❌ Node {node.identifier!r} disconnected!")
```

---

### `on_voltricx_failover`

Fired when players are being migrated from a failed node to a healthy one.

```python
@bot.event
async def on_voltricx_failover(
    old_node: voltricx.Node,
    new_node: voltricx.Node,
    players: list[voltricx.Player],
):
    for player in players:
        if player.home:
            await player.home.send(
                f"⚠️ Node failure — migrated to `{new_node.identifier}`"
            )
```

| Argument | Type | Description |
|----------|------|-------------|
| `old_node` | `Node` | The node that failed |
| `new_node` | `Node` | The node players were moved to |
| `players` | `list[Player]` | All affected players |

---

## Track Events

### `on_voltricx_track_start`

Fired when a track begins playing.

```python
@bot.event
async def on_voltricx_track_start(player: voltricx.Player, track: voltricx.Playable):
    if player.home:
        embed = discord.Embed(
            title="🎵 Now Playing",
            description=f"**{track.title}** by {track.author}",
            color=0x7c3aed,
        )
        embed.set_thumbnail(url=track.artwork)
        await player.home.send(embed=embed)
```

| Argument | Type | Description |
|----------|------|-------------|
| `player` | `Player` | The player that started the track |
| `track` | `Playable` | The track that started |

---

### `on_voltricx_track_end`

Fired when a track finishes, is stopped, or is replaced.

```python
@bot.event
async def on_voltricx_track_end(
    player: voltricx.Player,
    track: voltricx.Playable,
    reason: voltricx.TrackEndReason,
):
    print(f"Track ended: {track.title} (Reason: {reason.value})")
```

| Argument | Type | Description |
|----------|------|-------------|
| `player` | `Player` | The player |
| `track` | `Playable` | The track that ended |
| `reason` | `TrackEndReason` | Why the track ended |

#### `TrackEndReason` Values

| Value | Enum | Meaning |
|-------|------|---------|
| `finished` | `TrackEndReason.finished` | Track played to completion |
| `loadFailed` | `TrackEndReason.load_failed` | Track failed to load |
| `stopped` | `TrackEndReason.stopped` | Track was manually stopped |
| `replaced` | `TrackEndReason.replaced` | A new track replaced this one |
| `cleanup` | `TrackEndReason.cleanup` | Player cleanup |

---

### `on_voltricx_track_exception`

Fired when a track raises an exception during playback.

```python
@bot.event
async def on_voltricx_track_exception(
    player: voltricx.Player,
    track: voltricx.Playable,
    exception: Any,
):
    if player.home:
        await player.home.send(f"⚠️ Error playing **{track.title}**: `{exception}`")
```

---

### `on_voltricx_track_stuck`

Fired when a track stalls for longer than the configured threshold.

```python
@bot.event
async def on_voltricx_track_stuck(
    player: voltricx.Player,
    track: voltricx.Playable,
    threshold: int,
):
    print(f"Track stuck: {track.title} (threshold: {threshold}ms)")
    await player.skip()   # Try to skip past it
```

| Argument | Type | Description |
|----------|------|-------------|
| `player` | `Player` | The player |
| `track` | `Playable` | The stuck track |
| `threshold` | `int` | Threshold in milliseconds before the event fires |

---

## Player Events

### `on_voltricx_websocket_closed`

Fired when the Discord voice WebSocket is closed (not the Lavalink WS).

```python
@bot.event
async def on_voltricx_websocket_closed(
    player: voltricx.Player,
    code: int,
    reason: str,
    by_remote: bool,
):
    print(f"Voice WS closed: code={code}, reason={reason}, remote={by_remote}")
```

| Argument | Type | Description |
|----------|------|-------------|
| `player` | `Player` | The affected player |
| `code` | `int` | WebSocket close code |
| `reason` | `str` | Close reason string |
| `by_remote` | `bool` | `True` if Discord closed the connection |

---

### `on_voltricx_inactive_player`

Fired when a player has been idle for longer than `inactive_timeout`.

```python
@bot.event
async def on_voltricx_inactive_player(player: voltricx.Player):
    if player.home:
        await player.home.send("💤 Leaving due to inactivity.")
    await player.disconnect()
```

---

### `on_voltricx_inactive_channel`

Fired when the voice channel has been empty for the configured number of track-end events (`inactive_channel_tokens`).

```python
@bot.event
async def on_voltricx_inactive_player(player: voltricx.Player):
    # Also dispatched when channel becomes empty
    await player.disconnect()
```

---

## Using in Cogs

```python
import discord
from discord.ext import commands
import voltricx

class MusicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_voltricx_track_start(self, player: voltricx.Player, track: voltricx.Playable):
        if player.home:
            await player.home.send(f"🎶 Now playing: **{track.title}**")

    @commands.Cog.listener()
    async def on_voltricx_inactive_player(self, player: voltricx.Player):
        await player.disconnect()

async def setup(bot):
    await bot.add_cog(MusicCog(bot))
```
