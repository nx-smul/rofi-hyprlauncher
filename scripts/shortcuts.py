#!/usr/bin/env python3

import os
import sys
import requests
import shutil
from check_api import load_api_key, api_key_not_found
from game_list import find_shortcuts_vdf, get_non_steam_games

# Declare steam_root at the top for global usage
steam_root = os.path.expanduser("~/.local/share/Steam")
steam_cache = os.path.join(steam_root, "appcache/librarycache")

# API key and Base URL for SteamGridDB
CONFIG_DIR = os.path.expanduser("~/.config")
STATE_DIR = os.path.expanduser("~/.local/state")
SteamGridDB_API = os.path.join(STATE_DIR, "steamgriddb_apikey")
STEAM_APP_ID_FILE = os.path.join(STATE_DIR, "steamAPP_id")
BASE_URL = "https://www.steamgriddb.com/api/v2"
ADD_API = os.path.join(CONFIG_DIR, "rofi", "add_steamgridDB_api.sh")
# Function to compute shortcut ID


def get_shortcut_id(appid: int):
    return (appid << 32) | 0x02000000

# Load processed app IDs from file


def load_processed_app_ids():
    processed_app_ids = set()
    if os.path.exists(STEAM_APP_ID_FILE):
        with open(STEAM_APP_ID_FILE, 'r') as f:
            for line in f:
                if line.strip().isdigit():
                    processed_app_ids.add(int(line.strip()))
    return processed_app_ids


# Save processed app IDs to file
def save_processed_app_ids(app_ids):
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(STEAM_APP_ID_FILE, 'w') as f:
        for app_id in app_ids:
            f.write(f"{app_id}\n")

# Search for images by name in SteamGridDB


def search_images_by_name(name, API_KEY):
    headers = {
        "Authorization": f"Bearer {API_KEY}"
    }
    url = f"{BASE_URL}/search/autocomplete/{name}"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()["data"]
        if data:
            return data[0]["id"]
    return None


# Fetch image URL from SteamGridDB
def fetch_image(app_id, image_type, API_KEY):
    headers = {
        "Authorization": f"Bearer {API_KEY}"
    }
    url = f"{BASE_URL}/{image_type}/game/{app_id}"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()["data"]
        if data:
            return data[0]["url"]
    return None


# Download image from URL
def download_image(url, dest_path):
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
        return True
    return False


# Create library cache for a game
def create_library_cache(app_id, original_app_id, name, exe, force=False, API_KEY=None):
    shortcut_id = get_shortcut_id(original_app_id)
    cache_dir = os.path.join(steam_cache, f"{shortcut_id}")

    if not force and os.path.exists(cache_dir):
        print(f"Appcache folder already exists for {
              name} Skipping image download.\n")
        return

    os.makedirs(cache_dir, exist_ok=True)

    image_types = {
        "grids": "library_600x900.jpg",
        "heroes": "library_hero.jpg",
        "logos": "logo.png"
    }

    for image_type, file_name in image_types.items():
        image_url = fetch_image(app_id, image_type, API_KEY)
        if image_url:
            dest_path = os.path.join(cache_dir, file_name)
            if download_image(image_url, dest_path):
                print(f"{image_type.capitalize()} image downloaded for {name}")
                print(f"Image saved at: {dest_path}")
            else:
                print(f"Failed to download {
                      image_type.capitalize()} image for {name}")
        else:
            print(f"No {image_type.capitalize()} image found for {name}")

    print()  # Add space after processing


# Delete library cache for a game that was removed from shortcuts.vdf
def delete_library_cache(processed_app_ids, current_app_ids):
    for app_id in processed_app_ids:
        if app_id not in current_app_ids:
            shortcut_id = get_shortcut_id(app_id)
            cache_dir = os.path.join(steam_cache, f"{shortcut_id}")

            if os.path.exists(cache_dir):
                try:
                    shutil.rmtree(cache_dir)
                    print(f"Library cache deleted for app_id: {
                          shortcut_id} (removed from shortcuts.vdf)")
                except Exception as e:
                    print(f"Error deleting cache for app_id: {
                          shortcut_id} - {e}")


# Parse shortcuts.vdf file and process the games
def parse_shortcuts(file_path, force=False, API_KEY=None):
    processed_app_ids = load_processed_app_ids()
    new_app_ids = set()

    if os.path.getsize(file_path) == 0:
        print(f"{file_path} is empty. No shortcuts to process.")
        sys.exit(0)

    current_app_ids = set()

    non_steam_games = get_non_steam_games()

    for game in non_steam_games:
        try:
            original_app_id = int(game.alt_id)
            name = game.name
            exe = game.process_name

            shortcut_id = get_shortcut_id(original_app_id)
            steamgrid_app_id = search_images_by_name(name, API_KEY)

            if steamgrid_app_id:
                if original_app_id not in new_app_ids:
                    print(f"Processing {name} (original_app_id: {
                          original_app_id}, Launch_appid: {shortcut_id} SteamGridDB ID: {steamgrid_app_id})...")
                    new_app_ids.add(original_app_id)

                    create_library_cache(
                        steamgrid_app_id, original_app_id, name, exe, force, API_KEY)

            current_app_ids.add(original_app_id)

        except Exception as e:
            print(f"Error processing {game.name}: {e}")

    delete_library_cache(processed_app_ids, current_app_ids)

    print("Finished processing all app IDs.")
    if not force:
        print("\nTo overwrite appcache folders, use the '--force' flag.")


# Main script logic
def main():
    API_KEY = load_api_key()

    api_key_not_found(API_KEY=API_KEY)

    force = '--force' in sys.argv
    file_path = sys.argv[1] if len(
        sys.argv) > 1 and '--force' not in sys.argv[1] else find_shortcuts_vdf()

    print(f"Processing games from: {file_path}")

    parse_shortcuts(file_path, force, API_KEY)


if __name__ == '__main__':
    main()
