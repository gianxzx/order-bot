import discord
from discord.ext import commands
import os
from keep_alive import keep_alive
from ui_components import ClaimView

# --- Replace these with your actual IDs ---
TOKEN = "MTQ2MDk1ODY1MDY2NjMxOTkxMw.G-OZ2g.BsxOur3nrvuVYhDL6tx5tKuma6MAWEe9RzJ9zI"
INPUT_CHANNEL_ID = 1461710247969292316  # The channel receiving webhooks
QUEUE_CHANNEL_ID = 1461710247969292313  # The channel for claimed items

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True # Required to read webhook content
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Register the ClaimView so it stays active across restarts
        self.add_view(ClaimView(QUEUE_CHANNEL_ID))

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")

    async def on_message(self, message):
        # 1. THE INTERCEPTION
        # Filter: Only act if it's in the Input Channel and is a Webhook
        if message.channel.id == INPUT_CHANNEL_ID and message.webhook_id:
            
            # 2. THE TRANSFORMATION
            # Create a professional looking embed from the webhook text
            embed = discord.Embed(
                title="📦 New Action Required",
                description=message.content,
                color=discord.Color.blue()
            )
            embed.set_footer(text=f"Source ID: {message.webhook_id}")

            # Send the interactive version
            await message.channel.send(embed=embed, view=ClaimView(QUEUE_CHANNEL_ID))
            
            # Delete the messy original webhook message
            await message.delete()

        await self.process_commands(message)

# Start the web server (for Render)
keep_alive()

# Start the Bot
bot = MyBot()
bot.run(TOKEN)
