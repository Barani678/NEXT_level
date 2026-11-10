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
from discord.ext import commands
import aiosqlite
import asyncio
import os
from utils.config import OWNER_IDS
from utils.Tools import blacklist_check, ignore_check

DB_PATH = "db/vc_panel.db"


class MemberSelectView(discord.ui.View):
    """Ephemeral view allowing moderator to choose a member for a single-target VC action."""
    def __init__(self, action_name: str, channel: discord.VoiceChannel, callback_coro):
        super().__init__(timeout=60)
        self.action_name = action_name
        self.channel = channel
        self.callback_coro = callback_coro

        options = []
        for m in channel.members:
            options.append(discord.SelectOption(
                label=m.display_name[:25],
                description=f"ID: {m.id}",
                value=str(m.id)
            ))

        if not options:
            options.append(discord.SelectOption(
                label="No other members in VC",
                description="Join or invite others first",
                value="none"
            ))

        select = discord.ui.Select(
            placeholder=f"Select member for {action_name}...",
            min_values=1,
            max_values=1,
            options=options[:25]
        )
        select.callback = self.select_callback
        self.add_item(select)

    async def select_callback(self, interaction: discord.Interaction):
        val = interaction.data["values"][0]
        if val == "none":
            await interaction.response.send_message("❌ No member selected.", ephemeral=True)
            return

        member = interaction.guild.get_member(int(val))
        if not member:
            await interaction.response.send_message("❌ Member not found in server.", ephemeral=True)
            return

        await self.callback_coro(interaction, member)


