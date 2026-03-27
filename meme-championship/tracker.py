#!/usr/bin/env python3
"""
Meme Championship Tracker - Discord Bot
Tracks meme posts, reactions, and emoji usage in the chaos Discord server.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Optional

import discord
from discord import app_commands

# Configuration
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
MEMES_FILE = os.path.join(DATA_DIR, "memes.json")
REACTIONS_FILE = os.path.join(DATA_DIR, "reactions.json")
EMOJI_FILE = os.path.join(DATA_DIR, "emoji.json")

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('MemeTracker')

# Meme detection keywords (for text memes)
MEME_KEYWORDS = [
    'meme', 'lol', 'lmao', 'rofl', 'lmfao', 'cope', 'seethe', 'malding',
    'ratio', 'skill issue', 'touch grass', 'based', 'cringe', 'no cap',
    'slay', 'bussin', 'its giving', 'understood the assignment', 'ate and left no crumbs',
    'main character', 'delulu', 'slay', 'lowkey', 'highkey', 'rent free'
]

# Image extensions for meme detection
IMAGE_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.mp4', '.webm']


def load_json(filepath: str, default: dict = None) -> dict:
    """Load JSON data from file, return default if file doesn't exist."""
    if default is None:
        default = {}
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def save_json(filepath: str, data: dict) -> None:
    """Save data to JSON file."""
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2, default=str)


def is_meme_content(message: discord.Message) -> tuple[bool, str]:
    """Check if a message is a meme (image or text with keywords)."""
    # Check for attachments (images/videos)
    for attachment in message.attachments:
        for ext in IMAGE_EXTENSIONS:
            if attachment.filename.lower().endswith(ext):
                return True, "image"
    
    # Check for embed images (linked images)
    for embed in message.embeds:
        if embed.image or embed.thumbnail:
            return True, "image"
    
    # Check text content for meme keywords
    content_lower = message.content.lower()
    for keyword in MEME_KEYWORDS:
        if keyword in content_lower:
            return True, "text"
    
    # Check for specific meme formats
    if any(char in content_lower for char in ['💀', '🤣', '😂', '😭']):
        return True, "text"
    
    return False, ""


