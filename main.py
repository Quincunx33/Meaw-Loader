#!/usr/bin/env python3
"""
Meaw Loader entrypoint for Botkeep / Pterodactyl hosting environments.
Executes server.py directly.
"""
import runpy
import sys
import os

if __name__ == "__main__":
    server_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "server.py")
    runpy.run_path(server_script, run_name="__main__")
