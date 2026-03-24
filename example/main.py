# The MIT License (MIT)
#
# Copyright (c) 2026-Present @JustNixx, @Dipendra-creator and RevvLabs
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import os
from typing import TYPE_CHECKING, Any, cast

import discord
from discord.ext import commands
from dotenv import load_dotenv

import voltricx

if TYPE_CHECKING:
    from voltricx import Player

# --- CONFIGURATION ---
load_dotenv()
TOKEN = os.getenv("TOKEN")


class FullTestBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.voice_states = True
        super().__init__(command_prefix="!", intents=intents, help_command=None)

    async def setup_hook(self):
        nodes = []
        for i in range(1, 10):
            uri = os.getenv(f"NODE_{i}_URI")
            password = os.getenv(f"NODE_{i}_PASSWORD")
            region = os.getenv(f"NODE_{i}_REGION", "global")

            if uri and password:
                nodes.append(
                    voltricx.NodeConfig(
                        identifier=f"Node-{i}",
                        uri=uri,
                        password=password,
                        region=region,
                    )
                )

        if not nodes:
            print("No nodes found in .env!")
            return

        try:
            # Enable library logging for better visibility
            voltricx.voltricx_logger.enable()
            voltricx.voltricx_logger.set_level("DEBUG")

            # Connect with cache enabled to test get_cache_stats
            await voltricx.Pool.connect(
                client=self,
                nodes=nodes,
                cache_config={"capacity": 100, "track_capacity": 1000},
                default_search_source="dzsearch",
            )
            print(f"Lavalink Pool connected with {len(nodes)} nodes.")
        except Exception as e:
            print(f"Failed to connect: {e}")

    async def close(self):
        print("Shutting down...")
        await voltricx.Pool.close()
        await super().close()

    # --- Voltricx Event Listeners ---

    async def on_voltricx_node_ready(self, node: voltricx.Node):
        print(f"Event: Node {node.identifier} is READY.")

    async def on_voltricx_track_start(self, player: voltricx.Player, track: voltricx.Playable):
        print(f"Event: Track started in {player.guild.id}: {track.title}")
        if player.home:
            await player.home.send(f"🎶 **Started playing**: {track.title}")

    async def on_voltricx_track_end(
        self, player: voltricx.Player, track: voltricx.Playable, reason: Any
    ):
        print(f"Event: Track ended in {player.guild.id}: {track.title} (Reason: {reason})")
        if player.home and reason == "finished":
            await player.home.send(f"🏁 **Finished playing**: {track.title}")

    async def on_voltricx_track_exception(
        self, player: voltricx.Player, track: voltricx.Playable, exception: Any
    ):
        print(f"Event: Track exception in {player.guild.id}: {exception}")
        if player.home:
            ex_str = str(exception)
            if len(ex_str) > 1500:
                ex_str = ex_str[:1500] + "..."
            await player.home.send(f"⚠️ **Track Error**: {track.title}\n`{ex_str}`")

    async def on_voltricx_track_stuck(
        self, player: voltricx.Player, track: voltricx.Playable, threshold: int
    ):
        print(f"Event: Track stuck in {player.guild.id} (threshold: {threshold})")

    async def on_voltricx_websocket_closed(
        self, player: voltricx.Player, code: int, reason: str, remote: bool
    ):
        print(f"Event: WebSocket closed in {player.guild.id}. Code: {code}, Reason: {reason}")

    async def on_voltricx_node_disconnected(self, node: voltricx.Node):
        print(f"Event: Node {node.identifier} DISCONNECTED.")

    async def on_voltricx_failover(
        self,
        old_node: voltricx.Node,
        new_node: voltricx.Node,
        players: list[voltricx.Player],
    ):
        print(
            f"Event: Failover! Migrated {len(players)} players from {old_node.identifier} to {new_node.identifier}."
        )
        for player in players:
            if player.home:
                await player.home.send(
                    f"🔄 **Failover**: Migrated session to `{new_node.identifier}` due to `{old_node.identifier}` disconnecting."
                )

    async def on_voltricx_node_stats(self, node: voltricx.Node):
        print(f"Event: Node {node.identifier} stats updated.")


bot = FullTestBot()


@bot.event
async def on_ready():
    print(f"Full Test Bot Logged in as {bot.user}")


