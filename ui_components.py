import discord

class ClaimView(discord.ui.View):
    def __init__(self, queue_channel_id):
        super().__init__(timeout=None) # Keeps buttons working after bot restart
        self.queue_channel_id = queue_channel_id

    @discord.ui.button(label="Claim", style=discord.ButtonStyle.success, custom_id="claim_btn")
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):
        # 1. Capture the existing embed data
        original_embed = interaction.message.embeds[0]
        
        # 2. Update embed to show who claimed it
        new_embed = original_embed.copy()
        new_embed.color = discord.Color.green()
        new_embed.add_field(name="Status", value=f"✅ Claimed by {interaction.user.mention}")

        # 3. Redirect to the Queue Channel
        queue_channel = interaction.guild.get_channel(self.queue_channel_id)
        if queue_channel:
            await queue_channel.send(embed=new_embed)
            # 4. Update the original message to disable buttons
            await interaction.response.edit_message(content="**Moved to Queue**", embed=new_embed, view=None)
        else:
            await interaction.response.send_message("Queue channel not found!", ephemeral=True)

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.danger, custom_id="decline_btn")
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Simply delete the message to "Archive" it
        await interaction.message.delete()

