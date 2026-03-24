---
title: Playback Control
description: Playing tracks, pausing, seeking, volume control, and more with the Voltricx Player.
---

# Playback Control

The `Player` class is Voltricx's audio engine — it extends `discord.VoiceProtocol` and wraps all Lavalink player operations.

## Connecting a Player

Pass `cls=voltricx.Player` to `channel.connect()`:

```python
player: voltricx.Player = await ctx.author.voice.channel.connect(cls=voltricx.Player)
```

Or retrieve an existing player:

```python
player: voltricx.Player = ctx.voice_client  # type: ignore
```

---

## Searching for Tracks

Use `Pool.fetch_tracks()` to search or resolve a URL:

```python
# Plain text search (uses default_search_source if configured)
results = await voltricx.Pool.fetch_tracks("Bohemian Rhapsody")

# Explicit source prefix
results = await voltricx.Pool.fetch_tracks("dzsearch:Bohemian Rhapsody")   # Deezer
results = await voltricx.Pool.fetch_tracks("ytsearch:Bohemian Rhapsody")   # YouTube
results = await voltricx.Pool.fetch_tracks("scsearch:Bohemian Rhapsody")   # SoundCloud

# Direct URL
results = await voltricx.Pool.fetch_tracks("https://open.spotify.com/track/...")
results = await voltricx.Pool.fetch_tracks("https://www.youtube.com/watch?v=...")
```

Results are either a `list[Playable]` (single track / search results) or a `Playlist`:

```python
if isinstance(results, voltricx.Playlist):
    print(f"Playlist: {results.name} ({len(results)} tracks)")
    player.queue.put(results)
else:
    track = results[0]
    print(f"Track: {track.title} by {track.author}")
    player.queue.put(track)
```

You can also search directly on a `Playable`:

```python
results = await voltricx.Playable.search("Beethoven Symphony No. 5", source="dzsearch")
```

---

## Playing a Track

```python
track = results[0]
await player.play(track)
```

### `play()` Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `track` | `Playable` | — | The track to play |
| `replace` | `bool` | `True` | Replace the current track immediately |
| `start` | `int` | `0` | Start position in milliseconds |
| `end` | `int \| None` | `None` | End position in milliseconds |
| `volume` | `int \| None` | `None` | Override volume for this track |
| `paused` | `bool \| None` | `None` | Start in paused state |
| `add_history` | `bool` | `True` | Add to queue history |
| `filters` | `Filters \| None` | `None` | Override filters for this track |
| `populate` | `bool` | `False` | Populate auto_queue with recommendations |
| `max_populate` | `int` | `5` | Max tracks to add to auto_queue |

---

## Stopping Playback

```python
await player.stop()   # Skip to next or stop if queue empty
await player.skip()   # Same as stop() with force=True
```

---

## Pause & Resume

```python
await player.pause(True)   # Pause
await player.pause(False)  # Resume
```

Check state:

```python
if player.paused:
    print("Player is paused")
```

---

## Seeking

Seek to a position in milliseconds:

```python
await player.seek(30_000)   # Seek to 30 seconds
await player.seek(0)        # Restart from beginning
```

---

## Volume Control

Volume ranges from **0** to **1000** (100 = normal, 200 = double, etc.):

```python
await player.set_volume(100)   # Normal
await player.set_volume(50)    # Half volume
await player.set_volume(200)   # Double volume
```

Read current volume:

```python
print(player.volume)  # int
```

---

## Track Position

`player.position` provides a nanosecond-precision estimate of the current playback position:

```python
position_ms = player.position   # milliseconds
position_sec = position_ms / 1000
```

---

## Player State Properties

| Property | Type | Description |
|----------|------|-------------|
| `player.current` | `Playable \| None` | Currently playing track |
| `player.playing` | `bool` | `True` if connected and a track is active |
| `player.paused` | `bool` | `True` if paused |
| `player.volume` | `int` | Current volume (0–1000) |
| `player.position` | `int` | Current playback position (ms) |
| `player.ping` | `int` | WebSocket round-trip ping (ms) |
| `player.node` | `Node` | The node this player is on |
| `player.guild` | `Guild \| None` | The guild this player belongs to |
| `player.channel` | `VoiceChannel \| StageChannel` | Current voice channel |

---

## Moving Channels

```python
new_channel = bot.get_channel(CHANNEL_ID)
await player.move_to(new_channel)
```

Disconnect from voice entirely:

```python
await player.move_to(None)
```

---

## Migrating to Another Node

Manually migrate a player to a different Lavalink node:

```python
target_node = voltricx.Pool.get_node("EU")
await player.migrate_to(target_node)
```

Voltricx does this **automatically** during failover.

---

## Disconnecting

```python
await player.disconnect()
```

This cleans up the player from both Voltricx's internal registry and Discord's voice state.

---

## Inactivity Timeout

Configure automatic disconnect when the player is idle:

```python
player.inactive_timeout = 300    # Auto-disconnect after 5 minutes of inactivity
player.inactive_timeout = 0      # Disable auto-disconnect
```

Check idle state:

```python
if player.is_idle:
    print(f"Player has been idle for {player.idle_time:.1f} seconds")
```

Listen for the event:

```python
@bot.event
async def on_voltricx_inactive_player(player: voltricx.Player):
    await player.disconnect()
    if player.home:
        await player.home.send("💤 Disconnected due to inactivity.")
```

---

## Setting `player.home`

`player.home` stores the text channel where music commands were sent — useful for sending notifications:

```python
player.home = ctx.channel
```

---

## Full Playback Example

```python
@bot.command()
async def play(ctx: commands.Context, *, query: str):
    if not ctx.author.voice:
        return await ctx.send("❌ Join a voice channel first!")

    if ctx.voice_client:
        player: voltricx.Player = ctx.voice_client
    else:
        player: voltricx.Player = await ctx.author.voice.channel.connect(cls=voltricx.Player)
        player.home = ctx.channel
        player.inactive_timeout = 300  # 5 min inactivity disconnect

    results = await voltricx.Pool.fetch_tracks(query)
    if not results:
        return await ctx.send("❌ No results found.")

    if isinstance(results, voltricx.Playlist):
        added = player.queue.put(results)
        await ctx.send(f"📋 Queued **{results.name}** — {added} tracks")
    else:
        track = results[0]
        player.queue.put(track)
        await ctx.send(f"➕ Queued **{track.title}**")

    if not player.playing:
        await player.play(player.queue.get())
```