@bot.event
async def on_command_error(ctx: commands.Context, error: Exception):
    """Global error handler for Voltricx specific exceptions."""
    # Unwrap CommandInvokeError
    actual_error = getattr(error, "original", error)

    if isinstance(actual_error, voltricx.VoltricxException):
        return await ctx.send(f"❌ **Voltricx Error**: {actual_error}")

    await ctx.send(f"❌ **Error**: {actual_error}")


# --- Node & System Commands ---


@bot.command()
async def node_version(ctx: commands.Context):
    """Fetch the version of the first connected node."""
    node = voltricx.Pool.get_node()
    ver = await node.fetch_version()
    await ctx.send(f"🌐 **Node {node.identifier} Version**: `{ver}`")


@bot.command()
async def node_stats(ctx: commands.Context):
    """Fetch real-time stats from the node."""
    node = voltricx.Pool.get_node()
    stats = await node.fetch_stats()
    msg = (
        f"📊 **Node {node.identifier} Stats**\n"
        f"• Players: {stats.get('players', 0)} ({stats.get('playingPlayers', 0)} playing)\n"
        f"• Uptime: {stats.get('uptime', 0) // 1000}s\n"
        f"• CPU Cores: {stats.get('cpu', {}).get('cores', 0)}"
    )
    await ctx.send(msg)


@bot.command()
async def decode(ctx: commands.Context, encoded: str):
    """Decode a base64 track string."""
    node = voltricx.Pool.get_node()
    track = await node.decode_track(encoded)
    await ctx.send(f"🔓 **Decoded**: {track.title} by {track.author}")


@bot.command()
async def refresh_info(ctx: commands.Context):
    """Refresh node information."""
    node = voltricx.Pool.get_node()
    info = await node.fetch_info()
    await ctx.send(f"🔄 **Refreshed {node.identifier}**: Lavalink v{info.version.semver}")


@bot.command()
async def routeplanner(ctx: commands.Context):
    """Fetch route planner status."""
    node = voltricx.Pool.get_node()
    status = await node.fetch_routeplanner_status()
    if not status:
        return await ctx.send("RoutePlanner not enabled or not supported on this node.")
    await ctx.send(f"🗺️ **RoutePlanner**: {status.class_}")


@bot.command()
async def free_addr(ctx: commands.Context, address: str):
    """Free a specific address in RoutePlanner."""
    node = voltricx.Pool.get_node()
    await node.free_address(address)
    await ctx.send(f"✅ Freed address: `{address}`")


@bot.command()
async def free_all_addrs(ctx: commands.Context):
    """Free all addresses in RoutePlanner."""
    node = voltricx.Pool.get_node()
    await node.free_all_addresses()
    await ctx.send("✅ Freed all addresses.")


# --- Playback Commands ---


@bot.command(name="join")
async def join(ctx: commands.Context):
    """Joins the voice channel."""
    if not ctx.author.voice:
        return await ctx.send("Join a VC!")

    if not ctx.voice_client:
        player: Player = await cast(discord.VoiceChannel, ctx.author.voice.channel).connect(
            cls=voltricx.Player
        )
        player.home = ctx.channel
        await ctx.send(f"Connected to **{ctx.author.voice.channel.name}**")
    else:
        await ctx.send("Already connected.")


@bot.command(name="play", aliases=["p"])
async def play(ctx: commands.Context, *, query: str):
    """Play a track and add it to the queue."""
    if not ctx.author.voice:
        return await ctx.send("Join a VC!")

    if not ctx.voice_client:
        player: Player = await cast(discord.VoiceChannel, ctx.author.voice.channel).connect(
            cls=voltricx.Player
        )
        player.home = ctx.channel
    else:
        player = cast("Player", ctx.voice_client)

    # Test cache and different sources (Pool now handles default dzsearch)
    tracks = await voltricx.Pool.fetch_tracks(query)
    if not tracks:
        return await ctx.send(f"No results for: `{query}`")

    if isinstance(tracks, voltricx.Playlist):
        added = player.queue.put(tracks)
        await ctx.send(f"Added playlist **{tracks.name}** ({added} tracks)")
    else:
        track = cast(voltricx.Playable, tracks[0])
        player.queue.put(track)
        await ctx.send(f"Added **{track.title}** to queue.")

    if not player.playing:
        await player.play(player.queue.get())


