# COM315ARENA

A competitive multiplayer arena game for COM315 Computer Networks.

The game server runs 24/7. Your assignment is to write a **TCP client** that connects to the server, joins the game, and competes for the highest score on the leaderboard.

**Server:** `<TBD>`
**Game Port:** `9000` (TCP)
**Spectator:** `http://<TBD>:9001` (watch the game live in your browser)

---

## The Game

You are a player on a 1200x900 arena. The arena has walls you can't pass through. Resources (gold) spawn on the map. Other players are trying to collect them too.

**You score points by:**
- Collecting a resource: **+10 points** (rare red resources: **+50**)
- Eliminating another player: **+50 points**

**You have fog of war** — you can only see players, resources, and projectiles within a limited radius around you. You do NOT see the entire map.

The server ticks ~15 times per second. Every tick, it sends you the game state. You read it, decide what to do, and send a command.

---

## Step 1: Connect and Join

Open a TCP socket and send `JOIN YourName\n`:

```python
import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(("SERVER_HOST", 9000))
sock.sendall(b"JOIN MyBot\n")
```

The server responds with a `WELCOME` message containing your player ID, starting position, map size, and the wall layout:

```
WELCOME {"id":5,"pos":[423.1,187.5],"map":[1200,900],"walls":[[580,430,40,40],[760,510,20,100],...]}
```

Each wall is `[x, y, width, height]` — a rectangle you can't move or shoot through.

---

## Step 2: Read Messages from the Server

The server continuously sends you newline-terminated messages. The most important one is `GAMESTATE`, which arrives every tick:

```
GAMESTATE {"tick":142,"you":{"pos":[423.1,187.5],"hp":100,"score":30,"cd":0,"alive":true},"players":[{"id":3,"name":"Alice","pos":[460.2,190.0],"hp":80}],"resources":[{"pos":[500.0,200.0],"v":10}],"projectiles":[]}
```

**Your state (`you`):**

| Field | Meaning |
|-------|---------|
| `pos` | Your `[x, y]` position on the map |
| `hp` | Your hit points (max 100). At 0 you die. |
| `score` | Your total score |
| `cd` | Shoot cooldown. **0 means you can fire.** |
| `alive` | `false` while dead (you auto-respawn after a few seconds) |

**What you can see** (only things within your visibility radius):

| Array | Each entry | Meaning |
|-------|-----------|---------|
| `players` | `{"id":3, "name":"Alice", "pos":[x,y], "hp":80}` | Another player near you |
| `resources` | `{"pos":[x,y], "v":10}` | A collectible. Walk over it to pick up. `v` is its point value. |
| `projectiles` | `{"pos":[x,y], "dir":[dx,dy], "own":3}` | A projectile in flight. `dir` is its normalized direction. `own` is the shooter's player ID. |

**Other messages the server sends:**

| Message | When |
|---------|------|
| `HIT 20 Alice` | You were hit for 20 damage by Alice |
| `DEATH Alice` | You were killed by Alice |
| `KILL Bob` | You killed Bob |
| `RESPAWN 300.0 450.0` | You respawned at that position |
| `CHAT Alice hello everyone` | Chat message from Alice |
| `ERROR some message` | Something went wrong |

---

## Step 3: Send Commands

Send newline-terminated commands to control your player:

| Command | Effect |
|---------|--------|
| `MOVE dx dy` | Start moving in direction (dx, dy). The server normalizes this to a unit vector — `MOVE 1 0`, `MOVE 100 0`, and `MOVE 0.5 0` all mean "move right." **You keep moving in this direction every tick until you send `STOP` or a new `MOVE`.** |
| `STOP` | Stop moving. |
| `SHOOT dx dy` | Fire a projectile in direction (dx, dy). Subject to cooldown — check `cd == 0` first. |
| `CHAT message` | Send a chat message to all players. |

---

## Critical Concept: TCP Framing

**TCP is a byte stream, not a message stream.** This is the single most important thing to get right.

When you call `sock.recv(4096)`, you might get:
- Multiple complete messages: `"GAMESTATE {...}\nHIT 20 Alice\nGAMESTATE {...}\n"`
- Only part of a message: `"GAMESTATE {\"tick\":14"`
- A mix: `"2,\"alive\":true}\nGAMESTATE {\"tick\":1"`

**You must buffer incoming data and split on `\n`.** Here is the correct pattern:

```python
buf = ""

def read_messages(sock):
    """Read from socket, buffer, yield complete messages."""
    global buf
    data = sock.recv(4096)
    if not data:
        return []  # server disconnected
    buf += data.decode()

    messages = []
    while "\n" in buf:
        line, buf = buf.split("\n", 1)
        line = line.strip()
        if line:
            messages.append(line)
    return messages
```

If you skip this and just do `sock.recv(4096).decode()`, your client **will break** when messages get split across recv calls.

---

## Minimal Working Client

This is the absolute minimum — connect, join, read state, call strategy, send command:

