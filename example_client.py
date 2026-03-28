#!/usr/bin/env python3
"""COM315ARENA — example client.

Usage:
    python3 example_client.py <host> <port> <your_name>

Example:
    python3 example_client.py localhost 9000 MyBot

This client demonstrates:
  - TCP connection and JOIN handshake
  - Correct TCP framing (buffering + splitting on newlines)
  - Threaded architecture (receiver thread + main decision loop)
  - Parsing GAMESTATE, HIT, DEATH, KILL, RESPAWN messages
  - Using the provided strategy module for decision-making

YOUR JOB: Write your own version of the NETWORKING code below.
The strategy module (strategy.py) handles what commands to send.
Your client handles HOW to send and receive them over TCP.
"""

import json
import socket
import sys
import threading
import time

from strategy import decide


# ─── Receiver Thread ──────────────────────────────────────────
#
# Runs in the background. Reads bytes from the socket, buffers
# them, splits on newlines, and parses each complete message.
#
# IMPORTANT: TCP is a byte stream. A single recv() can return
# partial messages or multiple messages glued together. The
# buffer + split-on-newline pattern below is REQUIRED.

def recv_loop(sock, state):
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

        # Split buffer into complete lines
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
                print(f"[*] Joined as player {info['id']}"
                      f" at ({info['pos'][0]:.0f}, {info['pos'][1]:.0f})")

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


# ─── Send Helper ──────────────────────────────────────────────

def send(sock, msg):
    """Send a newline-terminated command to the server."""
    sock.sendall((msg + "\n").encode())


# ─── Main ─────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 4:
        print(f"Usage: {sys.argv[0]} <host> <port> <name>")
        sys.exit(1)

    host, port, name = sys.argv[1], int(sys.argv[2]), sys.argv[3]

    # 1. Connect via TCP
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    print(f"[*] Connected to {host}:{port}")

    # 2. Send JOIN
    send(sock, f"JOIN {name}")

    # 3. Start the receiver thread
    state = {"running": True, "game": None, "id": None, "map": None}
    t = threading.Thread(target=recv_loop, args=(sock, state), daemon=True)
    t.start()

    # Wait for WELCOME
    while state["id"] is None and state["running"]:
        time.sleep(0.05)
    if not state["running"]:
        return

    print("[*] Playing! Ctrl+C to quit.")

    # 4. Decision loop — read game state, call strategy, send command
    while state["running"]:
        time.sleep(0.1)  # ~10 decisions per second

        gs = state.get("game")
        if not gs:
            continue

        # The strategy module decides what command to send.
        # Your job is everything AROUND this call — the networking.
        command = decide(gs)
        if command:
            send(sock, command)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[*] Bye!")
