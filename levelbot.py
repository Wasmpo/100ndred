import discord
from discord.ext import commands
import os
import asyncio
from datetime import datetime
import json

# Config
intents = discord.Intents.all()
intents.message_content = True
level_bot = commands.Bot(command_prefix=">",
                         intents=intents,
                         help_command=None,
                         owner_id=1237239569808625767)

# Constants
WELCOME_CHANNEL_ID = 1366040548019929098
LOG_CHANNEL_ID = 1368311044904190052
ADMIN_ROLES = {1366040463122890843, 318004345193103361}
DB_FILE = "level_data.json"

LEVELS = {
    1: 40,
    2: 100,
    3: 180,
    4: 280,
    5: 400,
    10: 1500,
    15: 3000,
    20: 5000,
    25: 7500,
    30: 10500,
    35: 14000,
    40: 18000,
    45: 22500,
    50: 27500
}

# Database functions
def load_db():
    try:
        with open(DB_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {'users': {}}

def save_db(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=2)

# --- EVENTS ---
@level_bot.event
async def on_ready():
    print(f"✅ {level_bot.user} is online")
    await level_bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching, name="Waiting for new players..."))
    
    # Initialize DB if empty
    db = load_db()
    if 'users' not in db:
        db['users'] = {}
        save_db(db)

@level_bot.event
async def on_member_join(member):
    channel = level_bot.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        try:
            embed = discord.Embed(
                title=f"👋 Welcome to 100NDRED, {member.display_name}!",
                description="• Get roles in <#1366040534275194951>\n• Read rules in <#1362388375528804462>",
                color=0x00ff00
            )
            embed.set_thumbnail(url=member.avatar.url if member.avatar else None)
            welcome_msg = await channel.send(embed=embed)
            await asyncio.sleep(120)
            await welcome_msg.delete()
        except Exception as e:
            print(f"Error in welcome message: {e}")

@level_bot.event
async def on_message(message):
    if message.author.bot or message.content.startswith(level_bot.command_prefix):
        await level_bot.process_commands(message)
        return

    db = load_db()
    user_id = str(message.author.id)

    if user_id not in db['users']:
        db['users'][user_id] = {"words": 0, "level": 0}

    words = len(message.content.split())
    db['users'][user_id]["words"] += words

    current_level = db['users'][user_id]["level"]
    new_level = 0

    for level, req in sorted(LEVELS.items(), reverse=True):
        if db['users'][user_id]["words"] >= req:
            new_level = level
            break

    if new_level > current_level:
        db['users'][user_id]["level"] = new_level
        if current_level > 0:
            old_role = discord.utils.get(message.guild.roles,
                                       name=f"🏆・𝐋𝐞𝐯𝐞𝐥 {current_level}")
            if old_role and old_role in message.author.roles:
                await message.author.remove_roles(old_role)

        new_role = discord.utils.get(message.guild.roles,
                                   name=f"🏆・𝐋𝐞𝐯𝐞𝐥 {new_level}")
        if new_role:
            await message.author.add_roles(new_role)
            await message.channel.send(
                f"🎉 {message.author.mention} reached Level {new_level}!",
                delete_after=10)

    save_db(db)
    await level_bot.process_commands(message)

# [Rest of your commands (help, rank, rank_reset, xp_add, leaderboard) remain the same, 
# just replace db with load_db()/save_db(db) where needed]

if __name__ == '__main__':
    level_bot.run(os.getenv('DISCORD_TOKEN'))
