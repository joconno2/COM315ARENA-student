#!/usr/bin/env python3
"""COM315ARENA client skeleton.

Usage: python3 example_client.py <host> <port> <name>

This connects to the server but the networking is incomplete.
Your job is to make it work.
"""

import json
import socket
import sys
import time

from strategy import decide


def main():
    if len(sys.argv) < 4:
        print(f"Usage: {sys.argv[0]} <host> <port> <name>")
        sys.exit(1)

    host, port, name = sys.argv[1], int(sys.argv[2]), sys.argv[3]

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    sock.sendall(f"JOIN {name}\n".encode())

    # TODO: Read the WELCOME response and parse the JSON.

    # TODO: In a loop, read data from the socket and process messages.
    #
    # Remember: TCP is a byte stream. A single recv() call may return
    # multiple messages, or only part of one. You need to handle this.
    #
    # For each GAMESTATE message, parse the JSON and call:
    #     command = decide(game_state)
    #     if command:
    #         sock.sendall((command + "\n").encode())
    #
    # You also need to handle: HIT, DEATH, KILL, RESPAWN, ERROR
    #
    # Hint: how do you send commands while also reading from the socket?

    sock.close()


if __name__ == "__main__":
    main()
