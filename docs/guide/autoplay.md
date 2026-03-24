---
title: AutoPlay & Recommendations
description: Keep the music going forever with Voltricx's intelligent AutoPlay engine.
---

# AutoPlay & Recommendations

Voltricx's AutoPlay engine automatically queues recommended tracks when the queue runs dry, keeping the music flowing without manual interaction.

## AutoPlay Modes

There are three autoplay modes controlled via `player.autoplay`:

| Mode | Enum | Behavior |
|------|------|----------|
| `partial` | `AutoPlayMode.partial` | *(Default)* Plays through the queue normally; does NOT auto-recommend new tracks |
| `enabled` | `AutoPlayMode.enabled` | Actively fetches YouTube radio-based recommendations when the queue is empty |
| `disabled` | `AutoPlayMode.disabled` | Stops completely when the queue is empty |

```python
from voltricx import AutoPlayMode

player.autoplay = AutoPlayMode.enabled    # Full auto-recommendations
player.autoplay = AutoPlayMode.partial    # Manual queue only
player.autoplay = AutoPlayMode.disabled  # No autoplay
```

---

## Setting AutoPlay

```python
@bot.command()
async def autoplay(ctx: commands.Context, mode: str = "partial"):
    player: voltricx.Player = ctx.voice_client
    if not player:
        return await ctx.send("Not connected.")

    try:
        amode = voltricx.AutoPlayMode(mode.lower())
        player.autoplay = amode
        await ctx.send(f"✅ AutoPlay set to **{amode.value}**")
    except ValueError:
        await ctx.send("❌ Invalid mode. Use: `enabled`, `partial`, or `disabled`")
```

---

## How the Recommendation Engine Works

When `autoplay` is `enabled` and the queue is empty, Voltricx:

1. **Checks HyperCache L2** for a random cached track (fastest path, zero API call)
2. **Builds seed tracks** from play history, `auto_queue`, and the current track — weighted by recency
3. **Fetches a YouTube Radio playlist** (`/watch?v=ID&list=RDID`) based on the best seed track
4. **Populates `auto_queue`** with up to `_auto_cutoff` tracks (default: 20), skipping duplicates
5. **Plays the next track** from `auto_queue`

---

## Pre-Populating Recommendations

You can trigger recommendation population immediately when playing a track using the `populate` flag:

```python
await player.play(track, populate=True, max_populate=10)
```

This is useful for warming up the auto_queue **before** the current track ends.

---

## Tuning AutoPlay Behaviour

```python
player._auto_cutoff = 20    # Max tracks held in auto_queue at once
player._auto_weight = 3     # History weighting factor for seed selection
```

---

## The `auto_queue`

`player.auto_queue` is a separate `Queue` object that holds recommendation tracks. You can inspect or modify it:

```python
# View recommended tracks
for track in player.auto_queue:
    print(f"  Recommended: {track.title}")

# Clear recommendations
player.auto_queue.clear()
```

Recommended tracks have `track.recommended == True`:

```python
if track.recommended:
    print("This track was auto-recommended")
```

---

## HyperCache Integration

When `autoplay = enabled`, Voltricx first checks HyperCache L2 for a random cached track. This means:

- If users have recently searched for tracks, those become candidates for autoplay
- Zero Lavalink API calls for the most common autoplay scenario
- The more your bot is used, the better the autoplay becomes

Enable caching when connecting the Pool:

```python
await voltricx.Pool.connect(
    client=bot,
    nodes=[...],
    cache_config={"capacity": 200, "track_capacity": 2000},
)
```

---

## Full AutoPlay Bot Example

```python
class MusicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_voltricx_track_end(self, player: voltricx.Player, track, reason):
        # Only show a message for naturally finished tracks
        if str(reason) == "finished" and player.home:
            await player.home.send(f"✅ Finished: **{track.title}**")

    @commands.Cog.listener()
    async def on_voltricx_inactive_player(self, player: voltricx.Player):
        if player.home:
            await player.home.send("💤 Queue empty and autoplay exhausted. Leaving.")
        await player.disconnect()

    @commands.command()
    async def play(self, ctx: commands.Context, *, query: str):
        if not ctx.voice_client:
            player = await ctx.author.voice.channel.connect(cls=voltricx.Player)
            player.home = ctx.channel
            player.autoplay = voltricx.AutoPlayMode.enabled  # Enable autoplay
        else:
            player = ctx.voice_client

        results = await voltricx.Pool.fetch_tracks(query)
        if not results:
            return await ctx.send("No results.")

        if isinstance(results, voltricx.Playlist):
            player.queue.put(results)
            await ctx.send(f"📋 Queued playlist **{results.name}**")
        else:
            player.queue.put(results[0])
            await ctx.send(f"➕ Queued **{results[0].title}**")

        if not player.playing:
            await player.play(player.queue.get(), populate=True)
```
