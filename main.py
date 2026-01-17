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
        if message.channel.id == INPUT_CHANNEL_ID and message.webhook_id:
            
            # Default values
            description_text = message.content
            
            # If the webhook sent an Embed (like in your screenshot), capture its data
            if not description_text and len(message.embeds) > 0:
                incoming_embed = message.embeds[0]
                # Use the description or title of the incoming embed
                description_text = incoming_embed.description or incoming_embed.title or "New Order Received"
            
            # 2. THE TRANSFORMATION
            # We wrap the captured data into our own interactive embed
            new_embed = discord.Embed(
                title="🩵 NEW KITCHEN TICKET",
                description=description_text,
                color=discord.Color.blue()
            )
            
            # If the original embed had fields (like Roblox User, Total Bill), copy them
            if len(message.embeds) > 0:
                for field in message.embeds[0].fields:
                    new_embed.add_field(name=field.name, value=field.value, inline=field.inline)

            # Send the interactive version with buttons
            await message.channel.send(embed=new_embed, view=ClaimView(QUEUE_CHANNEL_ID))
            
            # Delete the original webhook message
            await message.delete()

        await self.process_commands(message)

# Start the web server (for Render)
keep_alive()

# Start the Bot
bot = MyBot()
bot.run(TOKEN)
