---
title: Quick Start
description: Build your first Discord music bot with Voltricx in minutes.
---

# Quick Start

This guide will get you from zero to a working music bot in under 5 minutes.

## 1. Set Up Your Project

```
my-music-bot/
├── bot.py
├── .env
└── application.yml   # Lavalink config
```

Create a `.env` file:

```env title=".env"
TOKEN=your_discord_bot_token
LAVALINK_URI=http://localhost:2333
LAVALINK_PASSWORD=youshallnotpass
```

## 2. Create the Bot

```python title="bot.py"
import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import voltricx

load_dotenv()

class MusicBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.voice_states = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        """Called once when the bot is starting up."""
        await voltricx.Pool.connect(
            client=self,
            nodes=[
                voltricx.NodeConfig(
                    identifier="Main",
                    uri=os.getenv("LAVALINK_URI"),
                    password=os.getenv("LAVALINK_PASSWORD"),
                )
            ],
            cache_config={"capacity": 100, "track_capacity": 500},
            default_search_source="dzsearch",  # (1)
        )

    async def close(self):
        await voltricx.Pool.close()  # (2)
        await super().close()

bot = MusicBot()
```

1. Sets Deezer as the default search source. When you search "Never Gonna Give You Up", it becomes `dzsearch:Never Gonna Give You Up` automatically.
2. Always close the Pool cleanly to release node connections.

## 3. Listen to Node Events

```python title="bot.py (continued)"
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

@bot.event
async def on_voltricx_node_ready(node: voltricx.Node):
    print(f"⚡ Lavalink node {node.identifier!r} is connected!")

@bot.event
async def on_voltricx_track_start(player: voltricx.Player, track: voltricx.Playable):
    if player.home:
        await player.home.send(f"🎶 Now playing: **{track.title}** by {track.author}")

@bot.event
async def on_voltricx_track_end(player: voltricx.Player, track: voltricx.Playable, reason):
    if player.home and str(reason) == "finished":
        await player.home.send(f"✅ Finished: **{track.title}**")
```

## 4. Add Music Commands

