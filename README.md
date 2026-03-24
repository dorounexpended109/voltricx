<div align="center">
  <img src="https://raw.githubusercontent.com/revvlabs/revvcore/refs/heads/main/assets/banner.svg" width="100%" alt="Voltricx Banner">
  
  <h3>The Next-Generation Lavalink Wrapper for Python</h3>

  <p align="center">
    <a href="https://pypi.org/project/testvoltricx/" style="text-decoration:none;"><img src="https://img.shields.io/pypi/v/testvoltricx?style=for-the-badge&logo=pypi&color=blue" alt="PyPI version"></a>
    <a href="https://pypi.org/project/testvoltricx/" style="text-decoration:none;"><img src="https://img.shields.io/badge/python-3.12%20|%203.13-3776AB?style=for-the-badge&logo=python" alt="Python versions"></a>
    <a href="LICENSE" style="text-decoration:none;"><img src="https://img.shields.io/badge/license-MIT-blue?style=for-the-badge" alt="License"></a>
    <img src="https://img.shields.io/badge/Status-Stable-brightgreen?style=for-the-badge" alt="Status">
  </p>

  <p align="center">
    <a href="https://lavalink.dev"><img src="https://img.shields.io/badge/Lavalink-v4.0%2B-FB7713?style=flat-square&logo=lavalink" alt="Lavalink version"></a>
    <img src="https://img.shields.io/badge/Plugins-Native_Support-FB7713?style=flat-square" alt="Plugins Support">
  </p>

  <p align="center">
    <a href="https://ded-lmfao.github.io/revvcore/"><img src="https://img.shields.io/github/actions/workflow/status/revvlabs/revvcore/deploy-docs.yml?branch=main&label=Docs&logo=readthedocs&style=flat-square" alt="Docs"></a>
    <a href="https://github.com/revvlabs/revvcore/actions/workflows/version_checks.yml"><img src="https://img.shields.io/github/actions/workflow/status/revvlabs/revvcore/version_checks.yml?branch=main&label=Version%20Checks&logo=githubactions&style=flat-square" alt="Version Checks"></a>
    <a href="https://github.com/revvlabs/revvcore/actions/workflows/version_checks.yml"><img src="https://img.shields.io/github/actions/workflow/status/revvlabs/revvcore/version_checks.yml?branch=main&label=Ruff&logo=ruff&style=flat-square" alt="Ruff Checks"></a>
    <a href="https://github.com/revvlabs/revvcore/actions/workflows/version_checks.yml"><img src="https://img.shields.io/github/actions/workflow/status/revvlabs/revvcore/version_checks.yml?branch=main&label=Pyright&logo=python&style=flat-square" alt="Pyright"></a>
    <a href="https://github.com/revvlabs/revvcore/actions/workflows/version_checks.yml"><img src="https://img.shields.io/github/actions/workflow/status/revvlabs/revvcore/version_checks.yml?branch=main&label=Pytest&logo=pytest&style=flat-square" alt="Pytest"></a>
  </p>


  <p align="center">
    <a href="https://github.com/revvlabs/revvcore/actions/workflows/build_and_publish.yml"><img src="https://github.com/revvlabs/revvcore/actions/workflows/build_and_publish.yml/badge.svg" alt="Publish to PyPI"></a>
  </p>


  <p align="center">
    <img src="https://raw.githubusercontent.com/revvlabs/revvcore/shield-stats/assets/quality_gate.svg" alt="Quality Gate">
    <img src="https://raw.githubusercontent.com/revvlabs/revvcore/shield-stats/assets/coverage.svg" alt="Coverage">
    <img src="https://raw.githubusercontent.com/revvlabs/revvcore/shield-stats/assets/bugs.svg" alt="Bugs">
    <img src="https://raw.githubusercontent.com/revvlabs/revvcore/shield-stats/assets/vulnerabilities.svg" alt="Vulnerabilities">
    <img src="https://raw.githubusercontent.com/revvlabs/revvcore/shield-stats/assets/code_smells.svg" alt="Code Smells">
  </p>
</div>

---

**Voltricx** is a high-performance, feature-rich Lavalink wrapper built for modern Discord bot development in Python. Engineered for speed, reliability, and ease of use, Voltricx offers a professional-grade API that makes audio integration seamless and powerful.

---

