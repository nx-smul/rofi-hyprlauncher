import re
from pathlib import Path
from typing import List, Tuple


def get_shortcut_id(appid: int):
    return (appid << 32) | 0x02000000


def get_non_steam_games(steam_root_path: Path) -> List[Tuple[str, str, str, str]]:
    # Search for the shortcuts.vdf file within the userdata directory
    userdata_path = steam_root_path / 'userdata'

    # Search through all the subdirectories in userdata (which represent user IDs)
    shortcut_path = None
    for user_dir in userdata_path.iterdir():
        if user_dir.is_dir():
            possible_shortcut_path = user_dir / 'config' / 'shortcuts.vdf'
            if possible_shortcut_path.is_file():
                shortcut_path = possible_shortcut_path
                break  # Stop once we find the first valid shortcuts.vdf

    if not shortcut_path:
        print("No non-Steam games shortcut file found in userdata directories.")
        return []

    # Read the shortcut file
    shortcut_bytes = shortcut_path.read_bytes()

    # Using regex to extract the shortcut information from the binary data
    game_pattern = re.compile(
        b"\x00\x02appid\x00(.{4})\x01appname\x00([^\x08]+?)\x00\x01exe\x00([^\x08]+?)\x00\x01.+?\x00tags\x00(?:\x01([^\x08]+?)|)\x08\x08", flags=re.DOTALL | re.IGNORECASE)

    games = []
    for game_match in game_pattern.findall(shortcut_bytes):
        # Convert the appid from bytes to integer
        appid = int.from_bytes(game_match[0], byteorder='little', signed=False)
        name = game_match[1].decode('utf-8')
        target = game_match[2].decode('utf-8')
        games.append((name, target, str(get_shortcut_id(appid))))

    return games


def list_games_in_rows(games: List[Tuple[str, str, str]]):
    """
    Function to print the games in CSV format.
    """
    # Print each game's details in CSV format (no header in the output)
    for game in games:
        # Output in requested format
        # Shortcut ID, Game Name, Executable Path
        print(f"{game[2]},{game[0]},{game[1]}")


# Example usage with Linux file path
# Assuming the default Steam installation path
steam_root_path = Path.home() / '.steam' / 'steam'

# Get the list of non-Steam games
games = get_non_steam_games(steam_root_path)

# List the games in the requested CSV format
if games:
    list_games_in_rows(games)
else:
    print("No non-Steam games found.")
