---
title: Full Featured Bot
description: A production-ready music bot with all Voltricx features enabled.
---

# Full Featured Bot

This example is a production-ready bot covering all Voltricx features: multi-node, caching, autoplay, filters, history, and more.

See the [full source](https://github.com/revvlabs/voltricx/blob/main/full_test_bot.py) on GitHub for the complete code.

## Features Demonstrated

- ✅ Multi-node connection with regions
- ✅ HyperCache enabled
- ✅ Default search source
- ✅ Logger with debug output
- ✅ Track history & previous track command
- ✅ All audio filter presets
- ✅ AutoPlay modes
- ✅ Queue pagination
- ✅ Node info & cache inspection
- ✅ Inactivity timeout handling
- ✅ Failover event handling

## Bot Setup

```python title="full_bot.py (setup)"
import asyncio, os, discord
from discord.ext import commands
from dotenv import load_dotenv
import voltricx

load_dotenv()

class FullMusicBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.voice_states = True
        super().__init__(command_prefix="!", intents=intents, help_command=None)

    async def setup_hook(self):
        voltricx.voltricx_logger.enable()
        voltricx.voltricx_logger.set_level("INFO")

        nodes = []
        for i in range(1, 10):
            uri = os.getenv(f"NODE_{i}_URI")
            pwd = os.getenv(f"NODE_{i}_PASSWORD")
            region = os.getenv(f"NODE_{i}_REGION", "global")
            if uri and pwd:
                nodes.append(voltricx.NodeConfig(
                    identifier=f"Node-{i}",
                    uri=uri, password=pwd, region=region,
                ))

        await voltricx.Pool.connect(
            client=self,
            nodes=nodes,
            cache_config={"capacity": 100, "track_capacity": 1000},
            default_search_source="dzsearch",
        )

    async def close(self):
        await voltricx.Pool.close()
        await super().close()
```

## Event Handlers

```python title="full_bot.py (events)"
@bot.event
async def on_voltricx_track_start(player: voltricx.Player, track: voltricx.Playable):
    if player.home:
        await player.home.send(f"🎶 **Started**: {track.title}")

@bot.event
async def on_voltricx_track_end(player, track, reason):
    if player.home and str(reason) == "finished":
        await player.home.send(f"✅ **Finished**: {track.title}")

@bot.event
async def on_voltricx_track_exception(player, track, exception):
    if player.home:
        await player.home.send(f"⚠️ **Error** with {track.title}: `{exception}`")

@bot.event
async def on_voltricx_failover(old_node, new_node, players):
    for player in players:
        if player.home:
            await player.home.send(
                f"🔄 **Failover**: migrated to `{new_node.identifier}`"
            )

@bot.event
async def on_voltricx_inactive_player(player: voltricx.Player):
    if player.home:
        await player.home.send("💤 Leaving due to inactivity.")
    await player.disconnect()
```

## Playback Commands

```python title="full_bot.py (playback)"
@bot.command(aliases=["p"])
async def play(ctx: commands.Context, *, query: str):
    if not ctx.author.voice:
        return await ctx.send("❌ Join a voice channel!")
    if not ctx.voice_client:
        player: voltricx.Player = await ctx.author.voice.channel.connect(cls=voltricx.Player)
        player.home = ctx.channel
        player.inactive_timeout = 300
    else:
        player: voltricx.Player = ctx.voice_client

    results = await voltricx.Pool.fetch_tracks(query)
    if not results:
        return await ctx.send("❌ No results.")

    if isinstance(results, voltricx.Playlist):
        added = player.queue.put(results)
        await ctx.send(f"📋 Added **{results.name}** ({added} tracks)")
    else:
        track = results[0]
        player.queue.put(track)
        await ctx.send(f"➕ Added **{track.title}**")

    if not player.playing:
        await player.play(player.queue.get(), populate=True)


@bot.command()
async def previous(ctx: commands.Context):
    """Play the previous track."""
    player: voltricx.Player = ctx.voice_client
    if not player or not player.queue.history:
        return await ctx.send("No history.")
    try:
        player.queue.history.pop()
        prev = player.queue.history.pop()
        player.queue.put_at_front(prev)
        await player.skip(force=True)
        await ctx.send(f"⏪ Back to **{prev.title}**")
    except Exception:
        await ctx.send("No previous track.")
```

## Filter Commands

```python title="full_bot.py (filters)"
FILTER_PRESETS = {
    "nightcore": lambda f: f.timescale.set(speed=1.3, pitch=1.3),
    "vaporwave": lambda f: f.timescale.set(speed=0.8, pitch=0.8),
    "8d":        lambda f: f.rotation.set(rotation_hz=0.2),
    "chipmunk":  lambda f: f.timescale.set(speed=1.0, pitch=1.5),
    "deepvoice": lambda f: f.timescale.set(speed=1.0, pitch=0.6),
    "karaoke":   lambda f: f.karaoke.set(level=1.0, mono_level=1.0),
}

@bot.command()
async def filter(ctx: commands.Context, preset: str):
    """Apply a filter preset."""
    player: voltricx.Player = ctx.voice_client
    if not player:
        return
    preset = preset.lower()
    if preset not in FILTER_PRESETS and preset != "reset":
        return await ctx.send(f"Available: {', '.join(FILTER_PRESETS)} reset")

    filters = player.filters
    if preset == "reset":
        filters = voltricx.Filters()
    else:
        FILTER_PRESETS[preset](filters)

    await player.set_filters(filters)
    await ctx.send(f"🎛️ Filter: **{preset}**")

@bot.command()
async def bassboost(ctx: commands.Context):
    """Toggle bass boost."""
    player: voltricx.Player = ctx.voice_client
    if not player:
        return
    filters = player.filters
    if any(filters.equalizer.payload[i]["gain"] > 0 for i in range(4)):
        filters.equalizer.reset()
        await ctx.send("Bass Boost **OFF**")
    else:
        for i in range(4):
            filters.equalizer.set_band(band=i, gain=0.25)
        await ctx.send("🔊 Bass Boost **ON**")
    await player.set_filters(filters)
```

## System Commands

```python title="full_bot.py (system)"
@bot.command()
async def nodeinfo(ctx: commands.Context):
    """Show all node stats."""
    nodes = voltricx.Pool.nodes()
    lines = []
    for ident, node in nodes.items():
        icon = "✅" if node.status == voltricx.NodeStatus.connected else "❌"
        cpu = f"{node.stats_cpu.system_load * 100:.1f}%" if node.stats_cpu else "N/A"
        mem = f"{node.stats_memory.used / 1024 / 1024:.1f} MB" if node.stats_memory else "N/A"
        lines.append(f"{icon} **{ident}**: {node.playing_count} players | CPU {cpu} | Mem {mem}")

    embed = discord.Embed(title="🖥️ Node Status", description="\n".join(lines), color=0x7c3aed)
    await ctx.send(embed=embed)

@bot.command()
async def cache(ctx: commands.Context):
    """Show HyperCache stats."""
    stats = voltricx.Pool.get_cache_stats()
    await ctx.send(
        f"🚀 **HyperCache**\n"
        f"• L1 (Queries): `{stats['l1_queries']}`\n"
        f"• L2 (Tracks): `{stats['l2_tracks']}`"
    )

@bot.command()
async def autoplay(ctx: commands.Context, mode: str = "partial"):
    """Set autoplay mode: enabled, partial, disabled."""
    player: voltricx.Player = ctx.voice_client
    if not player:
        return
    try:
        amode = voltricx.AutoPlayMode(mode.lower())
        player.autoplay = amode
        await ctx.send(f"AutoPlay: **{amode.value}**")
    except ValueError:
        await ctx.send("Use: `enabled`, `partial`, or `disabled`")
```
