#!/usr/bin/env python3

import os
import sys

# Paths for configuration
CONFIG_DIR = os.path.expanduser("~/.config")
STATE_DIR = os.path.expanduser("~/.local/state")
SteamGridDB_API = os.path.join(STATE_DIR, "steamgriddb_apikey")
ADD_API = os.path.join(CONFIG_DIR, "rofi", "add_steamgridDB_api.sh")


# Check if running in a terminal
def is_running_in_terminal():
    return os.isatty(sys.stdin.fileno())


# Load API key from file
def load_api_key():
    if os.path.exists(SteamGridDB_API):
        with open(SteamGridDB_API, 'r') as f:
            for line in f:
                if line.strip():
                    return line.strip()
    return None


# Notify if API key is missing
def api_key_not_found(API_KEY=None):
    notification_message = f"API key not found. To add your API key, run {
        ADD_API}"

    if not API_KEY:
        if not is_running_in_terminal():
            os.system(
                f'notify-send "SteamGridDB" "To add non-Steam games, run {ADD_API} and add your API key."')
        else:
            print(notification_message)
        sys.exit()


if __name__ == "__main__":
    API_KEY = load_api_key()
    if API_KEY:
        print(f"API key loaded successfully: {API_KEY}")
    else:
        api_key_not_found()
