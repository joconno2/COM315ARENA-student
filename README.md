# COM315ARENA — Programming Assignment 5

**Server:** `<TBD>:9000`
**Spectator:** `http://<TBD>:9001`

Write a TCP client that connects to the game server, joins the arena, and competes on the leaderboard.

## Protocol

All messages are UTF-8 text, delimited by `\n`. The server listens on TCP port 9000.

### Handshake

Send `JOIN <name>\n`. Server responds with `WELCOME <json>\n`.

The JSON contains your player `id`, starting `pos`, `map` dimensions, and `walls` (rectangles as `[x, y, w, h]`).

### Commands you can send

    MOVE <dx> <dy>
    STOP
    SHOOT <dx> <dy>
    CHAT <message>

Direction vectors are normalized by the server.

### Messages you'll receive

    GAMESTATE <json>       (every tick)
    HIT <damage> <name>
    DEATH <name>
    KILL <name>
    RESPAWN <x> <y>
    CHAT <name> <message>
    ERROR <message>

### GAMESTATE format

```json
{
  "tick": 142,
  "you": {"pos": [x,y], "hp": 100, "score": 0, "cd": 0, "alive": true},
  "players": [{"id": 3, "name": "Alice", "pos": [x,y], "hp": 80}],
  "resources": [{"pos": [x,y], "v": 10}],
  "projectiles": [{"pos": [x,y], "dir": [dx,dy], "own": 3}]
}
```

You can only see entities within a limited radius.

## Rules

- 100 HP. Regen after not taking damage. Respawn on death.
- Resources spawn periodically. Walk over them to collect. Gold = +10, red = +50.
- Kills = +50. Projectiles have a cooldown (`cd` field).
- Walls block movement and projectiles.
- Scores persist. Leaderboard is on the spectator page.

## Strategy Module

`strategy.py` provides `decide(game_state)` — pass it a parsed GAMESTATE dict, it returns a command string. All players use the same AI. Your job is the networking.

## Grading

| | |
|-|-|
| **Working client** — TCP connection, protocol handling, message parsing | 50% |
| **Gameplay** — bot plays autonomously using the provided strategy | 15% |
| **Code quality** | 15% |
| **Bonus** — documented networking discoveries | 20% |

This is a networking assignment, not an AI assignment. The strategy module is the same for everyone. Your score depends on how well you handle the network.

## Deliverables

- Your client source code
- Short writeup: how your client works, and anything you discovered about the server

## Rules

- Any language. Standard library only.
- No AI/LLM usage.
- Do not DoS the server.