## <img src="https://raw.githubusercontent.com/revvlabs/revvcore/refs/heads/main/assets/logo.svg" width="32" align="center" alt="Icon"> Table of Contents
- [Why Voltricx?](#why-voltricx)
- [Features](#features)
- [Installation](#installation)
- [Quickstart](#quickstart)
- [Examples](#examples)
- [Contributing](#contributing)
- [License](#license)

---

### <img src="https://raw.githubusercontent.com/revvlabs/revvcore/refs/heads/main/assets/logo.svg" width="32" align="center" alt="Icon"> Why Voltricx?

<table border="0">
  <tr>
    <td width="52" valign="middle"><img src="https://raw.githubusercontent.com/revvlabs/revvcore/refs/heads/main/assets/logo.svg" width="44" alt="Icon"></td>
    <td valign="middle"><strong>Next-Gen Performance</strong>: Dual-tier caching (LRU/LFU) powered by <code>HyperCache</code> for lightning-fast data retrieval.</td>
  </tr>
  <tr>
    <td width="52" valign="middle"><img src="https://raw.githubusercontent.com/revvlabs/revvcore/refs/heads/main/assets/logo.svg" width="44" alt="Icon"></td>
    <td valign="middle"><strong>Strictly Typed</strong>: Comprehensive type hinting and Pydantic v2 validation ensure your code is robust and maintainable.</td>
  </tr>
  <tr>
    <td width="52" valign="middle"><img src="https://raw.githubusercontent.com/revvlabs/revvcore/refs/heads/main/assets/logo.svg" width="44" alt="Icon"></td>
    <td valign="middle"><strong>High-Fidelity Failover</strong>: Automated node shifting and silent reconnects ensure a seamless listening experience.</td>
  </tr>
  <tr>
    <td width="52" valign="middle"><img src="https://raw.githubusercontent.com/revvlabs/revvcore/refs/heads/main/assets/logo.svg" width="44" alt="Icon"></td>
    <td valign="middle"><strong>Modern Standards</strong>: Fully compatible with Lavalink v4.0+, including native support for the DAVE E2EE protocol and filters.</td>
  </tr>
  <tr>
    <td width="52" valign="middle"><img src="https://raw.githubusercontent.com/revvlabs/revvcore/refs/heads/main/assets/logo.svg" width="44" alt="Icon"></td>
    <td valign="middle"><strong>Smart Load Balancing</strong>: Advanced penalty-based node selection for optimal performance across multiple Lavalink nodes.</td>
  </tr>
</table>

---

### <img src="https://raw.githubusercontent.com/revvlabs/revvcore/refs/heads/main/assets/logo.svg" width="32" align="center" alt="Icon"> Features

- 🚀 **Asynchronous Architecture**: Built from the ground up to be fully async and non-blocking.
- 📡 **Websocket Management**: Efficient handling of Lavalink websocket connections with automatic retries.
- 🎹 **Rich Audio Control**: Full support for filters including Equalizer, Timescale, Vibrato, and more.
- 🌐 **DAVE Protocol**: Support for the latest Discord Audio Video Encryption standards.
- ⚖️ **Regional Selection**: Intelligent node selection based on guild region and node latency.

---

### <img src="https://raw.githubusercontent.com/revvlabs/revvcore/refs/heads/main/assets/logo.svg" width="32" align="center" alt="Icon"> Installation

Voltricx requires **Python 3.12+**.

```bash
# Stable version from PyPI
pip install voltricx
```

For the latest development version:
```bash
pip install git+https://github.com/revvlabs/voltricx.git
```

---

### <img src="https://raw.githubusercontent.com/revvlabs/revvcore/refs/heads/main/assets/logo.svg" width="32" align="center" alt="Icon"> Quickstart

Here is a minimal example of how to get up and running with Voltricx.

```python
import discord
from discord.ext import commands
import voltricx

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all())

    async def setup_hook(self):
        # Configuration for your Lavalink Node
        config = voltricx.NodeConfig(
            uri="http://localhost:2333",
            password="youshallnotpass",
            identifier="MAIN-NODE"
        )

        # Initialize the Pool and add the node
        node = voltricx.Node(config=config)
        await voltricx.Pool.add_node(node)

bot = MyBot()

@bot.event
async def on_voltricx_node_ready(node: voltricx.Node):
    print(f"✅ Lavalink Node {node.identifier} is ready and connected!")

@bot.command()
async def play(ctx, *, query: str):
    # Retrieve or create a player for the guild
    player: voltricx.Player = ctx.voice_client or await ctx.author.voice.channel.connect(cls=voltricx.Player)

    # Search for tracks
    tracks = await voltricx.Pool.get_tracks(query)
    if not tracks:
        return await ctx.send("❌ No tracks found.")

    track = tracks[0]
    await player.play(track)
    await ctx.send(f"🎶 **Now playing**: {track.title}")

bot.run("YOUR_BOT_TOKEN")
```

---

### <img src="https://raw.githubusercontent.com/revvlabs/revvcore/refs/heads/main/assets/logo.svg" width="32" align="center" alt="Icon"> Examples

Check the [example](example/) directory for advanced usage, including:
- [Basic Bot Implementation](example/main.py)
- Custom Queue Handlers
- Advanced Filters (Nightcore, etc.)

---

### <img src="https://raw.githubusercontent.com/revvlabs/revvcore/refs/heads/main/assets/logo.svg" width="32" align="center" alt="Icon"> Contributing

We welcome contributions! If you'd like to help improve Voltricx:
1. **Fork** the repository.
2. **Clone** your fork and create a new feature branch (`git checkout -b feature/amazing-feature`).
3. **Commit** your improvements (`git commit -m 'feat: add some amazing feature'`).
4. **Push** the changes to your fork (`git push origin feature/amazing-feature`).
5. **Open a Pull Request**.

---

### <img src="https://raw.githubusercontent.com/revvlabs/revvcore/refs/heads/main/assets/logo.svg" width="32" align="center" alt="Icon"> License

Voltricx is released under the MIT License. See [LICENSE](LICENSE) for more information.
