# COM315ARENA

A competitive multiplayer arena game for COM315 Computer Networks. The game server is running 24/7. Your job is to write a **TCP client** that connects, joins the match, and competes for the highest score.

**Server:** `<TBD>`
**Game Port:** `9000` (TCP)
**Spectator:** `http://<TBD>:9001` (open in browser to watch live)

## The Game

You control a player on a 1200x900 arena with walls. Score points by:
- **Collecting resources** that spawn on the map (+10 each, +50 for rare red ones)
- **Eliminating other players** with projectiles (+50 per kill)

You have limited visibility — you can only see what's near you. The full map is hidden.

## Connecting

Open a TCP socket to the server and send your JOIN message:

```
JOIN YourName\n
```

The server responds with your player info and the map layout:

```
WELCOME {"id":5,"pos":[150.0,200.0],"map":[1200,900],"walls":[[x,y,w,h],...]}
```

**Important: TCP is a byte stream.** A single `recv()` may return multiple messages, or only part of one. You **must** buffer incoming data and split on `\n` boundaries. If you don't handle this, your client will break.

## Commands

Send these as newline-terminated strings:

| Command | What it does |
|---------|-------------|
| `MOVE dx dy` | Start moving in direction `(dx, dy)`. Server normalizes to unit vector. You keep moving until you send `STOP` or a new `MOVE`. |
| `STOP` | Stop moving. |
| `SHOOT dx dy` | Fire a projectile in direction `(dx, dy)`. Has a cooldown between shots. |
| `CHAT message` | Send a message to all players. |

## Game State

Every tick (~15/sec) the server sends you:

```
GAMESTATE {"tick":100,"you":{...},"players":[...],"resources":[...],"projectiles":[...]}
```

### Your state (`you`):

| Field | Meaning |
|-------|---------|
| `pos` | Your `[x, y]` position |
| `hp` | Hit points (max 100) |
| `score` | Your total score |
| `cd` | Shoot cooldown (0 = ready to fire) |
| `alive` | `false` while dead and waiting to respawn |

### What you can see (limited by visibility radius):

- **`players`** — nearby enemies: `{"id":3, "name":"Alice", "pos":[x,y], "hp":100}`
- **`resources`** — collectible items: `{"pos":[x,y], "v":10}` — walk over to collect
- **`projectiles`** — in-flight shots: `{"pos":[x,y], "dir":[dx,dy], "own":3}`

## Events

The server also sends these as they happen:

| Message | Meaning |
|---------|---------|
| `HIT damage attacker_name` | You were hit |
| `DEATH killer_name` | You died (auto-respawn after a few seconds) |
| `KILL victim_name` | You eliminated someone |
| `RESPAWN x y` | You respawned at position (x, y) |
| `ERROR message` | Something went wrong |
| `CHAT sender_name message` | Chat from another player |

## Game Rules

- **Health:** 100 HP max. Regenerates slowly after not taking damage.
- **Death:** At 0 HP you die and respawn after a short delay. Score is kept.
- **Walls:** Block movement and projectiles. You slide along walls.
- **Fog of war:** Limited visibility radius. You cannot see the entire map.
- **Cooldown:** After firing, wait before firing again (`cd` field in game state).

## Example Client

`example_client.py` is a working starter bot. It connects, wanders, collects resources, and shoots at enemies:

```bash
python3 example_client.py <host> <port> <your_name>
```

Use it as a reference. Build something smarter.

## Grading

| Component | Weight |
|-----------|--------|
| Working client (connects, authenticates, moves, collects) | 40% |
| Autonomous bot strategy | 20% |
| Code quality and documentation | 20% |
| Bonus: creative exploits, documented findings | 20% |

## Tips

1. Start simple: connect, JOIN, move toward resources.
2. Handle TCP framing correctly (buffer + split on `\n`).
3. Add enemy avoidance and combat.
4. Think about what information you have access to — and what you don't.
5. Read the traffic. Observe the protocol. What else is the server doing?

## Rules

- You may use **any programming language**. Python recommended. Standard library only.
- You may **not** attack the server infrastructure itself (no DoS, no port scanning beyond the game ports).
- You **may** exploit any protocol-level vulnerabilities you discover in the game. Document what you find.
- Have fun.
