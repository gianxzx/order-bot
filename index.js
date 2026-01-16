const { Client, GatewayIntentBits, EmbedBuilder, ActionRowBuilder, ButtonBuilder, ButtonStyle } = require('discord.js');
const express = require('express');
const bodyParser = require('body-parser');

const app = express();
const port = process.env.PORT || 3000;

app.use(bodyParser.json());

// Discord Bot Setup
const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.MessageContent,
    GatewayIntentBits.GuildMembers,
  ],
});

const DISCORD_TOKEN = process.env.MTQ2MDk1ODY1MDY2NjMxOTkxMw.G-OZ2g.BsxOur3nrvuVYhDL6tx5tKuma6MAWEe9RzJ9zI;
const PRIMARY_CHANNEL_ID = process.env.1461710247969292313; // e.g., '123456789012345678'
const QUEUE_CHANNEL_ID = process.env.1461710247969292316; // e.g., '987654321098765432'

client.once('ready', () => {
  console.log(`Logged in as ${client.user.tag}`);
});

client.on('interactionCreate', async (interaction) => {
  if (!interaction.isButton()) return;

  const { customId, message } = interaction;

  if (customId === 'claim') {
    // Migrate to queue channel
    const queueChannel = client.channels.cache.get(QUEUE_CHANNEL_ID);
    if (queueChannel) {
      const embed = new EmbedBuilder()
        .setColor(0x00FF00)
        .setTitle('Claimed Token')
        .setDescription(`Token: ${message.embeds[0].data.description}\nDetails: ${message.embeds[0].data.fields[0].value}`)
        .setTimestamp();

      await queueChannel.send({ embeds: [embed] });
      await interaction.reply({ content: 'Claimed and queued!', ephemeral: true });
    }
  } else if (customId === 'decline') {
    await interaction.reply({ content: 'Declined.', ephemeral: true });
  }

  // Remove buttons after interaction
  await message.edit({ components: [] });
});

// Webhook Endpoint
app.post('/webhook', async (req, res) => {
  const payload = req.body;
  console.log('Received webhook:', payload);

  // Parse payload (assume { token: string, details: string })
  const { token, details } = payload;

  if (!token || !details) {
    return res.status(400).send('Invalid payload');
  }

  const primaryChannel = client.channels.cache.get(PRIMARY_CHANNEL_ID);
  if (!primaryChannel) {
    return res.status(500).send('Channel not found');
  }

  // Create embed with buttons
  const embed = new EmbedBuilder()
    .setColor(0x0099FF)
    .setTitle('New Webhook Alert')
    .setDescription(token)
    .addFields({ name: 'Details', value: details })
    .setTimestamp();

  const row = new ActionRowBuilder()
    .addComponents(
      new ButtonBuilder().setCustomId('claim').setLabel('Claim').setStyle(ButtonStyle.Primary),
      new ButtonBuilder().setCustomId('decline').setLabel('Decline').setStyle(ButtonStyle.Secondary)
    );

  await primaryChannel.send({ embeds: [embed], components: [row] });

  res.status(200).send('Processed');
});

// Health Endpoint for Pinging
app.get('/health', (req, res) => {
  res.status(200).send('OK');
});

client.login(DISCORD_TOKEN);

app.listen(port, () => {
  console.log(`Server listening on port ${port}`);
});
