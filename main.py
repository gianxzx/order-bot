import discord
from discord.ext import commands
import os
from keep_alive import keep_alive
from ui_components import ClaimView

# --- Configuration ---
# It is better to use Render Environment Variables for these
TOKEN = os.getenv("MTQ2MDk1ODY1MDY2NjMxOTkxMw.GvCEDb.eb2AhAaRw86nK78oHNg7xiYvlYwQRnDeqWfK04") 
INPUT_CHANNEL_ID = 1461710247969292316  # Update with your ID
QUEUE_CHANNEL_ID = 1461710247969292313  # Update with your ID

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True 
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Register view for persistence
        self.add_view(ClaimView(QUEUE_CHANNEL_ID))

    async def on_ready(self):
        print(f"✅ Bot is online as {self.user}")

    async def on_message(self, message):
        # Prevent loops
        if message.author == self.user:
            return

        # 1. THE INTERCEPTION
        if message.channel.id == INPUT_CHANNEL_ID and message.webhook_id:
            
            # 2. THE TRANSFORMATION (Handling the Embed from the screenshot)
            # Create our new interactive ticket
            new_embed = discord.Embed(
                title="🩵 NEW KITCHEN TICKET",
                color=discord.Color.blue()
            )

            # Check if the incoming webhook message has an embed
            if message.embeds:
                incoming = message.embeds[0]
                # Copy the description (the order details)
                new_embed.description = incoming.description
                # Copy all fields (Roblox User, Discord User, Total Bill, etc.)
                for field in incoming.fields:
                    new_embed.add_field(name=field.name, value=field.value, inline=field.inline)
            else:
                # Fallback if it's just plain text
                new_embed.description = message.content

            # Send the interactive version with buttons
            await message.channel.send(embed=new_embed, view=ClaimView(QUEUE_CHANNEL_ID))
            
            # Delete the messy original webhook
            try:
                await message.delete()
            except discord.Forbidden:
                print("Missing 'Manage Messages' permission to delete webhook.")

        await self.process_commands(message)

# Start Flask and Bot
keep_alive()
if TOKEN:
    bot = MyBot()
    bot.run(TOKEN)
else:
    print("❌ ERROR: No BOT_TOKEN found in Environment Variables!")
