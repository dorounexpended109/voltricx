---
title: Slash Commands Bot
description: A music bot using Discord slash commands with Voltricx.
---

# Slash Commands Bot

Modern Discord bots use slash commands (`/play`) instead of prefix commands (`!play`). Here's how to build a slash-command music bot with Voltricx.

```python title="slash_bot.py"
import os
import discord
from discord import app_commands
from dotenv import load_dotenv
import voltricx

load_dotenv()

# ── Bot Setup ──────────────────────────────────────────────────────────────
class SlashMusicBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.voice_states = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

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
            default_search_source="dzsearch",
        )
        await self.tree.sync()

    async def close(self):
        await voltricx.Pool.close()
        await super().close()


client = SlashMusicBot()


# ── Events ─────────────────────────────────────────────────────────────────
@client.event
async def on_ready():
    print(f"✅ {client.user} ready with slash commands")

@client.event
async def on_voltricx_track_start(player: voltricx.Player, track: voltricx.Playable):
    if player.home:
        await player.home.send(f"🎵 Now playing: **{track.title}**")

@client.event
async def on_voltricx_inactive_player(player: voltricx.Player):
    await player.disconnect()


# ── Helper: Ensure user is in a VC ────────────────────────────────────────
async def ensure_voice(interaction: discord.Interaction) -> voltricx.Player | None:
    """Connect if needed and return the player. Returns None if user not in VC."""
    if not interaction.user.voice:
        await interaction.response.send_message("❌ Join a voice channel first!", ephemeral=True)
        return None

    if interaction.guild.voice_client:
        return interaction.guild.voice_client  # type: ignore

    player: voltricx.Player = await interaction.user.voice.channel.connect(cls=voltricx.Player)
    player.home = interaction.channel
    player.inactive_timeout = 300
    return player


# ── Slash Commands ─────────────────────────────────────────────────────────
@client.tree.command(name="play", description="Search and play a track or playlist")
@app_commands.describe(query="Song name, URL, or search query")
async def play(interaction: discord.Interaction, query: str):
    await interaction.response.defer()

    player = await ensure_voice(interaction)
    if not player:
        return

    results = await voltricx.Pool.fetch_tracks(query)
    if not results:
        return await interaction.followup.send(f"❌ No results for `{query}`")

    if isinstance(results, voltricx.Playlist):
        count = player.queue.put(results)
        await interaction.followup.send(f"📋 Added **{results.name}** ({count} tracks)")
    else:
        track = results[0]
        player.queue.put(track)
        await interaction.followup.send(f"➕ Added **{track.title}** to queue")

    if not player.playing:
        await player.play(player.queue.get())


@client.tree.command(name="skip", description="Skip the current track")
async def skip(interaction: discord.Interaction):
    if not interaction.guild.voice_client:
        return await interaction.response.send_message("❌ Not in a voice channel.", ephemeral=True)
    player: voltricx.Player = interaction.guild.voice_client
    old = player.current
    await player.skip()
    await interaction.response.send_message(f"⏭️ Skipped **{old.title if old else 'track'}**")


@client.tree.command(name="pause", description="Pause or resume playback")
async def pause(interaction: discord.Interaction):
    player: voltricx.Player = interaction.guild.voice_client
    if not player:
        return await interaction.response.send_message("❌ Not connected.", ephemeral=True)
    new_state = not player.paused
    await player.pause(new_state)
    await interaction.response.send_message("⏸️ Paused" if new_state else "▶️ Resumed")


@client.tree.command(name="volume", description="Set the volume (0–1000)")
@app_commands.describe(level="Volume level (0 = mute, 100 = normal, 200 = double)")
async def volume(interaction: discord.Interaction, level: app_commands.Range[int, 0, 1000]):
    player: voltricx.Player = interaction.guild.voice_client
    if not player:
        return await interaction.response.send_message("❌ Not connected.", ephemeral=True)
    await player.set_volume(level)
    await interaction.response.send_message(f"🔊 Volume set to **{level}%**")


@client.tree.command(name="nowplaying", description="Show the currently playing track")
async def nowplaying(interaction: discord.Interaction):
    player: voltricx.Player = interaction.guild.voice_client
    if not player or not player.current:
        return await interaction.response.send_message("Nothing is playing.", ephemeral=True)

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
    embed.add_field(name="Progress", value=f"`{fmt(pos)}` {bar} `{fmt(length)}`", inline=False)
    embed.add_field(name="Volume", value=f"{player.volume}%")
    embed.add_field(name="Queue", value=f"{len(player.queue)} tracks")
    if track.artwork:
        embed.set_thumbnail(url=track.artwork)
    await interaction.response.send_message(embed=embed)


@client.tree.command(name="queue", description="Show the current queue")
async def queue(interaction: discord.Interaction):
    player: voltricx.Player = interaction.guild.voice_client
    if not player or not player.queue:
        return await interaction.response.send_message("Queue is empty.", ephemeral=True)

    tracks = player.queue[0:10]
    lines = [f"`{i+1}.` {t.title}" for i, t in enumerate(tracks)]
    embed = discord.Embed(
        title=f"📋 Queue — {len(player.queue)} tracks",
        description="\n".join(lines),
        color=0x7c3aed,
    )
    if player.current:
        embed.set_author(name=f"▶ {player.current.title}")
    await interaction.response.send_message(embed=embed)


@client.tree.command(name="filter", description="Apply an audio filter preset")
@app_commands.describe(preset="Choose a preset")
@app_commands.choices(preset=[
    app_commands.Choice(name="🌃 Nightcore",   value="nightcore"),
    app_commands.Choice(name="🌊 Vaporwave",   value="vaporwave"),
    app_commands.Choice(name="🎙️ 8D Audio",   value="8d"),
    app_commands.Choice(name="🔊 Bass Boost",  value="bassboost"),
    app_commands.Choice(name="🎤 Karaoke",     value="karaoke"),
    app_commands.Choice(name="✨ Reset",        value="reset"),
])
async def filter_cmd(interaction: discord.Interaction, preset: str):
    player: voltricx.Player = interaction.guild.voice_client
    if not player:
        return await interaction.response.send_message("❌ Not connected.", ephemeral=True)

    filters = player.filters

    if preset == "nightcore":
        filters.timescale.set(speed=1.3, pitch=1.3)
        label = "🌃 Nightcore"
    elif preset == "vaporwave":
        filters.timescale.set(speed=0.8, pitch=0.8)
        label = "🌊 Vaporwave"
    elif preset == "8d":
        filters.rotation.set(rotation_hz=0.2)
        label = "🎙️ 8D Audio"
    elif preset == "bassboost":
        for i in range(4):
            filters.equalizer.set_band(band=i, gain=0.25)
        label = "🔊 Bass Boost"
    elif preset == "karaoke":
        filters.karaoke.set(level=1.0, mono_level=1.0)
        label = "🎤 Karaoke"
    else:
        filters = voltricx.Filters()
        label = "✨ Reset"

    await player.set_filters(filters)
    await interaction.response.send_message(f"Applied filter: **{label}**")


@client.tree.command(name="disconnect", description="Disconnect the bot from voice")
async def disconnect(interaction: discord.Interaction):
    player: voltricx.Player = interaction.guild.voice_client
    if player:
        await player.disconnect()
    await interaction.response.send_message("👋 Disconnected.")


client.run(os.getenv("TOKEN"))
```
