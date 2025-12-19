#!/usr/bin/env python3
"""
Installation script for the Honeypot Cog.
This script helps install the cog into a Red bot instance.
"""

import os
import shutil
import sys
from pathlib import Path

def find_red_bot_directory():
    """Find the Red bot directory"""
    possible_paths = [
        os.path.expanduser("~/Red-DiscordBot"),
        os.path.expanduser("~/.local/share/Red-DiscordBot"),
        os.path.expanduser("~/Red-DiscordBot/data"),
        "Red-DiscordBot",
        "redbot"
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            cogs_path = os.path.join(path, "cogs")
            if os.path.exists(cogs_path):
                return cogs_path
    
    return None

def install_cog():
    """Install the honeypot cog"""
    print("Honeypot Cog Installer")
    print("======================")
    
    # Find Red bot directory
    red_bot_cogs = find_red_bot_directory()
    
    if not red_bot_cogs:
        print("❌ Could not find Red bot directory.")
        print("Please make sure Red bot is installed and run this script from the correct location.")
        print("\nPossible locations:")
        print("- ~/Red-DiscordBot")
        print("- ~/.local/share/Red-DiscordBot")
        print("- Current directory (if Red bot is in ./Red-DiscordBot)")
        return False
    
    print(f"✅ Found Red bot cogs directory: {red_bot_cogs}")
    
    # Get current directory (where this script is located)
    current_dir = Path(__file__).parent
    honeypot_cog_source = current_dir / "neufox-honeypot"
    
    if not honeypot_cog_source.exists():
        print("❌ Could not find neufox-honeypot directory.")
        print("Make sure you're running this script from the correct location.")
        return False
    
    # Destination path
    honeypot_cog_dest = Path(red_bot_cogs) / "neufox-honeypot"
    
    try:
        # Remove existing installation if it exists
        if honeypot_cog_dest.exists():
            print(f"🔄 Removing existing installation...")
            shutil.rmtree(honeypot_cog_dest)
        
        # Copy the cog
        print(f"📦 Installing honeypot cog...")
        shutil.copytree(honeypot_cog_source, honeypot_cog_dest)
        
        print("✅ Honeypot cog installed successfully!")
        print("\nNext steps:")
        print("1. Start your Red bot")
        print("2. Load the cog: [p]load neufox-honeypot")
        print("3. Configure: [p]honeypot #channel")
        print("\nNote: Make sure the bot has Manage Messages and Ban Members.")
        
        return True
        
    except Exception as e:
        print(f"❌ Installation failed: {e}")
        return False

if __name__ == "__main__":
    success = install_cog()
    sys.exit(0 if success else 1)