@bot.command(name="search")
async def search(ctx: commands.Context, *, query: str):
    """Searches for a song and displays the first 10 results."""
    # We use fetch_tracks directly to show results
    tracks = await voltricx.Pool.fetch_tracks(f"dzsearch:{query}")
    if not tracks:
        return await ctx.send(f"No results for: `{query}`")

    if isinstance(tracks, voltricx.Playlist):
        return await ctx.send(
            f"Query returned a playlist: **{tracks.name}**. Use `!play` to add it."
        )

    titles = "\n".join([f"{i + 1}. {t.title} - {t.author}" for i, t in enumerate(tracks[:10])])
    await ctx.send(f"🔎 **Search Results**:\n{titles}\n\n*Use `!play <title>` to add one.*")


@bot.command(name="skip", aliases=["s", "next"])
async def skip(ctx: commands.Context):
    """Skip the current track."""
    if not ctx.voice_client:
        return

    player = cast("Player", ctx.voice_client)
    await player.skip()
    await ctx.send("⏭️ Skipped!")


@bot.command()
async def previous(ctx: commands.Context):
    """Play the previous track from history."""
    if not ctx.voice_client:
        return

    player = cast("Player", ctx.voice_client)
    if not player.queue.history:
        return await ctx.send("No history.")

    # To go back, we must pop current track AND the previous one
    try:
        _ = player.queue.history.pop()  # Current
        track = player.queue.history.pop()  # Previous
    except Exception:
        return await ctx.send("No previous track in history.")

    player.queue.put_at_front(track)
    await player.skip(force=True)
    await ctx.send(f"⏪ Back to: **{track.title}**")


@bot.command(name="karaoke")
async def karaoke(ctx: commands.Context):
    """Toggle karaoke filter."""
    if not ctx.voice_client:
        return

    player: voltricx.Player = ctx.voice_client
    filters = player.filters

    if filters.karaoke and filters.karaoke.level > 0:
        filters.karaoke.level = 0.0
        await ctx.send("Karaoke OFF")
    else:
        filters.karaoke = voltricx.Karaoke(level=1.0, mono_level=1.0)
        await ctx.send("Karaoke ON")

    await player.set_filters(filters)


@bot.command(name="bassboost")
async def bassboost(ctx: commands.Context):
    """Toggle the Bass Boost filter."""
    if not ctx.voice_client:
        return

    player: voltricx.Player = ctx.voice_client
    filters = player.filters

    # Simple Bass Boost: increase lower bands
    # Bands 0, 1, 2, 3 are typically bass
    for i in range(4):
        filters.equalizer.set_band(band=i, gain=0.25)

    await player.set_filters(filters)
    await ctx.send("🔊 Bass Boost **ON**")


@bot.command(name="nightcore")
async def nightcore(ctx: commands.Context):
    """Toggle the Nightcore filter (High speed, high pitch)."""
    if not ctx.voice_client:
        return

    player: voltricx.Player = ctx.voice_client
    filters = player.filters

    if filters.timescale and filters.timescale.speed > 1.0:
        filters.timescale.reset()
        await ctx.send("Nightcore **OFF**")
    else:
        filters.timescale.set(speed=1.3, pitch=1.3)
        await ctx.send("Nightcore **ON** (Speed/Pitch: 1.3x)")

    await player.set_filters(filters)


@bot.command(name="vaporwave")
async def vaporwave(ctx: commands.Context):
    """Toggle the Vaporwave filter (Low speed, low pitch)."""
    if not ctx.voice_client:
        return

    player: voltricx.Player = ctx.voice_client
    filters = player.filters

    if filters.timescale and filters.timescale.speed < 1.0:
        filters.timescale.reset()
        await ctx.send("Vaporwave **OFF**")
    else:
        filters.timescale.set(speed=0.8, pitch=0.8)
        await ctx.send("Vaporwave **ON** (Speed/Pitch: 0.8x)")

    await player.set_filters(filters)


@bot.command(name="8d")
async def eight_d(ctx: commands.Context):
    """Toggle the 8D Audio filter (Rotation)."""
    if not ctx.voice_client:
        return

    player: voltricx.Player = ctx.voice_client
    filters = player.filters

    if filters.rotation and filters.rotation.rotation_hz > 0:
        filters.rotation.reset()
        await ctx.send("8D Audio **OFF**")
    else:
        filters.rotation.set(rotation_hz=0.2)
        await ctx.send("8D Audio **ON**")

    await player.set_filters(filters)


