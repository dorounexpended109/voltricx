---
title: Lavalink Setup
description: How to install and run a Lavalink server for Voltricx.
---

# Lavalink Server Setup

Voltricx requires a running **Lavalink v4** server to handle audio streaming. This page walks you through setting one up.

## What is Lavalink?

[Lavalink](https://github.com/lavalink-devs/Lavalink) is a standalone audio-sending node based on [Lavaplayer](https://github.com/lavalink-devs/lavaplayer). Instead of processing audio inside your bot, the heavy lifting is offloaded to Lavalink — freeing your bot to handle more requests with less CPU overhead.

## Requirements

- **Java 17+** (Java 21 LTS recommended)
- At least **256 MB of RAM** (512 MB recommended)
- Network access for audio sources

## Download

Download the latest `Lavalink.jar` from the [official GitHub releases](https://github.com/lavalink-devs/Lavalink/releases):

```bash
wget https://github.com/lavalink-devs/Lavalink/releases/latest/download/Lavalink.jar
```

## Configure `application.yml`

Create an `application.yml` in the same directory as `Lavalink.jar`:

```yaml title="application.yml"
server:
  port: 2333
  address: 0.0.0.0

lavalink:
  server:
    password: "youshallnotpass"   # Change this!
    sources:
      youtube: true
      bandcamp: true
      soundcloud: true
      twitch: true
      vimeo: true
      http: true
      local: false
    filters:
      volume: true
      equalizer: true
      karaoke: true
      timescale: true
      tremolo: true
      vibrato: true
      distortion: true
      rotation: true
      channelMix: true
      lowPass: true
    bufferDurationMs: 400
    frameBufferDurationMs: 5000
    opusEncodingQuality: 10
    resamplingQuality: LOW
    trackStuckThresholdMs: 10000
    playerUpdateInterval: 5
    youtubeSearchEnabled: true
    soundcloudSearchEnabled: true

metrics:
  prometheus:
    enabled: false

sentry:
  dsn: ""

logging:
  file:
    path: ./logs/

  level:
    root: INFO
    lavalink: INFO
```

!!! warning "Change the password"
    Always change `youshallnotpass` to a strong, unique password before deploying to production.

## Start Lavalink

```bash
java -jar Lavalink.jar
```

You should see output similar to:

```
INFO lavalink: Starting Lavalink
INFO lavalink: Lavalink is ready to accept connections.
```

## Run with Docker

For production deployments, Docker is recommended:

```yaml title="docker-compose.yml"
version: "3.8"
services:
  lavalink:
    image: ghcr.io/lavalink-devs/lavalink:4
    container_name: lavalink
    restart: unless-stopped
    environment:
      - SERVER_PORT=2333
      - LAVALINK_SERVER_PASSWORD=youshallnotpass
    volumes:
      - ./application.yml:/opt/Lavalink/application.yml
    ports:
      - "2333:2333"
    networks:
      - bot-network

networks:
  bot-network:
    driver: bridge
```

```bash
docker-compose up -d
```

## Multiple Nodes

Voltricx supports connecting to **multiple Lavalink nodes** for load balancing and failover. Simply run additional Lavalink instances on different ports or hosts and register each one in your `Pool.connect()` call.

```python
await voltricx.Pool.connect(
    client=bot,
    nodes=[
        voltricx.NodeConfig(identifier="US-East",   uri="http://lavalink1:2333", password="..."),
        voltricx.NodeConfig(identifier="EU-West",   uri="http://lavalink2:2333", password="...", region="eu")
    ]
)
```

## Verify Connection

Once Lavalink is running, use this snippet to confirm Voltricx can connect:

```python
import asyncio
import discord
import voltricx

async def main():
    client = discord.Client(intents=discord.Intents.default())
    async with client:
        await client.login("YOUR_TOKEN")
        nodes = await voltricx.Pool.connect(
            client=client,
            nodes=[voltricx.NodeConfig(
                identifier="Test",
                uri="http://localhost:2333",
                password="youshallnotpass",
            )]
        )
        print("Connected nodes:", list(nodes.keys()))

asyncio.run(main())
```

## Next Steps

- [Configuration reference →](configuration.md)
- [Quick Start guide →](quickstart.md)
