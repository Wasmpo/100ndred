import discord
from discord.ext import commands
from datetime import datetime
import os
import json

DB_FILE = "updates_data.json"

def load_db():
    try:
        with open(DB_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {'versions': {}}

def save_db(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=2)

# Configuration
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.reactions = True

update_bot = commands.Bot(command_prefix="^", intents=intents, help_command=None)

# Constants
ANNOUNCEMENT_CHANNEL_ID = 1368311044904190052
DEVELOPER_ROLE_ID = 1366040463122890843
APPROVER_ROLE_ID = 1366040463122890843

@update_bot.event
async def on_ready():
    print(f"✅ {update_bot.user} is online")
    # Initialize DB if empty
    db = load_db()  # Add this line
    if 'versions' not in db:
        db['versions'] = {}
        save_db(db)

def create_update_embed(version: str, notes: str, author: discord.Member, approved: bool = False):
    embed = discord.Embed(
        title=f"{'✅ ' if approved else '🛠️ '}Update v{version}",
        color=0x1abc9c if approved else 0xf1c40f,
        description=f"*{'Approved' if approved else 'Pending'} update*",
        timestamp=datetime.utcnow())
    embed.add_field(name="📌 Changes", value=notes, inline=False)
    embed.add_field(name="🛣️ Roadmap", value="• Ticket System\n• Performance Dashboard\n• Mobile App", inline=False)
    embed.set_footer(
        text=f"Update {datetime.now().strftime('%d/%m-%Y')} | {author.display_name}",
        icon_url=author.avatar.url if author.avatar else None)
    return embed

@update_bot.command()
@commands.has_role(DEVELOPER_ROLE_ID)
async def devupdate(ctx, version: str, *, notes: str):
    """Submit a new update for approval"""
    db = load_db()
    db['versions'][version] = {
        'date': datetime.now().isoformat(),
        'author': str(ctx.author.id),
        'notes': notes
    }
    save_db(db)

    channel = update_bot.get_channel(ANNOUNCEMENT_CHANNEL_ID)
    if channel:
        msg = await channel.send(
            f"<@&{APPROVER_ROLE_ID}> New update:",
            embed=create_update_embed(version, notes, ctx.author)
        )
        await msg.add_reaction("✅")
        await msg.add_reaction("❌")
        await ctx.send(f"📝 Update v{version} submitted!", delete_after=10)

@update_bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id == update_bot.user.id:
        return

    channel = update_bot.get_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)

    if not message.embeds or "Update v" not in message.embeds[0].title:
        return

    guild = update_bot.get_guild(payload.guild_id)
    member = guild.get_member(payload.user_id)

    if not any(role.id == APPROVER_ROLE_ID for role in member.roles):
        return

    version = message.embeds[0].title.split("v")[-1]
    db = load_db()

    if str(payload.emoji) == "✅" and version in db['versions']:
        data = db['versions'][version]
        author = guild.get_member(int(data['author']))
        await channel.send(
            embed=create_update_embed(version, data['notes'], author, True))
    
    await message.delete()

if __name__ == "__main__":
    update_bot.run(os.getenv('ANNOUNCE_TOKEN'))
