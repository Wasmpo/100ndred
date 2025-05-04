import discord
from discord.ext import commands
from datetime import datetime
import os
from replit import db

# Configuration
intents = discord.Intents.default()
intents.members = True  # For role checks
intents.message_content = True  # For commands
intents.reactions = True  # For approval system

update_bot = commands.Bot(command_prefix="^",
                          intents=intents,
                          help_command=None)

# Constants
ANNOUNCEMENT_CHANNEL_ID = 1368311044904190052
DEVELOPER_ROLE_ID = 1366040463122890843
APPROVER_ROLE_ID = 1366040463122890843

# Initialize database
if 'versions' not in db:
    db['versions'] = {}


def create_update_embed(version: str,
                        notes: str,
                        author: discord.Member,
                        approved: bool = False):
    """Create a standardized update embed"""
    embed = discord.Embed(
        title=f"{'✅ ' if approved else '🛠️ '}Update v{version}",
        color=0x1abc9c if approved else 0xf1c40f,
        description=f"*{'Approved' if approved else 'Pending'} update*",
        timestamp=datetime.utcnow())
    embed.add_field(name="📌 Changes", value=notes, inline=False)
    embed.add_field(
        name="🛣️ Roadmap",
        value="• Ticket System\n• Performance Dashboard\n• Mobile App",
        inline=False)
    embed.set_footer(
        text=
        f"Update {datetime.now().strftime('%d/%m-%Y')} | {author.display_name}",
        icon_url=author.avatar.url if author.avatar else None)
    return embed


@update_bot.command()
@commands.has_role(DEVELOPER_ROLE_ID)
async def todays_update(ctx):
    """Post today's development update with recent improvements"""
    embed = discord.Embed(title="🛠️ Development Update - System Upgrades",
                          color=0x1abc9c,
                          description="*Latest improvements deployed today*",
                          timestamp=datetime.utcnow())

    # Today's Changes
    embed.add_field(
        name="🎉 New Features",
        value=
        ("• **Welcome Messages** in main chat with auto-delete after 2 minutes\n"
         "• **Dedicated Staff Bot** for admin commands\n"
         "• **UI Improvements** for >rank and >leaderboard\n"
         "• **Restricted Permissions** for rankreset command"),
        inline=False)

    # Technical Improvements
    embed.add_field(name="⚙️ Backend Upgrades",
                    value=("• Optimized command processing\n"
                           "• Improved database efficiency\n"
                           "• Enhanced error handling\n"
                           "• Added command cooldowns"),
                    inline=False)

    # Roadmap
    embed.add_field(name="🛣️ Coming Soon",
                    value=("• Server analytics dashboard\n"
                           "• Reward system for top players\n"
                           "• Mobile compatibility improvements"),
                    inline=False)

    embed.set_footer(
        text=
        f"Update {datetime.now().strftime('%m/%d/%Y')} | {ctx.author.display_name}",
        icon_url=ctx.author.avatar.url if ctx.author.avatar else None)

    channel = update_bot.get_channel(ANNOUNCEMENT_CHANNEL_ID)
    await channel.send(embed=embed)
    await ctx.send("✅ Today's update posted!", delete_after=10)


@update_bot.command()
@commands.has_role(DEVELOPER_ROLE_ID)
async def devupdate(ctx, version: str, *, notes: str):
    """Submit a new update for approval"""
    db['versions'][version] = {
        'date': datetime.now().isoformat(),
        'author': str(ctx.author.id),
        'notes': notes
    }

    channel = update_bot.get_channel(ANNOUNCEMENT_CHANNEL_ID)
    if channel:
        msg = await channel.send(f"<@&{APPROVER_ROLE_ID}> New update:",
                                 embed=create_update_embed(
                                     version, notes, ctx.author))
        await msg.add_reaction("✅")
        await msg.add_reaction("❌")
        await ctx.send(f"📝 Update v{version} submitted!", delete_after=10)


@update_bot.event
async def on_raw_reaction_add(payload):
    """Handle update approval/rejection"""
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

    if str(payload.emoji) == "✅":
        data = db['versions'][version]
        author = guild.get_member(int(data['author']))
        await channel.send(
            embed=create_update_embed(version, data['notes'], author, True))
    await message.delete()


@update_bot.command()
async def updates(ctx):
    """Show version history"""
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
            value=
            f"{date} | {author.display_name if author else 'Unknown'}\n{data['notes'][:100]}...",
            inline=False)
    await ctx.send(embed=embed)

if __name__ == "__main__":
    token = os.getenv("ANNOUNCE_TOKEN")
    if not token:
        print("❌ ERROR: ANNOUNCE_TOKEN not set in Secrets!")
    else:
        print("🔌 Starting dev bot...")
        update_bot.run(token)