```python title="bot.py (continued)"
def ensure_voice(ctx: commands.Context) -> voltricx.Player:
    """Helper: connect if needed, return player."""
    if ctx.voice_client:
        return ctx.voice_client  # type: ignore
    if not ctx.author.voice:
        raise commands.CheckFailure("You must be in a voice channel.")
    return None  # will connect below


@bot.command()
async def join(ctx: commands.Context):
    """Join the caller's voice channel."""
    if not ctx.author.voice:
        return await ctx.send("❌ Join a voice channel first!")
    player: voltricx.Player = await ctx.author.voice.channel.connect(cls=voltricx.Player)
    player.home = ctx.channel
    await ctx.send(f"✅ Connected to **{ctx.author.voice.channel.name}**")


@bot.command(aliases=["p"])
async def play(ctx: commands.Context, *, query: str):
    """Search and play a track, or add it to the queue."""
    if not ctx.author.voice:
        return await ctx.send("❌ You must be in a voice channel!")

    # Connect if not already in a channel
    if not ctx.voice_client:
        player: voltricx.Player = await ctx.author.voice.channel.connect(cls=voltricx.Player)
        player.home = ctx.channel
    else:
        player: voltricx.Player = ctx.voice_client

    # Fetch tracks (uses default_search_source if not a URL)
    results = await voltricx.Pool.fetch_tracks(query)

    if not results:
        return await ctx.send(f"❌ No results found for `{query}`")

    if isinstance(results, voltricx.Playlist):
        # It's a playlist — queue all tracks
        count = player.queue.put(results)
        await ctx.send(f"📋 Added **{results.name}** ({count} tracks) to the queue.")
    else:
        track = results[0]
        player.queue.put(track)
        await ctx.send(f"➕ Added **{track.title}** to the queue.")

    # Start playing if not already
    if not player.playing:
        next_track = player.queue.get()
        await player.play(next_track)


@bot.command()
async def skip(ctx: commands.Context):
    """Skip the current track."""
    if not ctx.voice_client:
        return await ctx.send("❌ Not connected to a voice channel.")
    await ctx.voice_client.skip()
    await ctx.send("⏭️ Skipped!")


@bot.command()
async def pause(ctx: commands.Context):
    """Pause playback."""
    if ctx.voice_client:
        await ctx.voice_client.pause(True)
        await ctx.send("⏸️ Paused.")


@bot.command()
async def resume(ctx: commands.Context):
    """Resume playback."""
    if ctx.voice_client:
        await ctx.voice_client.pause(False)
        await ctx.send("▶️ Resumed.")


@bot.command()
async def volume(ctx: commands.Context, level: int):
    """Set volume (0–1000)."""
    if ctx.voice_client:
        await ctx.voice_client.set_volume(level)
        await ctx.send(f"🔊 Volume set to **{level}%**")


@bot.command(aliases=["np"])
async def nowplaying(ctx: commands.Context):
    """Show the currently playing track."""
    player: voltricx.Player = ctx.voice_client
    if not player or not player.current:
        return await ctx.send("Nothing is playing right now.")

    track = player.current
    pos = player.position
    length = track.length

    # Build progress bar
    filled = int((pos / length) * 20) if length else 0
    bar = "▬" * filled + "🔘" + "▬" * max(0, 20 - filled)

    embed = discord.Embed(
        title="🎵 Now Playing",
        description=f"**[{track.title}]({track.uri})**\nby {track.author}",
        color=0x7c3aed,
    )
    embed.add_field(
        name="Progress",
        value=f"`{pos // 60000}:{(pos // 1000) % 60:02d}` {bar} `{length // 60000}:{(length // 1000) % 60:02d}`",
        inline=False,
    )
    embed.set_thumbnail(url=track.artwork)
    await ctx.send(embed=embed)


@bot.command()
async def disconnect(ctx: commands.Context):
    """Disconnect the bot from voice."""
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Disconnected.")


bot.run(os.getenv("TOKEN"))
```

## 5. Run Your Bot

```bash
# Make sure Lavalink is running first!
python bot.py
```

Your bot is now online. Try these commands in Discord:

| Command | Description |
|---------|-------------|
| `!join` | Connect to your voice channel |
| `!play never gonna give you up` | Search and play a track |
| `!play https://youtube.com/watch?v=...` | Play from URL |
| `!skip` | Skip current track |
| `!pause` / `!resume` | Pause and resume |
| `!volume 80` | Set volume to 80% |
| `!np` | Show currently playing track |
| `!disconnect` | Leave the voice channel |

---

## What's Next?

<div class="vtx-grid">

<div class="vtx-card">
<span class="vtx-card__icon">📋</span>
<div class="vtx-card__title"><a href="../guide/queue/">Queue Management</a></div>
<div class="vtx-card__desc">Learn how to use shuffle, loop modes, history, and priority queuing.</div>
</div>

<div class="vtx-card">
<span class="vtx-card__icon">🎛️</span>
<div class="vtx-card__title"><a href="../guide/filters/">Audio Filters</a></div>
<div class="vtx-card__desc">Apply Nightcore, Bass Boost, 8D audio, Karaoke, and more.</div>
</div>

<div class="vtx-card">
<span class="vtx-card__icon">🎯</span>
<div class="vtx-card__title"><a href="../guide/autoplay/">AutoPlay</a></div>
<div class="vtx-card__desc">Set up automated track recommendations when the queue runs dry.</div>
</div>

<div class="vtx-card">
<span class="vtx-card__icon">🏗️</span>
<div class="vtx-card__title"><a href="../examples/full-bot/">Full Bot Example</a></div>
<div class="vtx-card__desc">See a complete, production-ready bot with all features enabled.</div>
</div>

</div>