```python
import socket, json
from strategy import decide

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(("SERVER_HOST", 9000))
sock.sendall(b"JOIN MyBot\n")

buf = ""
while True:
    data = sock.recv(4096)
    if not data:
        break
    buf += data.decode()

    while "\n" in buf:
        line, buf = buf.split("\n", 1)
        line = line.strip()
        if not line:
            continue

        if line.startswith("GAMESTATE "):
            gs = json.loads(line[10:])
            command = decide(gs)
            if command:
                sock.sendall((command + "\n").encode())
```

This works but is single-threaded — it can't send while waiting for data. See `example_client.py` for a threaded version that handles concurrent I/O properly.

---

## The Strategy Module

The bot AI is provided for you as a pre-compiled module: **`strategy.py`**. It exports a single function:

```python
from strategy import decide

command = decide(game_state)  # returns "MOVE 1 0", "SHOOT 0 -1", or None
```

Pass it a parsed `GAMESTATE` dict. It returns a command string (or `None` if dead). **All players use the same AI.** You do not need to write game strategy code.

Your job is to write the **networking layer** around it:
- TCP connection and JOIN handshake
- Correct message framing (buffer + split on `\n`)
- Parsing server messages into dicts
- Sending the commands `decide()` returns
- Handling DEATH, RESPAWN, concurrent I/O

The competitive edge comes from **how well you understand and use the network**, not from writing a smarter bot brain. Think about what you learned in this course. The server has more going on than what's documented here.

---

## Game Rules

| Rule | Detail |
|------|--------|
| **HP** | 100 max. You die at 0. |
| **Regen** | HP regenerates slowly if you haven't been hit recently. |
| **Death** | You respawn after a few seconds. Your score is kept. |
| **Walls** | Block movement and projectiles. Your player slides along walls. |
| **Fog of war** | You can only see nearby entities. The full map is hidden. |
| **Shoot cooldown** | After firing, you must wait before firing again. Check `cd == 0`. |
| **Resources** | Gold (+10) spawns regularly. Rare red (+50) spawns less often. Walk over them to collect. |
| **Scoring** | Resources + kills. Scores persist across sessions. All-time leaderboard on the spectator page. |

---

## Grading

| Component | Weight |
|-----------|--------|
| **Working client** — TCP connection, JOIN handshake, correct message framing, parses GAMESTATE, sends commands, handles all message types | 50% |
| **Gameplay** — your bot connects, stays alive, and collects resources autonomously (the example strategy is sufficient) | 15% |
| **Code quality** — clean, readable, well-structured code with comments | 15% |
| **Bonus: networking exploits** — discover and document protocol-level advantages. Use what you know about TCP, packet analysis, and network protocols to gain an edge. | 20% |

**Note:** This assignment is about **networking**, not AI. You will not get extra credit for a fancier bot strategy. You **will** get extra credit for creative use of networking concepts — analyzing traffic, understanding the protocol deeply, and finding ways to gain information or capabilities that aren't obvious from this README alone.

---

## Hints

The game server is more than what's documented here. Some questions worth investigating:

- The `decide()` function returns **one** command per tick. Does the server only accept one?
- What ports is the server actually listening on? Have you checked all of them?
- What protocol does the spectator page use to get its data? Could your client use it too?
- What information does the spectator receive vs. what your TCP client receives?
- Is the server enforcing any kind of authentication or identity verification?
- What happens if you open more than one connection?
- Are `MOVE`, `STOP`, `SHOOT`, and `CHAT` the only commands the server understands?
- What can you learn by watching network traffic with Wireshark or tcpdump?
- Does `socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)` do anything useful?

You don't need to explore all of these. But this is where the bonus points are.

---

## Assignment Rules

- You may use **any programming language**. Python is recommended. Standard library only — no game/AI frameworks.
- You may **not** attack the server infrastructure (no denial-of-service, no port scanning beyond the game).
- You **may** use any protocol-level technique you discover. Sniffing traffic, opening multiple connections, probing undocumented features — all fair game. **Document what you find** for bonus credit.
- You **may** collaborate on ideas, but your code must be your own.
- You may **not** use, reference, or consult AI/LLM systems in any way for this assignment.

---

## Files

| File | What it is |
|------|-----------|
| `README.md` | This document |
| `strategy.py` | Pre-compiled strategy module. Provides `decide(game_state)`. All players use the same AI. |
| `example_client.py` | Working reference client showing TCP connection, framing, threading, and strategy integration. Read it, then write your own. |

---

## Quick Start Checklist

1. Read this README fully
2. Run `example_client.py` against the server to see it work
3. Open the spectator page in your browser to watch your bot play
4. Write your own client from scratch:
   - [ ] TCP connect to the server
   - [ ] Send `JOIN YourName\n`
   - [ ] Parse the `WELCOME` JSON response
   - [ ] Implement correct TCP framing (buffer + split on `\n`)
   - [ ] Parse `GAMESTATE` JSON each tick
   - [ ] Send `MOVE` / `SHOOT` / `STOP` commands
   - [ ] Handle `DEATH` and `RESPAWN` messages
   - [ ] Handle concurrent send/recv (threading or select)
5. Test your bot against the live server
6. Explore the network — what else is going on?
7. Submit your code + a short writeup of your approach and any discoveries
