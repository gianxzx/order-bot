import discord
from discord.ext import commands
import sqlite3
import json
import uuid
from datetime import datetime

# ================= CONFIG =================
TOKEN = "MTQ2MDk1ODY1MDY2NjMxOTkxMw.G-OZ2g.BsxOur3nrvuVYhDL6tx5tKuma6MAWEe9RzJ9zI"
INPUT_CHANNEL_ID  = 1461710247969292313   # webhook messages come here
QUEUE_CHANNEL_ID  = 1461710247969292316   # claimed items go here
LOG_CHANNEL_ID    = None                 # optional: declines / errors

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ================= DATABASE SETUP =================
DB_FILE = "claims.db"

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS claims (
                short_id TEXT PRIMARY KEY,
                payload_json TEXT NOT NULL,
                created_at INTEGER NOT NULL,
                claimed_by INTEGER,
                claimed_at INTEGER
            )
        """)
        conn.commit()

init_db()

# ================= HELPER =================
def save_payload(payload: dict) -> str:
    """Save payload → return short unique ID"""
    short_id = str(uuid.uuid4())[:8]  # 8 chars is plenty
    payload_json = json.dumps(payload, ensure_ascii=False)
    
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute(
            "INSERT INTO claims (short_id, payload_json, created_at) VALUES (?, ?, ?)",
            (short_id, payload_json, int(datetime.utcnow().timestamp()))
        )
        conn.commit()
    return short_id

def get_payload(short_id: str) -> dict | None:
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("SELECT payload_json FROM claims WHERE short_id = ?", (short_id,))
        row = c.fetchone()
        return json.loads(row[0]) if row else None

def mark_claimed(short_id: str, user_id: int):
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute(
            "UPDATE claims SET claimed_by = ?, claimed_at = ? WHERE short_id = ?",
            (user_id, int(datetime.utcnow().timestamp()), short_id)
        )
        conn.commit()

# ================= PERSISTENT VIEW =================
class ClaimView(discord.ui.View):
    def __init__(self, short_id: str):
        super().__init__(timeout=None)  # persistent
        self.short_id = short_id

    @discord.ui.button(label="Claim", style=discord.ButtonStyle.green, custom_id="claim:")
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):
        payload = get_payload(self.short_id)
        if not payload:
            await interaction.response.send_message("This claim is no longer available.", ephemeral=True)
            await interaction.message.delete()
            return

        # Mark as claimed in DB
        mark_claimed(self.short_id, interaction.user.id)

        # Edit original message
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.green()
        embed.title = "Claimed Order"
        embed.add_field(name="Claimed by", value=interaction.user.mention, inline=True)
        embed.set_footer(text=f"Claimed at {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")

        await interaction.message.edit(embed=embed, view=None)

        # Send to queue channel
        queue_channel = bot.get_channel(QUEUE_CHANNEL_ID)
        if queue_channel:
            content = f"Claimed by {interaction.user.mention}"
            embeds = [discord.Embed.from_dict(e) for e in payload.get("embeds", [])]
            files = [discord.File(fp=e["url"], filename=e["name"]) for e in payload.get("attachments", []) if "url" in e and "name" in e]

            await queue_channel.send(content=content, embeds=embeds, files=files)

            await interaction.response.send_message("Order claimed and moved to queue!", ephemeral=True)
        else:
            await interaction.response.send_message("Queue channel not found.", ephemeral=True)

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.red, custom_id="decline:")
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.message.delete()
        await interaction.response.send_message("Declined and removed.", ephemeral=True)

        # Optional: log somewhere
        if LOG_CHANNEL_ID:
            log_ch = bot.get_channel(LOG_CHANNEL_ID)
            if log_ch:
                payload = get_payload(self.short_id)
                if payload:
                    await log_ch.send(f"Declined by {interaction.user.mention} — {payload.get('content', '…')[:100]}")

# ================= REGISTER PERSISTENT VIEW =================
@bot.event
async def setup_hook():
    bot.add_view(ClaimView(""))  # empty short_id → we handle dynamic in callback

# ================= WEBHOOK LISTENER =================
@bot.event
async def on_message(message: discord.Message):
    if not message.webhook_id:
        return  # not from webhook

    if message.channel.id != INPUT_CHANNEL_ID:
        return

    if message.author.bot:  # safety
        return

    try:
        # 1. Capture data
        payload = {
            "content": message.content or "",
            "embeds": [e.to_dict() for e in message.embeds],
            "attachments": [{"url": a.url, "name": a.filename} for a in message.attachments],
            "timestamp": message.created_at.isoformat(),
            # add more fields if needed (username, avatar_url, etc.)
        }

        short_id = save_payload(payload)

        # 2. Build nice embed
        embed = discord.Embed(
            title="New Order / Request",
            description=payload["content"] or "No text content",
            color=0x5865F2,
            timestamp=discord.utils.utcnow()
        )

        if payload["embeds"]:
            embed.add_field(name="Original Embed", value="[Attached]", inline=False)
            if payload["embeds"][0].get("thumbnail", {}).get("url"):
                embed.set_thumbnail(url=payload["embeds"][0]["thumbnail"]["url"])

        if payload["attachments"]:
            names = ", ".join(a["name"] for a in payload["attachments"])
            embed.add_field(name="Attachments", value=names, inline=False)

        embed.set_footer(text=f"Awaiting claim • ID: {short_id}")

        # 3. Send repost + view
        view = ClaimView(short_id)
        view.claim.custom_id = f"claim:{short_id}"
        view.decline.custom_id = f"decline:{short_id}"

        await message.channel.send(embed=embed, view=view)

        # 4. Clean original webhook message
        await message.delete()

    except Exception as e:
        print(f"Error processing webhook: {e}")
        # optional: log to owner or channel

# ================= START =================
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} — Watching input channel {INPUT_CHANNEL_ID}")

bot.run(TOKEN)
