# ╔══════════════════════════════════════════════════════════════════╗
# ║                                                                  ║
# ║   ░█▀▀░█▀█░█▀▄░█▀▀░█░█   ░█▀▄░█▀▀░█░█░█▀▀                     ║
# ║   ░█░░░█░█░█░█░█▀▀░▄▀▄   ░█░█░█▀▀░▀▄▀░▀▀█                     ║
# ║   ░▀▀▀░▀▀▀░▀▀░░▀▀▀░▀░▀   ░▀▀░░▀▀▀░░▀░░▀▀▀                     ║
# ║                                                                  ║
# ║            © 2026 CodeX Devs — All Rights Reserved              ║
# ║                                                                  ║
# ║   discord  ──  https://discord.gg/codexdev                      ║
# ║   youtube  ──  https://youtube.com/@CodeXDevs                   ║
# ║   github   ──  https://github.com/RayExo                        ║
# ║                                                                  ║
# ╚══════════════════════════════════════════════════════════════════╝

import discord
import aiosqlite
import json
import re
import asyncio
from discord.ext import commands

class greet(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.join_queue = {}
        self.processing = set()

    async def safe_format(self, text, placeholders):
        placeholders_lower = {k.lower(): v for k, v in placeholders.items()}
        def replace_var(match):
            var_name = match.group(1).lower()
            return str(placeholders_lower.get(var_name, f"{{{var_name}}}"))
        return re.sub(r"\{(\w+)\}", replace_var, text or "")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.guild.id not in self.join_queue:
            self.join_queue[member.guild.id] = []
        self.join_queue[member.guild.id].append(member)
        if member.guild.id not in self.processing:
            self.processing.add(member.guild.id)
            await self.process_queue(member.guild)

    async def process_queue(self, guild):
        while self.join_queue[guild.id]:
            member = self.join_queue[guild.id].pop(0)
            async with aiosqlite.connect("db/welcome.db") as db:
                async with db.execute("SELECT welcome_type, welcome_message, channel_id, embed_data, auto_delete_duration FROM welcome WHERE guild_id = ?", (guild.id,)) as cursor:
                    row = await cursor.fetchone()
            if row is None:
                continue
            welcome_type, welcome_message, channel_id, embed_data, auto_delete_duration = row
            welcome_channel = self.bot.get_channel(channel_id)
            if not welcome_channel:
                continue
            now = discord.utils.utcnow()
            account_age_days = (now - member.created_at).days if member.created_at else 0
            placeholders = {
                "user": member.mention,
                "user_avatar": member.display_avatar.url,
                "user_name": member.name,
                "account_name": member.name,
                "user_id": str(member.id),
                "user_nick": member.display_name,
                "account_age": str(account_age_days),
                "user_age": str(account_age_days),
                "user_joindate": member.joined_at.strftime("%a, %b %d, %Y") if member.joined_at else "Unknown",
                "user_createdate": member.created_at.strftime("%a, %b %d, %Y") if member.created_at else "Unknown",
                "server_name": guild.name,
                "server_id": str(guild.id),
                "server_membercount": f"{guild.member_count:,}" if guild.member_count else "0",
                "member_count": f"{guild.member_count:,}" if guild.member_count else "0",
                "server_icon": guild.icon.url if guild.icon else "https://cdn.discordapp.com/embed/avatars/0.png",
                "timestamp": discord.utils.format_dt(now)
            }
            try:
                if welcome_type == "simple" and welcome_message:
                    content = await self.safe_format(welcome_message, placeholders)
                    sent_message = await welcome_channel.send(content=content)
                elif welcome_type == "embed" and embed_data:
                    embed_info = json.loads(embed_data)
                    color_value = embed_info.get("color", None)
                    embed_color = 0x2b2d31
                    if color_value and isinstance(color_value, str) and color_value.startswith("#"):
                        embed_color = discord.Color(int(color_value.lstrip("#"), 16))
                    elif isinstance(color_value, int):
                        embed_color = discord.Color(color_value)
                    content = await self.safe_format(embed_info.get("message", ""), placeholders) or None
                    embed = discord.Embed(
                        title=await self.safe_format(embed_info.get("title", ""), placeholders),
                        description=await self.safe_format(embed_info.get("description", ""), placeholders),
                        color=embed_color
                    )
                    embed.timestamp = discord.utils.utcnow()
                    if embed_info.get("footer_text"):
                        f_icon = await self.safe_format(embed_info.get("footer_icon", ""), placeholders) if embed_info.get("footer_icon") else None
                        embed.set_footer(
                            text=await self.safe_format(embed_info["footer_text"], placeholders),
                            icon_url=f_icon or None
                        )
                    if embed_info.get("author_name"):
                        a_icon = await self.safe_format(embed_info.get("author_icon", ""), placeholders) if embed_info.get("author_icon") else None
                        embed.set_author(
                            name=await self.safe_format(embed_info["author_name"], placeholders),
                            icon_url=a_icon or None
                        )
                    if embed_info.get("thumbnail"):
                        thumb = await self.safe_format(embed_info["thumbnail"], placeholders)
                        if thumb:
                            embed.set_thumbnail(url=thumb)
                    if embed_info.get("image"):
                        img = await self.safe_format(embed_info["image"], placeholders)
                        if img:
                            embed.set_image(url=img)
                    sent_message = await welcome_channel.send(content=content, embed=embed)
                if auto_delete_duration:
                    await sent_message.delete(delay=auto_delete_duration)
            except discord.Forbidden:
                continue
            except discord.HTTPException as e:
                if e.code == 50035 or e.status == 429:
                    await asyncio.sleep(1)
                    self.join_queue[guild.id].append(member)
                    continue
            await asyncio.sleep(2)
        self.processing.remove(guild.id)

