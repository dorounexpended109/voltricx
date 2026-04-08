---
title: Installation
description: How to install Voltricx and its dependencies.
---

# Installation

Voltricx supports Python **3.12 and above** and Lavalink **v4.x**.

## Prerequisites

Before installing Voltricx you will need:

- **Python 3.12+** — [Download Python](https://www.python.org/downloads/)
- **A running Lavalink server** — [Lavalink Setup Guide](lavalink-setup.md)
- **discord.py 2.0+** — installed as a dependency automatically

## Install via pip

The simplest installation method:

```bash
pip install voltricx
```

!!! tip "Virtual Environments"
    It is best practice to install packages inside a virtual environment.
    ```bash
    python -m venv .venv
    source .venv/bin/activate   # Linux / macOS
    .venv\Scripts\activate      # Windows
    pip install voltricx
    ```

## Install from Source (Development)

If you want the latest unreleased changes or plan to contribute:

```bash
git clone https://github.com/revvlabs/voltricx
cd voltricx
pip install -e .
```

The `-e` flag installs in *editable mode*, meaning code changes are reflected immediately without reinstalling.

## Dependencies

Voltricx will automatically install all required packages:

| Package | Version | Purpose |
|---------|---------|---------|
| `discord.py` | ≥ 2.0.0 | Discord bot framework |
| `pydantic` | ≥ 2.0.0 | Data validation and models |
| `aiohttp` | ≥ 3.8.0 | Async HTTP client for REST requests |
| `yarl` | ≥ 1.9.0 | URL parsing |
| `python-dotenv` | ≥ 1.0.0 | Environment variable loading |

## Optional Dependencies

### DAVE Protocol (E2EE Audio)

To enable support for Discord's Audio Video Encryption protocol:

```bash
pip install davey
```

!!! note
    DAVE support is optional. Voltricx works perfectly without it. Only install `davey` if your use case requires end-to-end encrypted voice sessions.

## Verify Installation

After installing, verify everything works:

```python
import voltricx
print(voltricx.__version__)
```

## Next Steps

- [Configure a Lavalink server →](lavalink-setup.md)
- [Read the Quick Start guide →](quickstart.md)
