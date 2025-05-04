import discord
from discord.ext import commands
import os
import asyncio
from datetime import datetime
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

# --- COMMANDS ---
@level_bot.command()
async def help(ctx):
    """Custom help command"""
    embed = discord.Embed(title="🔹 100NDERD BOT COMMANDS",
                        description="Bot is watching for new players...",
                        color=0x1abc9c)

    embed.add_field(
        name="🎚️ LEVEL SYSTEM",
        value="`>rank` - Check your level\n`>leaderboard` - Top 10 players",
        inline=False)

    if any(role.id in ADMIN_ROLES for role in ctx.author.roles):
        embed.add_field(
            name="⚙️ ADMIN TOOLS",
            value="`>rank_reset @user` - Reset progress\n`>xp_add @user 100` - Grant XP",
            inline=False)

    await ctx.send(embed=embed)

@level_bot.command()
@commands.cooldown(1, 10, commands.BucketType.user)  # 10-second cooldown
async def rank(ctx, member: discord.Member = None):
    target = member or ctx.author
    user_id = str(target.id)
    db = load_db()
    
    if user_id not in db['users']:
        return await ctx.send(f"{target.mention} hasn't earned XP yet!", delete_after=10)
    
    data = db['users'][user_id]
    next_lvl = data['level'] + 1
    req_xp = LEVELS.get(next_lvl, "MAX")
    
    embed = discord.Embed(title=f"🏆 {target.display_name}'s Rank", color=0x3498db)
    embed.add_field(name="Level", value=data['level'], inline=True)
    embed.add_field(name="Total Words", value=data['words'], inline=True)
    embed.add_field(name="Progress", value=f"{data['words']}/{req_xp}", inline=False)
    embed.set_thumbnail(url=target.avatar.url if target.avatar else None)
    
    await ctx.send(embed=embed, delete_after=20)

@level_bot.command()
@commands.has_any_role(*ADMIN_ROLES)
async def rank_reset(ctx, member: discord.Member):
    """Reset a user's progress"""
    db = load_db()
    user_id = str(member.id)

    if user_id not in db['users']:
        return await ctx.send(f"❌ {member.mention} has no rank data!",
                            delete_after=10)

    for lvl in range(1, 51):
        role = discord.utils.get(ctx.guild.roles, name=f"🏆・𝐋𝐞𝐯𝐞𝐥 {lvl}")
        if role and role in member.roles:
            await member.remove_roles(role)

    db['users'][user_id] = {"words": 0, "level": 0}
    save_db(db)

    log_channel = level_bot.get_channel(LOG_CHANNEL_ID)
    if log_channel:
        await log_channel.send(
            f"⚠️ **Rank Reset**\n"
            f"Admin: {ctx.author.mention}\n"
            f"Target: {member.mention}\n"
            f"Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")

    await ctx.send(f"✅ {member.mention}'s progress reset!", delete_after=10)

@level_bot.command()
@commands.has_any_role(*ADMIN_ROLES)
async def xp_add(ctx, member: discord.Member, amount: int):
    """Add XP to a user"""
    db = load_db()
    user_id = str(member.id)
    if user_id not in db['users']:
        db['users'][user_id] = {"words": 0, "level": 0}

    db['users'][user_id]["words"] += amount
    save_db(db)
    await ctx.send(f"Added {amount} XP to {member.mention}.", delete_after=10)

@level_bot.command()
@commands.cooldown(1, 30, commands.BucketType.user)
async def leaderboard(ctx):
    """Show top 10 active users"""
    try:
        db = load_db()
        users = sorted(db['users'].items(),
                     key=lambda x: x[1]['words'],
                     reverse=True)[:10]

        embed = discord.Embed(title="🏅 Leaderboard",
                            description="Top 10 most active members:",
                            color=0xffd700)

        for idx, (user_id, data) in enumerate(users, 1):
            member = ctx.guild.get_member(int(user_id))
            name = member.display_name if member else "Unknown"
            embed.add_field(
                name=f"{idx}. {name}",
                value=f"Level {data['level']} | {data['words']} words",
                inline=False)

        await ctx.send(embed=embed)

    except Exception as e:
        print(f"Leaderboard error: {e}")
        await ctx.send("❌ Couldn't generate leaderboard", delete_after=10)

@level_bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingAnyRole):
        await ctx.send("❌ Admin only command!", delete_after=10)
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏳ Try again in {error.retry_after:.1f}s.",
                     delete_after=5)
    else:
        print(f"Error: {error}")

if __name__ == '__main__':
    level_bot.run(os.getenv('DISCORD_TOKEN'))
