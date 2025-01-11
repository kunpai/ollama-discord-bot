import discord
from discord.ext import commands
from discord import app_commands
from ollama import chat, ChatResponse
from dotenv import load_dotenv
import os

# Load environment variables from a .env file
load_dotenv()

intents = discord.Intents.default()
intents.message_content = True  # Enable access to message content

bot = commands.Bot(command_prefix='!', intents=intents)

@app_commands.command(name='ask', description='Ask a question to the Chussu model')
async def ask(interaction: discord.Interaction, question: str):
    await interaction.response.defer()  # Acknowledge the interaction and defer the response
    try:
        # Query the Ollama model
        response: ChatResponse = chat(model='chussu:latest', messages=[
            {'role': 'user', 'content': question},
        ])
        # Send the response back to the Discord channel
        await interaction.followup.send(response.message.content)
    except Exception as e:
        await interaction.followup.send(f"An error occurred: {e}")

bot.tree.add_command(ask)


@bot.event
async def on_message(message):
    # Ignore messages sent by the bot itself to prevent infinite loops
    if message.author == bot.user:
        return

    # Check if the message is a reply to another message
    if message.reference and message.reference.message_id:
        # Fetch the original message being replied to
        original_message = await message.channel.fetch_message(message.reference.message_id)

        # Check if the original message was sent by the bot
        if original_message.author == bot.user:
            # Process the reply as a question to the model
            question = message.content
            await process_question(message.channel, question)
    elif bot.user in message.mentions:
        # Remove the bot mention from the message content to extract the question
        question = message.content.replace(bot.user.mention, '').strip()
        await process_question(message.channel, question)
    else:
        # Process regular messages or commands as needed
        await bot.process_commands(message)

async def process_question(channel, question):
    try:
        # Query the Ollama model
        response: ChatResponse = chat(model='chussu:latest', messages=[
            {'role': 'user', 'content': question},
        ])
        # Send the response back to the channel
        await channel.send(response.message.content)
    except Exception as e:
        await channel.send(f"An error occurred: {e}")

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'Logged in as {bot.user}')

# Run the bot with your token
bot.run(os.getenv('DISCORD'))