@bot.command(name="chipmunk")
async def chipmunk(ctx: commands.Context):
    """Toggle the Chipmunk filter (High pitch, normal speed)."""
    if not ctx.voice_client:
        return

    player: voltricx.Player = ctx.voice_client
    filters = player.filters

    if filters.timescale and filters.timescale.pitch > 1.0 and filters.timescale.speed == 1.0:
        filters.timescale.reset()
        await ctx.send("Chipmunk **OFF**")
    else:
        filters.timescale.set(speed=1.0, pitch=1.5)
        await ctx.send("Chipmunk **ON** (Pitch: 1.5x)")

    await player.set_filters(filters)


@bot.command(name="deepvoice")
async def deepvoice(ctx: commands.Context):
    """Toggle the Deep Voice filter (Low pitch, normal speed)."""
    if not ctx.voice_client:
        return

    player: voltricx.Player = ctx.voice_client
    filters = player.filters

    if filters.timescale and filters.timescale.pitch < 1.0 and filters.timescale.speed == 1.0:
        filters.timescale.reset()
        await ctx.send("Deep Voice **OFF**")
    else:
        filters.timescale.set(speed=1.0, pitch=0.6)
        await ctx.send("Deep Voice **ON** (Pitch: 0.6x)")

    await player.set_filters(filters)


@bot.command(name="reset")
async def reset_filters(ctx: commands.Context):
    """Reset all filters back to none."""
    if not ctx.voice_client:
        return

    await ctx.voice_client.set_filters(voltricx.Filters())
    await ctx.send("✨ Filters **RESET** to default.")


@bot.command()
async def tremolo(ctx: commands.Context, freq: float = 2.0, depth: float = 0.5):
    """Set tremolo filter."""
    if not ctx.voice_client:
        return
    player: voltricx.Player = ctx.voice_client
    filters = player.filters
    filters.tremolo.set(frequency=freq, depth=depth)
    await player.set_filters(filters)
    await ctx.send(f"📳 Tremolo ON (freq: {freq}, depth: {depth})")


@bot.command()
async def vibrato(ctx: commands.Context, freq: float = 2.0, depth: float = 0.5):
    """Set vibrato filter."""
    if not ctx.voice_client:
        return
    player: voltricx.Player = ctx.voice_client
    filters = player.filters
    filters.vibrato.set(frequency=freq, depth=depth)
    await player.set_filters(filters)
    await ctx.send(f"🎻 Vibrato ON (freq: {freq}, depth: {depth})")


@bot.command()
async def distortion(ctx: commands.Context):
    """Set a preset distortion filter."""
    if not ctx.voice_client:
        return
    player: voltricx.Player = ctx.voice_client
    filters = player.filters
    filters.distortion.set(
        sin_offset=0,
        sin_scale=1,
        cos_offset=0,
        cos_scale=1,
        tan_offset=0,
        tan_scale=1,
        offset=0,
        scale=1,
    )
    await player.set_filters(filters)
    await ctx.send("😵 Distortion ON")


@bot.command()
async def lowpass(ctx: commands.Context, smoothing: float = 20.0):
    """Set low pass filter."""
    if not ctx.voice_client:
        return
    player: voltricx.Player = ctx.voice_client
    filters = player.filters
    filters.low_pass.set(smoothing=smoothing)
    await player.set_filters(filters)
    await ctx.send(f"🔅 Low Pass ON (smoothing: {smoothing})")


@bot.command()
async def mono(ctx: commands.Context):
    """Set channel mix to mono."""
    if not ctx.voice_client:
        return
    player: voltricx.Player = ctx.voice_client
    filters = player.filters
    filters.channel_mix.set(
        left_to_left=0.5, left_to_right=0.5, right_to_left=0.5, right_to_right=0.5
    )
    await player.set_filters(filters)
    await ctx.send("📻 Mono mode ON")


@bot.command()
async def pause(ctx: commands.Context):
    """Pause playback."""
    if ctx.voice_client:
        await ctx.voice_client.pause(True)
        await ctx.send("Paused.")


@bot.command()
async def resume(ctx: commands.Context):
    """Resume playback."""
    if ctx.voice_client:
        await ctx.voice_client.pause(False)
        await ctx.send("Resumed.")