class MemeTracker(discord.Client):
    """Main bot class for tracking memes, reactions, and emoji."""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.reactions = True
        intents.guilds = True
        
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        
        # Data storage
        self.memes = load_json(MEMES_FILE)
        self.reactions = load_json(REACTIONS_FILE)
        self.emoji_usage = load_json(EMOJI_FILE)
        
        # Initialize storage structures if empty
        if "posts" not in self.memes:
            self.memes["posts"] = []
        if "reactions" not in self.reactions:
            self.reactions["reactions"] = []
        if "usage" not in self.emoji_usage:
            self.emoji_usage["usage"] = []
    
    async def setup_hook(self):
        """Set up the bot when it starts."""
        await self.tree.sync()
        logger.info("Meme Tracker bot synced!")
    
    async def on_ready(self):
        """Called when bot is ready."""
        logger.info(f'Logged in as {self.user} (ID: {self.user.id})')
        logger.info('Bot is ready to track memes!')
        
        # Find the Lily channel
        for guild in self.guilds:
            for channel in guild.channels:
                if channel.name.lower() in ['lily', 'memes', 'lounge']:
                    logger.info(f"Found channel: {channel.name} ({channel.id})")
    
    async def on_message(self, message: discord.Message):
        """Handle incoming messages."""
        # Ignore bot messages
        if message.author.bot:
            return
        
        # Check if message is a meme
        is_meme, meme_type = is_meme_content(message)
        
        if is_meme:
            meme_entry = {
                "user_id": str(message.author.id),
                "username": message.author.name,
                "message_id": str(message.id),
                "channel_id": str(message.channel.id),
                "timestamp": message.created_at.isoformat(),
                "type": meme_type,
                "content": message.content[:200] if message.content else ""
            }
            
            self.memes["posts"].append(meme_entry)
            save_json(MEMES_FILE, self.memes)
            logger.info(f"Meme detected from {message.author.name}: {meme_type}")
    
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.User):
        """Handle reactions added to messages."""
        if user.bot:
            return
        
        # Get the message author (the person who posted)
        if reaction.message.author.bot:
            return
        
        reaction_entry = {
            "user_id": str(reaction.message.author.id),
            "username": reaction.message.author.name,
            "message_id": str(reaction.message.id),
            "reactor_id": str(user.id),
            "reactor_name": user.name,
            "emoji": str(reaction.emoji),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.reactions["reactions"].append(reaction_entry)
        save_json(REACTIONS_FILE, self.reactions)
        logger.info(f"Reaction from {user.name} on {reaction.message.author.name}'s message")
    
    def count_emoji_usage(self, message: discord.Message) -> Dict[str, int]:
        """Count emoji usage in a message."""
        emoji_counts = defaultdict(int)
        
        # Count unicode emoji in content
        for char in message.content:
            if ord(char) > 127000:  # Emoji range
                emoji_counts[char] += 1
        
        # Count custom emoji
        for emoji in message.emojis:
            emoji_counts[f":{emoji.name}:"] += 1
        
        return dict(emoji_counts)
    
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        """Track emoji usage when messages are edited."""
        if after.author.bot:
            return
        
        emoji_counts = self.count_emoji_usage(after)
        for emoji, count in emoji_counts.items():
            usage_entry = {
                "user_id": str(after.author.id),
                "username": after.author.name,
                "emoji": emoji,
                "count": count,
                "timestamp": datetime.utcnow().isoformat(),
                "message_id": str(after.id)
            }
            self.emoji_usage["usage"].append(usage_entry)
        
        if emoji_counts:
            save_json(EMOJI_FILE, self.emoji_usage)


def aggregate_weekly_data() -> dict:
    """Aggregate data for the current week."""
    memes = load_json(MEMES_FILE)
    reactions = load_json(REACTIONS_FILE)
    emoji_usage = load_json(EMOJI_FILE)
    
    # Calculate leaderboards
    meme_counts = defaultdict(int)
    reaction_received = defaultdict(int)
    emoji_counts = defaultdict(int)
    
    # Count memes per user
    for post in memes.get("posts", []):
        meme_counts[post["username"]] += 1
    
    # Count reactions received per user
    for reaction in reactions.get("reactions", []):
        reaction_received[reaction["username"]] += 1
    
    # Count emoji usage per user
    for usage in emoji_usage.get("usage", []):
        emoji_counts[usage["username"]] += usage.get("count", 1)
    
    # Get tier for a score
    def get_tier(score: int) -> tuple[str, str]:
        if score <= 2:
            return "💀", "Dead Weight"
        elif score <= 5:
            return "😬", "Warming Up"
        elif score <= 9:
            return "🔥", "Mid-Tier Chaos"
        elif score <= 14:
            return "💎", "Elite Shitposter"
        else:
            return "👑", "Meme Lord"
    
    # Build leaderboards
    def build_leaderboard(counts: dict) -> list:
        leaderboard = []
        for username, score in sorted(counts.items(), key=lambda x: -x[1]):
            tier, tier_name = get_tier(score)
            leaderboard.append({
                "username": username,
                "score": score,
                "tier": tier,
                "tier_name": tier_name
            })
        return leaderboard
    
    meme_leaderboard = build_leaderboard(dict(meme_counts))
    reaction_leaderboard = build_leaderboard(dict(reaction_received))
    emoji_leaderboard = build_leaderboard(dict(emoji_counts))
    
    # Get winners and losers
    weekly_winner = None
    weekly_loser = None
    
    if meme_leaderboard:
        weekly_winner = {
            "category": "memes",
            "username": meme_leaderboard[0]["username"],
            "score": meme_leaderboard[0]["score"]
        }
        if len(meme_leaderboard) > 1:
            weekly_loser = {
                "category": "memes",
                "username": meme_leaderboard[-1]["username"],
                "score": meme_leaderboard[-1]["score"]
            }
    
    # Get current week info
    now = datetime.utcnow()
    start_of_week = now - timedelta(days=now.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    
    weekly_data = {
        "week": f"{now.isocalendar()[0]}-W{now.isocalendar()[1]:02d}",
        "start_date": start_of_week.strftime("%Y-%m-%d"),
        "end_date": end_of_week.strftime("%Y-%m-%d"),
        "generated_at": now.isoformat(),
        "leaderboards": {
            "memes": meme_leaderboard,
            "reactions": reaction_leaderboard,
            "emoji": emoji_leaderboard
        },
        "weekly_winner": weekly_winner,
        "weekly_loser": weekly_loser
    }
    
    return weekly_data


def export_weekly_data() -> None:
    """Export current week data to file."""
    weekly_data = aggregate_weekly_data()
    
    # Save to current.json
    current_file = os.path.join(DATA_DIR, "current.json")
    save_json(current_file, weekly_data)
    
    # Save to weeks archive
    week_filename = f"week_{weekly_data['week'].replace('-', '_')}.json"
    weeks_dir = os.path.join(DATA_DIR, "weeks")
    os.makedirs(weeks_dir, exist_ok=True)
    week_file = os.path.join(weeks_dir, week_filename)
    save_json(week_file, weekly_data)
    
    logger.info(f"Weekly data exported to {week_file}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Meme Championship Tracker")
    parser.add_argument("--aggregate", action="store_true", help="Aggregate weekly data")
    parser.add_argument("--export", action="store_true", help="Export weekly data")
    
    args = parser.parse_args()
    
    if args.aggregate or args.export:
        export_weekly_data()
        print("Weekly data aggregation complete!")
    else:
        # Run the bot
        token = os.getenv("DISCORD_BOT_TOKEN")
        if not token:
            logger.error("DISCORD_BOT_TOKEN environment variable not set!")
            logger.info("Get a token from https://discord.com/developers/applications")
            return
        
        client = MemeTracker()
        client.run(token, log_handler=None)


if __name__ == "__main__":
    main()
