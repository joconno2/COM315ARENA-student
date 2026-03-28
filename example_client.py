#!/usr/bin/env python3
"""COM315ARENA — minimal example client.

Usage:  python3 simple_client.py <host> <port> <name>

This bot wanders randomly and shoots at nearby enemies.
Students should use this as a starting point and build a smarter strategy.
"""

import json
import math
import random
import socket
import sys
import threading
import time


def recv_loop(sock, state):
    """Background thread: continuously reads server messages."""
    buf = ""
    while True:
        try:
            data = sock.recv(4096)
            if not data:
                print("[!] Server closed connection.")
                state["running"] = False
                return
            buf += data.decode(errors="replace")
        except (ConnectionError, OSError):
            state["running"] = False
            return

        while "\n" in buf:
            line, buf = buf.split("\n", 1)
            line = line.strip()
            if not line:
                continue

            if line.startswith("WELCOME "):
                info = json.loads(line[8:])
                state["id"] = info["id"]
                state["map"] = info["map"]
                state["walls"] = info["walls"]
                print(f"[*] Joined as player {info['id']} at ({info['pos'][0]}, {info['pos'][1]})")

            elif line.startswith("GAMESTATE "):
                state["game"] = json.loads(line[10:])

            elif line.startswith("HIT "):
                parts = line.split(maxsplit=2)
                print(f"[!] Hit for {parts[1]} damage by {parts[2]}")

            elif line.startswith("DEATH "):
                print(f"[X] Killed by {line[6:]}")

            elif line.startswith("KILL "):
                print(f"[*] You killed {line[5:]}!")

            elif line.startswith("RESPAWN "):
                parts = line.split()
                print(f"[*] Respawned at ({parts[1]}, {parts[2]})")

            elif line.startswith("CHAT "):
                parts = line.split(maxsplit=2)
                if len(parts) >= 3:
                    print(f"[chat] {parts[1]}: {parts[2]}")

            elif line.startswith("ERROR "):
                print(f"[!] {line}")


def send(sock, msg):
    sock.sendall((msg + "\n").encode())


def main():
    if len(sys.argv) < 4:
        print(f"Usage: {sys.argv[0]} <host> <port> <name>")
        sys.exit(1)

    host, port, name = sys.argv[1], int(sys.argv[2]), sys.argv[3]

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    print(f"[*] Connected to {host}:{port}")

    send(sock, f"JOIN {name}")

    state = {"running": True, "game": None, "id": None, "map": None}
    t = threading.Thread(target=recv_loop, args=(sock, state), daemon=True)
    t.start()

    # wait for welcome
    while state["id"] is None and state["running"]:
        time.sleep(0.05)

    if not state["running"]:
        return

    print("[*] Playing!  Ctrl+C to quit.")

    while state["running"]:
        time.sleep(0.1)  # ~10 decisions per second
        gs = state.get("game")
        if not gs:
            continue

        me = gs["you"]
        if not me["alive"]:
            continue

        mx, my = me["pos"]
        players = gs.get("players", [])
        resources = gs.get("resources", [])

        # ── strategy: shoot nearest enemy, move toward nearest resource ──

        # shoot at closest visible enemy
        if players and me["cd"] == 0:
            closest = min(players, key=lambda p: math.hypot(p["pos"][0] - mx, p["pos"][1] - my))
            dx = closest["pos"][0] - mx
            dy = closest["pos"][1] - my
            send(sock, f"SHOOT {dx:.1f} {dy:.1f}")

        # move toward closest resource (or wander)
        if resources:
            target = min(resources, key=lambda r: math.hypot(r["pos"][0] - mx, r["pos"][1] - my))
            dx = target["pos"][0] - mx
            dy = target["pos"][1] - my
            send(sock, f"MOVE {dx:.1f} {dy:.1f}")
        else:
            # random wander
            angle = random.uniform(0, 2 * math.pi)
            send(sock, f"MOVE {math.cos(angle):.1f} {math.sin(angle):.1f}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[*] Bye!")
