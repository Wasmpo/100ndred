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
intents.members = True  # For role checks
intents.message_content = True  # For commands
intents.reactions = True  # For approval system

update_bot = commands.Bot(command_prefix="^", intents=intents, help_command=None)

# Constants
ANNOUNCEMENT_CHANNEL_ID = 1368311044904190052
DEVELOPER_ROLE_ID = 1366040463122890843
APPROVER_ROLE_ID = 1366040463122890843

@update_bot.event
async def on_ready():
    print(f"✅ {update_bot.user} is online")
    # Initialize DB if empty
    db = load_db()
    if 'versions' not in db:
        db['versions'] = {}
        save_db(db)

def create_update_embed(version: str, notes: str, author: discord.Member, approved: bool = False):
    """Create a standardized update embed"""
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
async def todays_update(ctx):
    """Post today's development update"""
    embed = discord.Embed(
        title="🛠️ Development Update",
        color=0x1abc9c,
        description="*Latest improvements deployed today*",
        timestamp=datetime.utcnow()
    )
    
    embed.add_field(
        name="🎉 New Features",
        value="• Improved command system\n• Better error handling\n• New role management",
        inline=False
    )
    
    channel = update_bot.get_channel(ANNOUNCEMENT_CHANNEL_ID)
    await channel.send(embed=embed)
    await ctx.send("✅ Today's update posted!", delete_after=10)

@update_bot.command(name="devupdate", help="Submit a new update. Usage: ^devupdate [version] [notes]")
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

@devupdate.error
async def devupdate_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Missing arguments! Usage: `^devupdate [version] [notes]`", delete_after=10)
    elif isinstance(error, commands.MissingRole):
        role = ctx.guild.get_role(DEVELOPER_ROLE_ID)
        await ctx.send(
            f"❌ You need the {role.name if role else 'Developer'} role to use this command!",
            delete_after=10
        )

@update_bot.command()
async def updates(ctx):
    """Show version history"""
    db = load_db()
    if not db['versions']:
        return await ctx.send("No updates yet.", delete_after=10)

    embed = discord.Embed(title="📚 Version History", color=0x3498db)
    for version, data in sorted(db['versions'].items(),
                              key=lambda x: x[1]['date'],
                              reverse=True):
        date = datetime.fromisoformat(data['date']).strftime("%d/%m-%Y")
        author = ctx.guild.get_member(int(data['author']))
        embed.add_field(
            name=f"v{version}",
            value=f"{date} | {author.display_name if author else 'Unknown'}\n{data['notes'][:100]}...",
            inline=False)
    await ctx.send(embed=embed)

@update_bot.command(name="help")
async def bot_help(ctx):
    """Show available commands"""
    help_text = """
    **Developer Bot Commands:**
    `^devupdate [version] [notes]` - Submit new update
    `^todays_update` - Post today's dev update
    `^updates` - Show version history
    `^help` - Show this message
    """
    await ctx.send(help_text)

if __name__ == "__main__":
    update_bot.run(os.getenv('ANNOUNCE_TOKEN'))
