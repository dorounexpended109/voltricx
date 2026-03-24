---
title: Basic Music Bot
description: A minimal but complete music bot built with Voltricx.
---

# Basic Music Bot

A clean, minimal music bot covering the essential commands. Perfect as a starting point.

```python title="basic_bot.py"
import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import voltricx

load_dotenv()

# ── Bot Setup ──────────────────────────────────────────────────────────────
class MusicBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.voice_states = True
        super().__init__(command_prefix="!", intents=intents, help_command=None)

    async def setup_hook(self):
        await voltricx.Pool.connect(
            client=self,
            nodes=[
                voltricx.NodeConfig(
                    identifier="Main",
                    uri=os.getenv("LAVALINK_URI", "http://localhost:2333"),
                    password=os.getenv("LAVALINK_PASSWORD", "youshallnotpass"),
                )
            ],
            cache_config={"capacity": 100, "track_capacity": 500},
            default_search_source="dzsearch",
        )

    async def close(self):
        await voltricx.Pool.close()
        await super().close()


bot = MusicBot()


# ── Events ─────────────────────────────────────────────────────────────────
@bot.event
async def on_ready():
    print(f"🎵 {bot.user} is ready!")

@bot.event
async def on_voltricx_node_ready(node: voltricx.Node):
    print(f"✅ Node {node.identifier!r} connected")

@bot.event
async def on_voltricx_track_start(player: voltricx.Player, track: voltricx.Playable):
    if player.home:
        embed = discord.Embed(
            title="🎵 Now Playing",
            description=f"**{track.title}**\nby {track.author}",
            color=0x7c3aed,
        )
        if track.artwork:
            embed.set_thumbnail(url=track.artwork)
        embed.add_field(
            name="Duration",
            value=f"{track.length // 60000}:{(track.length // 1000) % 60:02d}" if not track.is_stream else "🔴 LIVE",
        )
        embed.add_field(name="Source", value=track.source.capitalize())
        await player.home.send(embed=embed)

@bot.event
async def on_voltricx_inactive_player(player: voltricx.Player):
    if player.home:
        await player.home.send("💤 Left the channel due to inactivity.")
    await player.disconnect()

@bot.event
async def on_command_error(ctx: commands.Context, error: Exception):
    error = getattr(error, "original", error)
    if isinstance(error, voltricx.VoltricxException):
        await ctx.send(f"❌ **Music Error**: {error}")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Missing argument: `{error.param.name}`")
    elif not isinstance(error, commands.CommandNotFound):
        raise error


# ── Helper ─────────────────────────────────────────────────────────────────
def get_player(ctx: commands.Context) -> voltricx.Player | None:
    return ctx.voice_client  # type: ignore


# ── Commands ───────────────────────────────────────────────────────────────
@bot.command()
async def join(ctx: commands.Context):
    """Join your voice channel."""
    if not ctx.author.voice:
        return await ctx.send("❌ You must be in a voice channel.")
    if ctx.voice_client:
        return await ctx.send("Already connected.")
    player: voltricx.Player = await ctx.author.voice.channel.connect(cls=voltricx.Player)
    player.home = ctx.channel
    player.inactive_timeout = 300  # 5 minutes
    await ctx.send(f"✅ Joined **{ctx.author.voice.channel.name}**")


@bot.command(aliases=["p"])
async def play(ctx: commands.Context, *, query: str):
    """Play a track or add it to the queue."""
    if not ctx.author.voice:
        return await ctx.send("❌ Join a voice channel first!")

    if not ctx.voice_client:
        player: voltricx.Player = await ctx.author.voice.channel.connect(cls=voltricx.Player)
        player.home = ctx.channel
        player.inactive_timeout = 300
    else:
        player: voltricx.Player = ctx.voice_client

    async with ctx.typing():
        results = await voltricx.Pool.fetch_tracks(query)

    if not results:
        return await ctx.send(f"❌ No results for `{query}`")

    if isinstance(results, voltricx.Playlist):
        count = player.queue.put(results)
        await ctx.send(f"📋 Added playlist **{results.name}** ({count} tracks)")
    else:
        track = results[0]
        player.queue.put(track)
        await ctx.send(f"➕ Added **{track.title}** to queue")

    if not player.playing:
        await player.play(player.queue.get())


@bot.command(aliases=["s"])
async def skip(ctx: commands.Context):
    """Skip the current track."""
    player = get_player(ctx)
    if not player:
        return await ctx.send("❌ Not in a voice channel.")
    old = player.current
    await player.skip()
    await ctx.send(f"⏭️ Skipped **{old.title if old else 'track'}**")


@bot.command()
async def pause(ctx: commands.Context):
    """Pause playback."""
    player = get_player(ctx)
    if player:
        await player.pause(True)
        await ctx.send("⏸️ Paused.")


@bot.command()
async def resume(ctx: commands.Context):
    """Resume playback."""
    player = get_player(ctx)
    if player:
        await player.pause(False)
        await ctx.send("▶️ Resumed.")


@bot.command(aliases=["vol"])
async def volume(ctx: commands.Context, level: int):
    """Set volume (0–1000)."""
    player = get_player(ctx)
    if player:
        await player.set_volume(level)
        await ctx.send(f"🔊 Volume: **{level}%**")


@bot.command(aliases=["np"])
async def nowplaying(ctx: commands.Context):
    """Show current track with progress bar."""
    player = get_player(ctx)
    if not player or not player.current:
        return await ctx.send("Nothing is playing.")

    track = player.current
    pos, length = player.position, track.length
    filled = int((pos / length) * 20) if length else 0
    bar = "▬" * filled + "🔘" + "▬" * max(0, 20 - filled)

    fmt = lambda ms: f"{ms // 60000}:{(ms // 1000) % 60:02d}"

    embed = discord.Embed(
        title="🎵 Now Playing",
        description=f"**[{track.title}]({track.uri})**\nby {track.author}",
        color=0x7c3aed,
    )
    embed.add_field(
        name="Progress",
        value=f"`{fmt(pos)}` {bar} `{fmt(length)}`",
        inline=False,
    )
    embed.add_field(name="Volume", value=f"{player.volume}%")
    embed.add_field(name="Queue", value=f"{len(player.queue)} tracks")
    if track.artwork:
        embed.set_thumbnail(url=track.artwork)
    await ctx.send(embed=embed)


@bot.command(aliases=["q"])
async def queue(ctx: commands.Context):
    """Show the queue."""
    player = get_player(ctx)
    if not player or not player.queue:
        return await ctx.send("The queue is empty.")

    tracks = player.queue[0:10]
    lines = [f"`{i+1}.` {t.title}" for i, t in enumerate(tracks)]
    embed = discord.Embed(
        title=f"📋 Queue — {len(player.queue)} tracks",
        description="\n".join(lines),
        color=0x7c3aed,
    )
    if player.current:
        embed.set_author(name=f"▶ {player.current.title}")
    if len(player.queue) > 10:
        embed.set_footer(text=f"Showing 10/{len(player.queue)} tracks")
    await ctx.send(embed=embed)


@bot.command()
async def seek(ctx: commands.Context, position: str):
    """Seek to m:ss or seconds."""
    player = get_player(ctx)
    if not player:
        return
    try:
        if ":" in position:
            m, s = map(int, position.split(":"))
            ms = (m * 60 + s) * 1000
        else:
            ms = int(position) * 1000
        await player.seek(ms)
        await ctx.send(f"⏩ Seeked to `{position}`")
    except ValueError:
        await ctx.send("❌ Use `m:ss` or `seconds`")


@bot.command()
async def stop(ctx: commands.Context):
    """Stop and clear the queue."""
    player = get_player(ctx)
    if player:
        player.queue.clear()
        await player.stop()
        await ctx.send("⏹️ Stopped and cleared queue.")


@bot.command()
async def disconnect(ctx: commands.Context):
    """Disconnect from voice."""
    player = get_player(ctx)
    if player:
        await player.disconnect()
        await ctx.send("👋 Disconnected.")


@bot.command()
async def shuffle(ctx: commands.Context):
    """Shuffle the queue."""
    player = get_player(ctx)
    if player and player.queue:
        player.queue.shuffle()
        await ctx.send("🔀 Queue shuffled!")


@bot.command()
async def loop(ctx: commands.Context, mode: str = "normal"):
    """Set loop mode: normal, loop, loop_all."""
    player = get_player(ctx)
    if not player:
        return
    try:
        player.queue.mode = voltricx.QueueMode(mode.lower())
        await ctx.send(f"🔁 Loop mode: **{mode}**")
    except ValueError:
        await ctx.send("❌ Use: `normal`, `loop`, or `loop_all`")


@bot.command()
async def help(ctx: commands.Context):
    """Show all commands."""
    embed = discord.Embed(title="🎵 Voltricx Music Bot", color=0x7c3aed)
    embed.add_field(name="Playback", value=(
        "`!play <query>` `!skip` `!pause` `!resume`\n"
        "`!stop` `!seek <time>` `!volume <0-1000>`"
    ), inline=False)
    embed.add_field(name="Queue", value=(
        "`!queue` `!shuffle` `!loop <mode>`\n"
        "`!nowplaying` `!disconnect`"
    ), inline=False)
    await ctx.send(embed=embed)


bot.run(os.getenv("TOKEN"))
```
