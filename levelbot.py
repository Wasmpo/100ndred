import discord
from discord.ext import commands
import os
import asyncio
import json

# Config
DB_FILE = "level_data.json"

def load_db():
    try:
        with open(DB_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {'users': {}}

def save_db(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=2)

# Initialize bot with disabled default help command
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=">", intents=intents, help_command=None)

# ===== CONFIGURATION =====
APPLICATION_ID = 1362388618978660595
WELCOME_CHANNEL_ID = 1366040548019929098
ADMIN_ID = 1237239569808625767
RANK_COOLDOWN = 25  # seconds
MESSAGE_DELAY = 7  # seconds

# ===== LEVEL SYSTEM =====
LEVELS = {
    1: 10,
    2: 30,
    3: 60,
    4: 100,
    5: 150,
    10: 550,
    15: 1250,
    20: 2200,
    25: 3400,
    30: 4900,
    35: 6700,
    40: 8800,
    45: 11200,
    50: 14000
}

@bot.event
async def on_ready():
    print(f"✅ {bot.user} is online")
    # Initialize DB if empty
    db = load_db()
    if 'users' not in db:
        db['users'] = {}
        save_db(db)

@bot.event
async def on_member_join(member):
    welcome_channel = bot.get_channel(997464496790589520)
    rules_channel = 1362388375528804462
    roles_channel = 1366040534275194951
    
    if welcome_channel:
        welcome_msg = await welcome_channel.send(
            f"Hello {member.mention}!\n\n"
            f"**bingy_owo**\n\n"
            f"Welcome to **100NDRED - Guild Tags**!\n\n"
            f"• Find FAQs in <#{rules_channel}>\n"
            f"• Get your roles in <#{roles_channel}>"
        )
        await asyncio.sleep(120)
        await welcome_msg.delete()

@bot.event
async def on_message(message):
    if message.author.bot:
        return await bot.process_commands(message)

    db = load_db()
    user_id = str(message.author.id)

    if user_id not in db['users']:
        db['users'][user_id] = {"words": 0, "level": 0}

    words = len(message.content.split())
    db['users'][user_id]["words"] += words

    current_level = db['users'][user_id]["level"]
    new_level = max([
        lvl for lvl, req in LEVELS.items() 
        if db['users'][user_id]["words"] >= req
    ], default=0)

    if current_level < new_level:
        db['users'][user_id]["level"] = new_level
        role_name = f"🏆・Level {new_level}"
        role = discord.utils.get(message.guild.roles, name=role_name)
        if role:
            await message.author.add_roles(role)
            await message.channel.send(
                f"🎉 {message.author.mention} reached Level {new_level}!",
                delete_after=10)
    
    save_db(db)
    await bot.process_commands(message)

@bot.command()
@commands.cooldown(1, RANK_COOLDOWN, commands.BucketType.user)
async def rank(ctx):
    """Check your current level and progress"""
    db = load_db()
    user_id = str(ctx.author.id)

    if user_id not in db['users']:
        return await ctx.send("Start chatting to earn levels!", delete_after=MESSAGE_DELAY)

    data = db['users'][user_id]
    next_level = data['level'] + 1
    needed = max(0, LEVELS.get(next_level, 0) - data['words'])

    embed = discord.Embed(
        title=f"🏆 {ctx.author.display_name}'s Rank",
        color=0x00ff00
    )
    embed.add_field(name="Current Level", value=data['level'], inline=True)
    embed.add_field(name="Words Typed", value=data['words'], inline=True)
    embed.add_field(name="Next Level", value=f"{needed} words needed", inline=False)
    
    await ctx.send(embed=embed, delete_after=MESSAGE_DELAY)

if __name__ == '__main__':
    bot.run(os.getenv('DISCORD_TOKEN'))
