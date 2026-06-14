import tkinter as tk
from tkinter import messagebox
import requests
import json
import os
import re

import sys

def get_asset_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)

def fetch_and_package():
    input_text = textbox.get("1.0", tk.END).strip()
    
    if not input_text:
        messagebox.showwarning("No AppID", "No AppID's provided")
        return

    app_ids = re.findall(r'\d+', input_text)
    
    if not app_ids:
        messagebox.showwarning("Invalid Input", "I can't find this AppID. Please double check it.")
        return

    user_profile = os.environ.get('USERPROFILE', os.path.expanduser('~'))
    base_dir = os.path.join(user_profile, 'AppData', 'LocalLow', 'NestedLoop', 'BOXROOM', 'steam_cache_v2')

    if not os.path.exists(base_dir):
        os.makedirs(base_dir)

    success_count = 0
    successful_ids = [] # We need to track these to update the ledger later!

    for appid in app_ids:
        steam_url = f"https://store.steampowered.com/api/appdetails?appids={appid}"
        
        try:
            response = requests.get(steam_url)
            data = response.json()
            
            if str(appid) in data and data[str(appid)]["success"]:
                game_info = data[str(appid)]["data"]
                
                genres = [g["description"] for g in game_info.get("genres", [])]
                screenshots = [s["path_full"] for s in game_info.get("screenshots", [])]
                
                meta_package = {
                    "PlayTimeMinutes": 0,
                    "Name": game_info.get("name", "Unknown"),
                    "ShortDescription": game_info.get("short_description", ""),
                    "DetailedDescription": game_info.get("detailed_description", ""),
                    "AboutTheGame": game_info.get("about_the_game", ""),
                    "BoxArtUrlBase": f"https://cdn.cloudflare.steamstatic.com/steam/apps/{appid}/",
                    "FallbackHeaderUrl": game_info.get("header_image", ""),
                    "ReleaseDate": game_info.get("release_date", {}).get("date", "Unknown"),
                    "Developers": game_info.get("developers", []),
                    "Publishers": game_info.get("publishers", []),
                    "Genres": genres,
                    "ScreenshotUrls": screenshots
                }
                
                # Create folders inside appdata
                target_folder = os.path.join(base_dir, str(appid))
                if not os.path.exists(target_folder):
                    os.makedirs(target_folder)
                    
                file_path = os.path.join(target_folder, "meta.json")
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(meta_package, f, indent=2, ensure_ascii=False)
                    
                success_count += 1
                successful_ids.append(int(appid)) # Save as integer for the ledger!
            else:
                print(f"Steam couldn't find data for AppID: {appid}")
                
        except Exception as e:
            print(f"A communication error accoured with {appid}: {e}")

    # Update the owned_games.json ledger
    if successful_ids:
        owned_games_path = os.path.join(base_dir, "owned_games.json")
        
        if os.path.exists(owned_games_path):
            try:
                with open(owned_games_path, "r", encoding="utf-8") as f:
                    owned_data = json.load(f)
                    
                # Add our new IDs if they aren't already in the ledger
                if "AppIds" in owned_data:
                    for new_id in successful_ids:
                        if new_id not in owned_data["AppIds"]:
                            owned_data["AppIds"].append(new_id)

                with open(owned_games_path, "w", encoding="utf-8") as f:
                    json.dump(owned_data, f, separators=(',', ':'), ensure_ascii=False)
                    
            except Exception as e:
                print(f"Oh my! I couldn't update the owned_games.json ledger: {e}")

    if success_count > 0:
        messagebox.showinfo("Delivery Complete!", f"Yes, yes! Successfully packaged {success_count} item(s) into their folders and updated the ledger!")
    else:
        messagebox.showwarning("Delivery Failed", "Oh my. I couldn't fetch data for any of the provided AppIDs.")


# GUI
# bg 1e1108
# yellow f0c030
# text 9a8463


root = tk.Tk()
root.title("BoxCo GameStation")
root.geometry("450x530")
icon_path = get_asset_path(os.path.join("assets", "icon.ico"))
root.iconbitmap(icon_path)
root.configure(padx=20, pady=20, bg="#1e1108")

title_label = tk.Label(root, text="BOXCO GameStation", font=("Helvetica", 12, "bold"), bg="#f0c030", fg="#1e1108")
title_label.pack(pady=(0, 10))

instruction_label = tk.Label(root, text=" Enter Steam AppID's Of Your Games: \n(You can separate multiple IDs with spaces or commas)", font=("Helvetica", 9), bg="#1e1108", fg="#9a8463")
instruction_label.pack(pady=(0, 10))

textbox = tk.Text(root, height=12, width=40, font=("Helvetica", 10), bg="#0e0608", fg="#9a8463")
textbox.pack(pady=10)

fetch_button = tk.Button(root, text="Fetch Metadata", font=("Helvetica", 12, "bold"), bg="#f0c030", fg="#1e1108", command=fetch_and_package)
fetch_button.pack(pady=10)

footer_label = tk.Label(root, text="fffuyayyyamada", font=("Helvetica", 8), bg="#1e1108", fg="#9a8463")
footer_label.pack(side=tk.BOTTOM, pady=10)

root.mainloop()