# --- Advanced Modes ---


@bot.command()
async def loop(ctx: commands.Context, mode: str = "normal"):
    """Set queue loop mode: normal, loop, loop_all."""
    if not ctx.voice_client:
        return

    try:
        qmode = voltricx.QueueMode(mode.lower())
        ctx.voice_client.queue.mode = qmode
        await ctx.send(f"Queue mode set to: **{qmode.name}**")
    except ValueError:
        await ctx.send("Invalid mode. Use: `normal`, `loop`, or `loop_all`.")


@bot.command()
async def autoplay(ctx: commands.Context, mode: str = "disabled"):
    """Set autoplay mode: enabled, partial, disabled."""
    if not ctx.voice_client:
        return

    try:
        amode = voltricx.AutoPlayMode(mode.lower())
        ctx.voice_client.autoplay = amode
        await ctx.send(f"Autoplay set to: **{amode.name}**")
    except ValueError:
        await ctx.send("Invalid mode. Use: `enabled`, `partial`, or `disabled`.")


# --- Data Inspection ---


@bot.command()
async def help(ctx: commands.Context):
    """Show all commands and their usage."""
    help_text = (
        "**Music Commands**\n"
        "`!play <query>` | `!search <query>` | `!join` | `!pause`/`!resume` | `!skip` | `!previous` | `!replay` | `!stop` | `!seek <time>` | `!volume <v>` | `!disconnect` | `!random` \n\n"
        "**Queue Commands**\n"
        "`!queue` | `!nowplaying` | `!remove <idx>` | `!clearqueue` | `!shuffle` | `!loop <mode>` | `!autoplay <mode>` | `!move <i1> <i2>` | `!swap <i1> <i2>` | `!peek <n>` | `!history` | `!upcoming` \n\n"
        "**Filter Commands**\n"
        "`!bassboost` | `!nightcore` | `!vaporwave` | `!8d` | `!chipmunk` | `!deepvoice` | `!tremolo` | `!vibrato` | `!distortion` | `!lowpass` | `!mono` | `!reset` \n\n"
        "**System Commands**\n"
        "`!cache` | `!cache_list` | `!export_cache` | `!nodeinfo` | `!node_version` | `!node_stats` | `!decode <b64>` | `!refresh_info` | `!routeplanner` | `!free_addr` | `!free_all_addrs` | `!status` "
    )
    await ctx.send(help_text)


@bot.command()
async def status(ctx: commands.Context):
    """Show detailed player state."""
    if not ctx.voice_client:
        return await ctx.send("Not connected.")

    player = cast("Player", ctx.voice_client)
    # Use getattr to be safe if properties are missing
    current_title = player.current.title if player.current else "None"

    msg = (
        f"**Playing**: {current_title}\n"
        f"**Original**: {getattr(player, '_original', None).title if getattr(player, '_original', None) else 'None'}\n"
        f"**Loop Mode**: {player.queue.mode}\n"
        f"**AutoPlay**: {player.autoplay}\n"
        f"**Volume**: {player.volume}%\n"
        f"**Paused**: {player.paused}"
    )
    await ctx.send(msg)


@bot.command()
async def upcoming(ctx: commands.Context, limit: int = 10):
    """Show upcoming tracks in the deque."""
    if not ctx.voice_client:
        return

    q = ctx.voice_client.queue
    if not q:
        return await ctx.send("Queue is empty.")

    count = min(limit, len(q))
    tracks = q[0:count]
    titles = "\n".join([f"{i + 1}. {t.title}" for i, t in enumerate(tracks)])
    await ctx.send(f"📜 **Upcoming Tracks ({len(q)} total)**:\n{titles}")


@bot.command()
async def history(ctx: commands.Context, limit: int = 10):
    """Show track history from the history deque."""
    if not ctx.voice_client:
        return

    h = ctx.voice_client.queue.history
    if not h:
        return await ctx.send("History is empty.")

    # History is also a deque, we display most recent first
    count = min(limit, len(h))
    tracks = list(reversed(h))[:count]
    titles = "\n".join([f"{i + 1}. {t.title}" for i, t in enumerate(tracks)])
    await ctx.send(f"🕒 **Recent History ({len(h)} total)**:\n{titles}")


