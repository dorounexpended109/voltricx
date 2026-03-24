---
title: Connecting Nodes
description: How to manage Lavalink nodes with the Pool — connection, failover, and load balancing.
---

# Connecting Nodes

## The Pool

`Pool` is the **central orchestrator** in Voltricx. It manages all Lavalink node connections, handles failover, and performs load balancing automatically.

```python
import voltricx

# Single node
await voltricx.Pool.connect(
    client=bot,
    nodes=[
        voltricx.NodeConfig(identifier="Main", uri="http://localhost:2333", password="pass")
    ]
)

# Multiple nodes with regions
await voltricx.Pool.connect(
    client=bot,
    nodes=[
        voltricx.NodeConfig(identifier="US",   uri="http://us.node:2333",  password="pass", region="us"),
        voltricx.NodeConfig(identifier="EU",   uri="http://eu.node:2333",  password="pass", region="eu")
    ]
)
```

After connection, Pool prints a status report to the console:

```
[Lavalink] Node connection report (3/3 connected)

  [CONNECTED] US         http://us.node:2333            region=us
  [CONNECTED] EU         http://eu.node:2333            region=eu
  [CONNECTED] Asia       http://asia.node:2333          region=asia
```

---

## Node Status

A `Node` can be in one of three states:

| Status | Enum | Meaning |
|--------|------|---------|
| Connected | `NodeStatus.connected` | Node is online and accepting requests |
| Connecting | `NodeStatus.connecting` | Handshake in progress |
| Disconnected | `NodeStatus.disconnected` | Node is offline or unreachable |

```python
from voltricx import NodeStatus

node = voltricx.Pool.get_node("Main")
if node.status == NodeStatus.connected:
    print("Node is healthy!")
```

---

## Node Selection & Load Balancing

`Pool.get_node()` uses a **penalty scoring system** to select the healthiest node:

```python
# Automatic selection (lowest penalty score)
node = voltricx.Pool.get_node()

# By identifier
node = voltricx.Pool.get_node("EU")

# By region (closest healthy node in that region)
node = voltricx.Pool.get_node(region="eu")
```

### Penalty Formula

The penalty score is calculated from three components:

```
penalty = CPU_penalty + FrameDeficit_penalty + FrameNulled_penalty + Player_penalty
```

| Component | Formula |
|-----------|---------|
| CPU | `(1.05 ^ (100 × system_load) × 10) − 10` |
| Frame deficit | `(1.03 ^ (500 × deficit / 3000) × 300) − 300` |
| Frame nulled | `(1.03 ^ (500 × nulled / 3000) × 300) − 300) × 2` |
| Players | `playing_count × 1.5` |

A node that is **disconnected** gets a penalty of `9e30` (effectively infinite), so it's never selected.

---

## Node Events

Listen to node lifecycle events with discord.py's event system:

```python
@bot.event
async def on_voltricx_node_ready(node: voltricx.Node):
    print(f"✅ Node {node.identifier} connected")

@bot.event
async def on_voltricx_node_disconnected(node: voltricx.Node):
    print(f"❌ Node {node.identifier} disconnected")
```

---

## Automatic Failover

When a node disconnects, Voltricx automatically migrates all its players to the next healthiest node:

```python
@bot.event
async def on_voltricx_failover(
    old_node: voltricx.Node,
    new_node: voltricx.Node,
    players: list[voltricx.Player]
):
    print(f"Migrated {len(players)} players from {old_node.identifier} → {new_node.identifier}")
    for player in players:
        if player.home:
            await player.home.send(
                f"⚠️ Server failover — migrated to `{new_node.identifier}`"
            )
```

The failover logic:

1. Waits up to 5 seconds for a healthy node to appear
2. Selects the node with the lowest penalty score
3. Migrates each player individually, accounting for region preferences
4. Resumes playback from the current track position

---

## Fetching Node Info

```python
node = voltricx.Pool.get_node("Main")

# Fetch Lavalink server info
info = await node.fetch_info()
print(info.version.semver)       # e.g. "4.0.8"
print(info.source_managers)      # ["youtube", "soundcloud", ...]

# Fetch stats
stats = await node.fetch_stats()

# Fetch version string
version = await node.fetch_version()
```

---

## Route Planner

The Lavalink RoutePlanner is used with rotating IP addresses for YouTube API compliance:

```python
# Check status
status = await node.fetch_routeplanner_status()
if status:
    print(f"Type: {status.cls}")

# Unmark a specific failing IP
await node.free_address("1.2.3.4")

# Reset all failing IPs
await node.free_all_addresses()
```

---

## Listing All Nodes

```python
all_nodes = voltricx.Pool.nodes()
for identifier, node in all_nodes.items():
    print(f"{identifier}: {node.status.value} ({len(node.players)} players)")
```

---

## Shutting Down

Always call `Pool.close()` before your bot exits to cleanly destroy all players and close WebSocket connections:

```python
async def close(self):
    await voltricx.Pool.close()
    await super().close()
```