class VoiceControlView(discord.ui.View):
    """
    Interactive Voice Channel Control Panel with clickable buttons matching the moderation interface.
    """
    def __init__(self, cog, channel_id: int, guild_id: int):
        super().__init__(timeout=None)
        self.cog = cog
        self.channel_id = channel_id
        self.guild_id = guild_id

    async def _check_authorized(self, interaction: discord.Interaction) -> bool:
        if await self.cog.is_controller(interaction.guild.id, interaction.user.id):
            return True
        await interaction.response.send_message("❌ You are not authorized to use this voice control panel.", ephemeral=True)
        return False

    def _get_channel(self, guild: discord.Guild) -> discord.VoiceChannel:
        ch = guild.get_channel(self.channel_id)
        if isinstance(ch, discord.VoiceChannel):
            return ch
        # Fallback to user's current voice channel if available
        return None

    # ──────────────────────────────────────────────────────────────────────────
    # ROW 0: Moderation
    # ──────────────────────────────────────────────────────────────────────────

    @discord.ui.button(label="VC Kick", style=discord.ButtonStyle.secondary, row=0, custom_id="vc_btn_kick")
    async def btn_kick(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_authorized(interaction): return
        ch = self._get_channel(interaction.guild) or getattr(interaction.user.voice, "channel", None)
        if not ch:
            return await interaction.response.send_message("❌ Voice channel not found.", ephemeral=True)

        async def do_kick(inter: discord.Interaction, target: discord.Member):
            try:
                await target.move_to(None, reason=f"VC Kick by {inter.user}")
                await inter.response.send_message(f"👞 Disconnected {target.mention} from {ch.name}.", ephemeral=True)
            except Exception as e:
                await inter.response.send_message(f"❌ Failed to kick {target.mention}: {e}", ephemeral=True)

        view = MemberSelectView("VC Kick", ch, do_kick)
        await interaction.response.send_message("Select member to kick from VC:", view=view, ephemeral=True)

    @discord.ui.button(label="VC Ban", style=discord.ButtonStyle.danger, row=0, custom_id="vc_btn_ban")
    async def btn_ban(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_authorized(interaction): return
        ch = self._get_channel(interaction.guild) or getattr(interaction.user.voice, "channel", None)
        if not ch:
            return await interaction.response.send_message("❌ Voice channel not found.", ephemeral=True)

        async def do_ban(inter: discord.Interaction, target: discord.Member):
            try:
                await ch.set_permissions(target, connect=False, reason=f"VC Ban by {inter.user}")
                if target.voice and target.voice.channel == ch:
                    await target.move_to(None, reason="VC Ban")
                await inter.response.send_message(f"🚫 Banned {target.mention} from joining {ch.name}.", ephemeral=True)
            except Exception as e:
                await inter.response.send_message(f"❌ Failed to VC-ban {target.mention}: {e}", ephemeral=True)

        view = MemberSelectView("VC Ban", ch, do_ban)
        await interaction.response.send_message("Select member to ban from this VC:", view=view, ephemeral=True)

    @discord.ui.button(label="VC Unban", style=discord.ButtonStyle.success, row=0, custom_id="vc_btn_unban")
    async def btn_unban(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_authorized(interaction): return
        ch = self._get_channel(interaction.guild) or getattr(interaction.user.voice, "channel", None)
        if not ch:
            return await interaction.response.send_message("❌ Voice channel not found.", ephemeral=True)

        banned_overwrites = [target for target, perms in ch.overwrites.items() if isinstance(target, discord.Member) and perms.connect is False]
        if not banned_overwrites:
            return await interaction.response.send_message("ℹ️ No specific members are currently VC-banned in this channel.", ephemeral=True)

        options = [discord.SelectOption(label=m.display_name[:25], description=f"ID: {m.id}", value=str(m.id)) for m in banned_overwrites[:25]]

        class UnbanSelect(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=60)
                sel = discord.ui.Select(placeholder="Select member to unban...", options=options)
                sel.callback = self.cb
                self.add_item(sel)

            async def cb(self, inter: discord.Interaction):
                mid = int(inter.data["values"][0])
                member = inter.guild.get_member(mid)
                if member:
                    await ch.set_permissions(member, overwrite=None, reason=f"VC Unban by {inter.user}")
                    await inter.response.send_message(f"✅ Unbanned {member.mention} from {ch.name}.", ephemeral=True)
                else:
                    await inter.response.send_message("❌ Member not found.", ephemeral=True)

        await interaction.response.send_message("Select member to VC-unban:", view=UnbanSelect(), ephemeral=True)

    @discord.ui.button(label="VC Kick All", style=discord.ButtonStyle.secondary, row=0, custom_id="vc_btn_kickall")
    async def btn_kickall(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_authorized(interaction): return
        ch = self._get_channel(interaction.guild) or getattr(interaction.user.voice, "channel", None)
        if not ch:
            return await interaction.response.send_message("❌ Voice channel not found.", ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        count = 0
        for m in list(ch.members):
            if m != interaction.user:
                try:
                    await m.move_to(None, reason=f"VC Kick All by {interaction.user}")
                    count += 1
                except Exception:
                    pass
        await interaction.followup.send(f"👞 Disconnected {count} member(s) from {ch.name}.", ephemeral=True)

    @discord.ui.button(label="VC Ban All", style=discord.ButtonStyle.danger, row=0, custom_id="vc_btn_banall")
    async def btn_banall(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_authorized(interaction): return
        ch = self._get_channel(interaction.guild) or getattr(interaction.user.voice, "channel", None)
        if not ch:
            return await interaction.response.send_message("❌ Voice channel not found.", ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        count = 0
        for m in list(ch.members):
            if m != interaction.user and m != interaction.guild.owner:
                try:
                    await ch.set_permissions(m, connect=False, reason=f"VC Ban All by {interaction.user}")
                    await m.move_to(None, reason="VC Ban All")
                    count += 1
                except Exception:
                    pass
        await interaction.followup.send(f"🚫 Banned and disconnected {count} member(s) from {ch.name}.", ephemeral=True)

    # ──────────────────────────────────────────────────────────────────────────
    # ROW 1: Channel & Moderation Overflow
    # ──────────────────────────────────────────────────────────────────────────

    @discord.ui.button(label="VC Unban All", style=discord.ButtonStyle.success, row=1, custom_id="vc_btn_unbanall")
    async def btn_unbanall(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_authorized(interaction): return
        ch = self._get_channel(interaction.guild) or getattr(interaction.user.voice, "channel", None)
        if not ch:
            return await interaction.response.send_message("❌ Voice channel not found.", ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        cleared = 0
        for target, perms in list(ch.overwrites.items()):
            if isinstance(target, discord.Member) and perms.connect is False:
                await ch.set_permissions(target, overwrite=None, reason=f"VC Unban All by {interaction.user}")
                cleared += 1
        await interaction.followup.send(f"✅ Cleared VC bans for {cleared} member(s).", ephemeral=True)

    @discord.ui.button(label="Lock VC", style=discord.ButtonStyle.danger, row=1, custom_id="vc_btn_lock")
    async def btn_lock(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_authorized(interaction): return
        ch = self._get_channel(interaction.guild) or getattr(interaction.user.voice, "channel", None)
        if not ch:
            return await interaction.response.send_message("❌ Voice channel not found.", ephemeral=True)

        await ch.set_permissions(interaction.guild.default_role, connect=False, reason=f"Locked by {interaction.user}")
        await interaction.response.send_message(f"🔒 Locked {ch.name} (members cannot join).", ephemeral=True)

    @discord.ui.button(label="Unlock VC", style=discord.ButtonStyle.success, row=1, custom_id="vc_btn_unlock")
    async def btn_unlock(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_authorized(interaction): return
        ch = self._get_channel(interaction.guild) or getattr(interaction.user.voice, "channel", None)
        if not ch:
            return await interaction.response.send_message("❌ Voice channel not found.", ephemeral=True)

        await ch.set_permissions(interaction.guild.default_role, connect=None, reason=f"Unlocked by {interaction.user}")
        await interaction.response.send_message(f"🔓 Unlocked {ch.name} (connect permission reset).", ephemeral=True)

    @discord.ui.button(label="Hide VC", style=discord.ButtonStyle.secondary, row=1, custom_id="vc_btn_hide")
    async def btn_hide(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_authorized(interaction): return
        ch = self._get_channel(interaction.guild) or getattr(interaction.user.voice, "channel", None)
        if not ch:
            return await interaction.response.send_message("❌ Voice channel not found.", ephemeral=True)

        await ch.set_permissions(interaction.guild.default_role, view_channel=False, reason=f"Hidden by {interaction.user}")
        await interaction.response.send_message(f"👁️‍🗨️ Hidden {ch.name} from @everyone.", ephemeral=True)

    @discord.ui.button(label="Show VC", style=discord.ButtonStyle.primary, row=1, custom_id="vc_btn_show")
    async def btn_show(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_authorized(interaction): return
        ch = self._get_channel(interaction.guild) or getattr(interaction.user.voice, "channel", None)
        if not ch:
            return await interaction.response.send_message("❌ Voice channel not found.", ephemeral=True)

        await ch.set_permissions(interaction.guild.default_role, view_channel=None, reason=f"Revealed by {interaction.user}")
        await interaction.response.send_message(f"👁️ Made {ch.name} visible to @everyone.", ephemeral=True)

    # ──────────────────────────────────────────────────────────────────────────
    # ROW 2: Voice Mute Controls
    # ──────────────────────────────────────────────────────────────────────────

    @discord.ui.button(label="VMute 1", style=discord.ButtonStyle.secondary, row=2, custom_id="vc_btn_vmute1")
    async def btn_vmute1(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_authorized(interaction): return
        ch = self._get_channel(interaction.guild) or getattr(interaction.user.voice, "channel", None)
        if not ch:
            return await interaction.response.send_message("❌ Voice channel not found.", ephemeral=True)

        async def do_mute(inter: discord.Interaction, target: discord.Member):
            try:
                await target.edit(mute=True, reason=f"VMute by {inter.user}")
                await inter.response.send_message(f"🔇 Server-muted {target.mention}.", ephemeral=True)
            except Exception as e:
                await inter.response.send_message(f"❌ Failed to mute: {e}", ephemeral=True)

        view = MemberSelectView("VMute 1", ch, do_mute)
        await interaction.response.send_message("Select member to mute:", view=view, ephemeral=True)

    @discord.ui.button(label="VUnmute 1", style=discord.ButtonStyle.success, row=2, custom_id="vc_btn_vunmute1")
    async def btn_vunmute1(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_authorized(interaction): return
        ch = self._get_channel(interaction.guild) or getattr(interaction.user.voice, "channel", None)
        if not ch:
            return await interaction.response.send_message("❌ Voice channel not found.", ephemeral=True)

        async def do_unmute(inter: discord.Interaction, target: discord.Member):
            try:
                await target.edit(mute=False, reason=f"VUnmute by {inter.user}")
                await inter.response.send_message(f"🔊 Server-unmuted {target.mention}.", ephemeral=True)
            except Exception as e:
                await inter.response.send_message(f"❌ Failed to unmute: {e}", ephemeral=True)

        view = MemberSelectView("VUnmute 1", ch, do_unmute)
        await interaction.response.send_message("Select member to unmute:", view=view, ephemeral=True)

    @discord.ui.button(label="Mute All", style=discord.ButtonStyle.danger, row=2, custom_id="vc_btn_muteall")
    async def btn_muteall(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_authorized(interaction): return
        ch = self._get_channel(interaction.guild) or getattr(interaction.user.voice, "channel", None)
        if not ch:
            return await interaction.response.send_message("❌ Voice channel not found.", ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        count = 0
        for m in ch.members:
            if m != interaction.user and not m.bot:
                try:
                    await m.edit(mute=True, reason=f"Mute All by {interaction.user}")
                    count += 1
                except Exception:
                    pass
        await interaction.followup.send(f"🔇 Muted {count} member(s) in {ch.name}.", ephemeral=True)

    @discord.ui.button(label="Unmute All", style=discord.ButtonStyle.success, row=2, custom_id="vc_btn_unmuteall")
    async def btn_unmuteall(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_authorized(interaction): return
        ch = self._get_channel(interaction.guild) or getattr(interaction.user.voice, "channel", None)
        if not ch:
            return await interaction.response.send_message("❌ Voice channel not found.", ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        count = 0
        for m in ch.members:
            if not m.bot:
                try:
                    await m.edit(mute=False, reason=f"Unmute All by {interaction.user}")
                    count += 1
                except Exception:
                    pass
        await interaction.followup.send(f"🔊 Unmuted {count} member(s) in {ch.name}.", ephemeral=True)

    # ──────────────────────────────────────────────────────────────────────────
    # ROW 3: Voice Deafen Controls
    # ──────────────────────────────────────────────────────────────────────────

    @discord.ui.button(label="Deafen 1", style=discord.ButtonStyle.secondary, row=3, custom_id="vc_btn_deafen1")
    async def btn_deafen1(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_authorized(interaction): return
        ch = self._get_channel(interaction.guild) or getattr(interaction.user.voice, "channel", None)
        if not ch:
            return await interaction.response.send_message("❌ Voice channel not found.", ephemeral=True)

        async def do_deafen(inter: discord.Interaction, target: discord.Member):
            try:
                await target.edit(deafen=True, reason=f"Deafen by {inter.user}")
                await inter.response.send_message(f"🔕 Server-deafened {target.mention}.", ephemeral=True)
            except Exception as e:
                await inter.response.send_message(f"❌ Failed to deafen: {e}", ephemeral=True)

        view = MemberSelectView("Deafen 1", ch, do_deafen)
        await interaction.response.send_message("Select member to deafen:", view=view, ephemeral=True)

    @discord.ui.button(label="Undeafen 1", style=discord.ButtonStyle.success, row=3, custom_id="vc_btn_undeafen1")
    async def btn_undeafen1(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_authorized(interaction): return
        ch = self._get_channel(interaction.guild) or getattr(interaction.user.voice, "channel", None)
        if not ch:
            return await interaction.response.send_message("❌ Voice channel not found.", ephemeral=True)

        async def do_undeafen(inter: discord.Interaction, target: discord.Member):
            try:
                await target.edit(deafen=False, reason=f"Undeafen by {inter.user}")
                await inter.response.send_message(f"🔔 Server-undeafened {target.mention}.", ephemeral=True)
            except Exception as e:
                await inter.response.send_message(f"❌ Failed to undeafen: {e}", ephemeral=True)

        view = MemberSelectView("Undeafen 1", ch, do_undeafen)
        await interaction.response.send_message("Select member to undeafen:", view=view, ephemeral=True)

    @discord.ui.button(label="Deafen All", style=discord.ButtonStyle.danger, row=3, custom_id="vc_btn_deafenall")
    async def btn_deafenall(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_authorized(interaction): return
        ch = self._get_channel(interaction.guild) or getattr(interaction.user.voice, "channel", None)
        if not ch:
            return await interaction.response.send_message("❌ Voice channel not found.", ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        count = 0
        for m in ch.members:
            if m != interaction.user and not m.bot:
                try:
                    await m.edit(deafen=True, reason=f"Deafen All by {interaction.user}")
                    count += 1
                except Exception:
                    pass
        await interaction.followup.send(f"🔕 Deafened {count} member(s) in {ch.name}.", ephemeral=True)

    @discord.ui.button(label="Undeafen All", style=discord.ButtonStyle.success, row=3, custom_id="vc_btn_undeafenall")
    async def btn_undeafenall(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_authorized(interaction): return
        ch = self._get_channel(interaction.guild) or getattr(interaction.user.voice, "channel", None)
        if not ch:
            return await interaction.response.send_message("❌ Voice channel not found.", ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        count = 0
        for m in ch.members:
            if not m.bot:
                try:
                    await m.edit(deafen=False, reason=f"Undeafen All by {interaction.user}")
                    count += 1
                except Exception:
                    pass
        await interaction.followup.send(f"🔔 Undeafened {count} member(s) in {ch.name}.", ephemeral=True)

    # ──────────────────────────────────────────────────────────────────────────
    # ROW 4: Drag Controls
    # ──────────────────────────────────────────────────────────────────────────

    @discord.ui.button(label="VDrag", style=discord.ButtonStyle.primary, row=4, custom_id="vc_btn_vdrag")
    async def btn_vdrag(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_authorized(interaction): return
        ch = self._get_channel(interaction.guild) or getattr(interaction.user.voice, "channel", None)
        if not ch:
            return await interaction.response.send_message("❌ Voice channel not found.", ephemeral=True)

        async def do_drag(inter: discord.Interaction, target: discord.Member):
            self.cog.active_vdrags[inter.user.id] = target.id
            await inter.response.send_message(f"🧲 **VDrag enabled!** {target.mention} will now auto-follow you across voice channels. Click `VDrag Stop` to cancel.", ephemeral=True)

        view = MemberSelectView("VDrag", ch, do_drag)
        await interaction.response.send_message("Select member to auto-drag with you:", view=view, ephemeral=True)

    @discord.ui.button(label="VDrag Stop", style=discord.ButtonStyle.danger, row=4, custom_id="vc_btn_vdragstop")
    async def btn_vdragstop(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_authorized(interaction): return
        if interaction.user.id in self.cog.active_vdrags:
            del self.cog.active_vdrags[interaction.user.id]
            await interaction.response.send_message("🛑 **VDrag stopped.** You will no longer drag any members.", ephemeral=True)
        else:
            await interaction.response.send_message("ℹ️ You do not currently have an active VDrag target.", ephemeral=True)


class VoicePanel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_vdrags = {}  # {moderator_id: target_user_id}
        self.bot.loop.create_task(self.initialize_db())

    async def initialize_db(self):
        os.makedirs("db", exist_ok=True)
        async with aiosqlite.connect(DB_PATH, timeout=30.0) as db:
            await db.execute("PRAGMA journal_mode=WAL;")
            await db.execute("""
                CREATE TABLE IF NOT EXISTS vc_panel_config (
                    guild_id INTEGER PRIMARY KEY,
                    enabled BOOLEAN DEFAULT 1
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS vc_controllers (
                    guild_id INTEGER,
                    user_id INTEGER,
                    PRIMARY KEY (guild_id, user_id)
                )
            """)
            await db.commit()

    async def is_controller(self, guild_id: int, user_id: int) -> bool:
        if user_id in OWNER_IDS:
            return True
        guild = self.bot.get_guild(guild_id)
        if guild:
            if guild.owner_id == user_id:
                return True
            member = guild.get_member(user_id)
            if member and member.guild_permissions.administrator:
                return True

        async with aiosqlite.connect(DB_PATH, timeout=30.0) as db:
            async with db.execute("SELECT 1 FROM vc_controllers WHERE guild_id = ? AND user_id = ?", (guild_id, user_id)) as cur:
                row = await cur.fetchone()
                return row is not None

    async def add_controller(self, guild_id: int, user_id: int):
        async with aiosqlite.connect(DB_PATH, timeout=30.0) as db:
            await db.execute("INSERT OR IGNORE INTO vc_controllers (guild_id, user_id) VALUES (?, ?)", (guild_id, user_id))
            await db.commit()

    async def remove_controller(self, guild_id: int, user_id: int):
        async with aiosqlite.connect(DB_PATH, timeout=30.0) as db:
            await db.execute("DELETE FROM vc_controllers WHERE guild_id = ? AND user_id = ?", (guild_id, user_id))
            await db.commit()

    async def list_controllers(self, guild_id: int) -> list[int]:
        async with aiosqlite.connect(DB_PATH, timeout=30.0) as db:
            async with db.execute("SELECT user_id FROM vc_controllers WHERE guild_id = ?", (guild_id,)) as cur:
                rows = await cur.fetchall()
                return [r[0] for r in rows]

    async def is_panel_enabled(self, guild_id: int) -> bool:
        async with aiosqlite.connect(DB_PATH, timeout=30.0) as db:
            async with db.execute("SELECT enabled FROM vc_panel_config WHERE guild_id = ?", (guild_id,)) as cur:
                row = await cur.fetchone()
                return row is None or row[0] == 1

    async def set_panel_enabled(self, guild_id: int, enabled: bool):
        async with aiosqlite.connect(DB_PATH, timeout=30.0) as db:
            await db.execute("INSERT OR REPLACE INTO vc_panel_config (guild_id, enabled) VALUES (?, ?)", (guild_id, int(enabled)))
            await db.commit()

    def build_panel_embed(self, channel: discord.VoiceChannel, member: discord.Member) -> discord.Embed:
        embed = discord.Embed(
            title=f"🎙️ Voice Channel Control Panel",
            description=(
                f"**Channel:** {channel.mention} (`{channel.id}`)\n"
                f"**Controller:** {member.mention}\n\n"
                f"🔨 **Moderation**\n"
                f"`VC Kick` • `VC Ban` • `VC Unban` • `VC Kick All` • `VC Ban All` • `VC Unban All`\n"
                f"────────────────────────────\n"
                f"⚙️ **Channel**\n"
                f"`Lock VC` • `Unlock VC` • `Hide VC` • `Show VC`\n"
                f"────────────────────────────\n"
                f"🔊 **Voice**\n"
                f"`VMute 1` • `VUnmute 1` • `Mute All` • `Unmute All`\n"
                f"`Deafen 1` • `Undeafen 1` • `Deafen All` • `Undeafen All`\n"
                f"`VDrag` • `VDrag Stop`"
            ),
            color=0x2B2D31
        )
        embed.set_footer(text="ZyroX Voice Management • Click buttons below to moderate")
        embed.set_thumbnail(url=member.display_avatar.url)
        return embed

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if member.bot:
            return

        # ── 1. Handle VDrag ──────────────────────────────────────────────────
        if member.id in self.active_vdrags and after.channel is not None and before.channel != after.channel:
            target_id = self.active_vdrags[member.id]
            target = member.guild.get_member(target_id)
            if target and target.voice and target.voice.channel:
                try:
                    await target.move_to(after.channel, reason=f"VDrag follow {member}")
                except Exception:
                    pass

        # ── 2. Handle Auto Panel on Join VC ──────────────────────────────────
        if after.channel is not None and (before.channel is None or before.channel.id != after.channel.id):
            if not await self.is_panel_enabled(member.guild.id):
                return

            if await self.is_controller(member.guild.id, member.id):
                # Send control panel to the voice channel's chat
                try:
                    embed = self.build_panel_embed(after.channel, member)
                    view = VoiceControlView(self, after.channel.id, member.guild.id)
                    content = f"🎙️ {member.mention} — Voice Channel Control Panel for **{after.channel.name}**"
                    await after.channel.send(content=content, embed=embed, view=view)
                except Exception as e:
                    print(f"[VC Panel] Could not send panel to {after.channel.name}: {e}")

    # ──────────────────────────────────────────────────────────────────────────
    # COMMANDS
    # ──────────────────────────────────────────────────────────────────────────

    @commands.group(name="vcpanel", invoke_without_command=True, aliases=["vcp"])
    @blacklist_check()
    @ignore_check()
    async def vc_panel_cmd(self, ctx: commands.Context):
        """Shows or manually summons the Voice Control Panel."""
        if not ctx.author.voice or not ctx.author.voice.channel:
            return await ctx.reply("❌ You must be connected to a voice channel to open the VC panel.", delete_after=8)

        if not await self.is_controller(ctx.guild.id, ctx.author.id):
            return await ctx.reply("❌ You are not an authorized VC controller in this server.", delete_after=8)

        channel = ctx.author.voice.channel
        embed = self.build_panel_embed(channel, ctx.author)
        view = VoiceControlView(self, channel.id, ctx.guild.id)
        content = f"🎙️ {ctx.author.mention} — Voice Channel Control Panel for **{channel.name}**"
        await channel.send(content=content, embed=embed, view=view)
        await ctx.reply(f"✅ Voice Control Panel sent in {channel.mention} text chat!", delete_after=6)

    @vc_panel_cmd.command(name="add", help="Add a member ID who can get the VC control panel and moderate VCs.")
    @commands.has_permissions(administrator=True)
    async def add_controller_cmd(self, ctx: commands.Context, member: discord.Member):
        await self.add_controller(ctx.guild.id, member.id)
        await ctx.reply(f"✅ Added {member.mention} (`{member.id}`) to authorized VC controllers.")

    @vc_panel_cmd.command(name="remove", aliases=["del", "rm"], help="Remove an authorized VC controller.")
    @commands.has_permissions(administrator=True)
    async def remove_controller_cmd(self, ctx: commands.Context, member: discord.Member):
        await self.remove_controller(ctx.guild.id, member.id)
        await ctx.reply(f"❌ Removed {member.mention} (`{member.id}`) from VC controllers.")

    @vc_panel_cmd.command(name="list", help="List all authorized VC controllers in this server.")
    async def list_controllers_cmd(self, ctx: commands.Context):
        ids = await self.list_controllers(ctx.guild.id)
        if not ids:
            return await ctx.reply("ℹ️ No custom controller IDs configured (Only Server Owner & Admins currently have access).")

        mentions = [f"<@{uid}> (`{uid}`)" for uid in ids]
        embed = discord.Embed(
            title="🎙️ Authorized VC Controllers",
            description="\n".join(mentions),
            color=0x2B2D31
        )
        embed.set_footer(text=f"Total: {len(ids)} controllers")
        await ctx.reply(embed=embed)

    @vc_panel_cmd.command(name="toggle", help="Toggle auto-sending the VC panel when joining a voice channel.")
    @commands.has_permissions(administrator=True)
    async def toggle_panel_cmd(self, ctx: commands.Context):
        current = await self.is_panel_enabled(ctx.guild.id)
        new_state = not current
        await self.set_panel_enabled(ctx.guild.id, new_state)
        status = "enabled" if new_state else "disabled"
        await ctx.reply(f"⚙️ Auto Voice Control Panel on join is now **{status}**.")


async def setup(bot):
    await bot.add_cog(VoicePanel(bot))