@bot.command()
async def cache(ctx: commands.Context):
    """Show HyperCache statistics."""
    stats = voltricx.Pool.get_cache_stats()
    msg = (
        f"🚀 **HyperCache Stats**\n"
        f"• L1 (Queries): {stats['l1_queries']}\n"
        f"• L2 (Tracks): {stats['l2_tracks']}"
    )
    await ctx.send(msg)


@bot.command()
async def cache_list(ctx: commands.Context):
    """Show detailed HyperCache entries."""
    entries = voltricx.Pool.get_cache_entries()
    if not entries:
        return await ctx.send("Cache is empty.")

    msg = "**📂 HyperCache Entries**\n"
    for query, titles in entries.items():
        tracks_str = ", ".join(titles[:3])
        if len(titles) > 3:
            tracks_str += f" (+{len(titles) - 3} more)"
        msg += f"• `{query}` -> {tracks_str}\n"

    # Check for message length
    if len(msg) > 2000:
        msg = msg[:1990] + "..."
    await ctx.send(msg)


@bot.command()
async def nodeinfo(ctx: commands.Context):
    """Show detailed node statistics."""
    nodes = voltricx.Pool.nodes()
    if not nodes:
        return await ctx.send("No nodes found.")

    lines = []
    for ident, node in nodes.items():
        status = "✅" if node.status == voltricx.NodeStatus.connected else "❌"
        # Node statistics if available
        cpu = f"{node.stats_cpu.system_load * 100:.1f}%" if node.stats_cpu else "N/A"
        mem = f"{node.stats_memory.used / 1024 / 1024:.1f} MB" if node.stats_memory else "N/A"
        lines.append(f"{status} **{ident}**: {node.playing_count} players, CPU: {cpu}, Mem: {mem}")

    await ctx.send("**Node Overview**:\n" + "\n".join(lines))


@bot.command()
async def peek(ctx: commands.Context, amount: int = 2):
    """Verify deque slicing by peeking at N tracks."""
    if not ctx.voice_client:
        return

    q = ctx.voice_client.queue
    if not q:
        return await ctx.send("Queue is empty.")

    count = min(amount, len(q))
    tracks = q[:count]

    if not isinstance(tracks, list):
        tracks = [tracks]

    titles = "\n".join([f"{i + 1}. {t.title}" for i, t in enumerate(tracks)])
    await ctx.send(f"👀 **Peeked {len(tracks)} tracks**:\n{titles}")


@bot.command()
async def shuffle(ctx: commands.Context):
    """Shuffle the current queue."""
    if ctx.voice_client:
        ctx.voice_client.queue.shuffle()
        await ctx.send("🔀 Queue shuffled!")


@bot.command(name="queue", aliases=["q"])
async def queue(ctx: commands.Context, limit: int = 10):
    """Displays the current song queue."""
    if not ctx.voice_client:
        return

    q = ctx.voice_client.queue
    if not q:
        return await ctx.send("Queue is empty.")

    count = min(limit, len(q))
    tracks = q[0:count]
    titles = "\n".join([f"{i + 1}. {t.title}" for i, t in enumerate(tracks)])

    embed = discord.Embed(
        title=f"Queue ({len(q)} tracks)",
        description=titles,
        color=discord.Color.green(),
    )
    if len(q) > limit:
        embed.set_footer(text=f"Showing {limit} of {len(q)} tracks.")
    await ctx.send(embed=embed)


@bot.command()
async def remove(ctx: commands.Context, index: int):
    """Removes a song from the queue by its index."""
    if not ctx.voice_client:
        return

    q = ctx.voice_client.queue
    try:
        # Indices are 1-based for users
        track = q[index - 1]
        del q[index - 1]
        await ctx.send(f"Removed **{track.title}** from queue.")
    except IndexError:
        await ctx.send("Invalid index.")


@bot.command()
async def clearqueue(ctx: commands.Context):
    """Clears the entire song queue."""
    if ctx.voice_client:
        ctx.voice_client.queue.clear()
        await ctx.send("🗑️ Queue cleared!")


@bot.command()
async def move(ctx: commands.Context, from_idx: int, to_idx: int):
    """Move a track in the queue."""
    if not ctx.voice_client:
        return
    q = ctx.voice_client.queue
    try:
        track = q[from_idx - 1]
        del q[from_idx - 1]
        q.put_at(to_idx - 1, track)
        await ctx.send(f"🚚 Moved **{track.title}** to position {to_idx}")
    except IndexError:
        await ctx.send("Invalid index.")


