#!/usr/bin/env python3

import os
import re
import sys
import glob
from pathlib import Path
from typing import List

# Declare steam_root for global usage
steam_root = os.path.expanduser("~/.local/share/Steam")


class Game:
    def __init__(self, id, name, alt_id, process_name):
        self.id = id
        self.name = name
        self.alt_id = alt_id
        self.process_name = process_name


# Find the path to shortcuts.vdf
def find_shortcuts_vdf():
    pattern = os.path.join(steam_root, "userdata/*/config/shortcuts.vdf")
    files = glob.glob(pattern)
    if files:
        return files[0]
    else:
        sys.exit("Error: No shortcuts.vdf file found")


# Get non-Steam games from shortcuts.vdf using regex
def get_non_steam_games() -> List[Game]:
    shortcut_path = find_shortcuts_vdf()
    if not os.path.isfile(shortcut_path):
        print(f"No non-Steam games shortcut file found at {
              shortcut_path}. Assuming no non-Steam games are installed.")
        return []
    shortcut_bytes = Path(shortcut_path).read_bytes()

    game_pattern = re.compile(
        b"(?i)\x00\x02appid\x00(.{4})\x01appname\x00([^\x08]+?)\x00\x01exe\x00([^\x08]+?)\x00\x01.+?\x00tags\x00(?:\x01([^\x08]+?)|)\x08\x08"
    )
    games = []
    for game_match in game_pattern.findall(shortcut_bytes):
        id = str(int.from_bytes(
            game_match[0], byteorder="little", signed=False))
        name = game_match[1].decode("utf-8")
        target = game_match[2].decode("utf-8")
        target_process = os.path.basename(re.sub(r'^"|"$', "", target))
        games.append(Game(id="unknown", name=name,
                     alt_id=id, process_name=target_process))

    return games


if __name__ == "__main__":
    non_steam_games = get_non_steam_games()
    if non_steam_games:
        print("List of non-Steam games found:")
        for game in non_steam_games:
            print(f"Name: {game.name}, Alt ID: {
                  game.alt_id}, Process Name: {game.process_name}")
    else:
        print("No non-Steam games found.")