@bot.command()
async def swap(ctx: commands.Context, idx1: int, idx2: int):
    """Swap two tracks in the queue."""
    if not ctx.voice_client:
        return
    q = ctx.voice_client.queue
    try:
        q.swap(idx1 - 1, idx2 - 1)
        await ctx.send(f"🔄 Swapped tracks at {idx1} and {idx2}")
    except IndexError:
        await ctx.send("Invalid index.")


@bot.command()
async def random(ctx: commands.Context):
    """Play a random track from the global cache."""
    track = voltricx.Pool.get_random_cached_track()
    if not track:
        return await ctx.send("No tracks in cache yet. Play something first!")

    if not ctx.voice_client:
        await ctx.invoke(join)

    player: Player = cast("Player", ctx.voice_client)
    player.queue.put(track)
    await ctx.send(f"🎲 Random from cache: **{track.title}**")
    if not player.playing:
        await player.play(player.queue.get())


@bot.command()
async def export_cache(ctx: commands.Context):
    """Export raw cache data."""
    data = voltricx.Pool.export_cache_data()
    l1_count = len(data.get("l1", {}))
    l2_count = len(data.get("l2", {}))
    await ctx.send(f"📦 **Cache Export Summary**: L1={l1_count} queries, L2={l2_count} tracks.")


@bot.command()
async def stop(ctx: commands.Context):
    """Stops the current song and clears the queue."""
    if ctx.voice_client:
        ctx.voice_client.queue.clear()
        await ctx.voice_client.stop()
        await ctx.send("Stopped and cleared queue.")


@bot.command(name="nowplaying", aliases=["np"])
async def nowplaying(ctx: commands.Context):
    """Displays the current song playing with a progress bar."""
    if not ctx.voice_client or not ctx.voice_client.current:
        return await ctx.send("Nothing playing.")

    player = cast("Player", ctx.voice_client)
    track = player.current

    # Simple progress bar
    pos = player.position
    length = track.length
    bar_len = 20
    filled = int((pos / length) * bar_len) if length > 0 else 0
    bar = "▬" * filled + "🔘" + "▬" * max(0, bar_len - filled)

    time_pos = f"{pos // 60000}:{(pos // 1000) % 60:02d}"
    time_len = f"{length // 60000}:{(length // 1000) % 60:02d}"

    embed = discord.Embed(
        title="Now Playing",
        description=f"[{track.title}]({track.uri})",
        color=discord.Color.blue(),
    )
    embed.add_field(name="Progress", value=f"`{time_pos}` {bar} `{time_len}`", inline=False)
    await ctx.send(embed=embed)


@bot.command()
async def replay(ctx: commands.Context):
    """Replays the current song."""
    if not ctx.voice_client:
        return

    if ctx.voice_client.current:
        await ctx.voice_client.seek(0)
        await ctx.send("Replaying current track...")
    elif ctx.voice_client.queue.loaded:
        await ctx.voice_client.play(ctx.voice_client.queue.loaded)
        await ctx.send("Replaying last loaded track...")
    else:
        await ctx.send("No track to replay.")


@bot.command()
async def seek(ctx: commands.Context, position: str):
    """Seeks to a specific time in the song (e.g. 1:30 or 90)."""
    if not ctx.voice_client:
        return

    # Parse m:ss or ss
    try:
        if ":" in position:
            m, s = map(int, position.split(":"))
            ms = (m * 60 + s) * 1000
        else:
            ms = int(position) * 1000

        await ctx.voice_client.seek(ms)
        await ctx.send(f"Seeked to `{position}`")
    except ValueError:
        await ctx.send("Invalid format. Use `m:ss` or `seconds`.")


@bot.command(name="volume", aliases=["vol"])
async def volume(ctx: commands.Context, value: int):
    """Adjusts the bot's volume (0-1000)."""
    if ctx.voice_client:
        await ctx.voice_client.set_volume(value)
        await ctx.send(f"Volume set to **{value}%**")


@bot.command()
async def disconnect(ctx: commands.Context):
    """Disconnect and cleanup."""
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("Disconnected.")


if __name__ == "__main__":
    bot.run(TOKEN)
