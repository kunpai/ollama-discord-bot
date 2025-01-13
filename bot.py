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

# Supported models and their default behavior
SUPPORTED_MODELS = ['chussu', 'kiwi', 'babloo']
DEFAULT_MODEL = 'chussu'

# A mapping to store model references for continued conversations
message_model_map = {}

@app_commands.command(name='ask', description='Ask a question to the specified model')
@app_commands.describe(
    question='The question you want to ask',
    model='The model to query'
)
@app_commands.choices(model=[
    app_commands.Choice(name=model, value=model) for model in SUPPORTED_MODELS
])
async def ask(interaction: discord.Interaction, question: str, model: app_commands.Choice[str]):
    await interaction.response.defer()  # Acknowledge the interaction and defer the response
    await query_model(interaction.followup.send, question, model.value)

bot.tree.add_command(ask)

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    print(f"Received message: {message.content}")
    # Parse mentions like "<@BOT_ID> chussu: What is the meaning of life?"
    if bot.user.mention in message.content:
        print("Mention detected")
        content = message.content.replace(bot.user.mention, '').strip()
        model, question = parse_model_and_question(content)
        if question:  # Valid question extracted
            await query_model(message.channel.send, question, model)
        return

    # Check if it's a reply to another bot message
    if message.reference and message.reference.message_id:
        print("Reply detected")
        original_message = await message.channel.fetch_message(message.reference.message_id)
        print(f"Original message: {original_message.content}")
        print(message_model_map)
        if original_message.id in message_model_map:
            model = message_model_map[original_message.id]
            question = message.content.strip()
            print(f"Model: {model}, Question: {question}")
            await query_model(message.channel.send, question, model)
            return

    # Process commands if no special case applies
    await bot.process_commands(message)

def parse_model_and_question(content):
    """
    Parses a message to extract the model and question.
    - Format: "chussu: What is the meaning of life?"
    - If no model is specified, defaults to DEFAULT_MODEL.
    """
    for model in SUPPORTED_MODELS:
        if content.startswith(f"{model}:"):
            question = content[len(f"{model}:"):].strip()
            return model, question

    # Default behavior if no model prefix is found
    return DEFAULT_MODEL, content

async def query_model(send_response, question, model):
    """
    Queries the specified model and sends the response to the given output method.
    """
    try:
        response: ChatResponse = chat(model=f'{model}:latest', messages=[
            {'role': 'user', 'content': question},
        ])
        bot_message = await send_response(f"{model.title()}: {response.message.content}")
        # Update the message_model_map with the bot's response message ID
        message_model_map[bot_message.id] = model
    except Exception as e:
        await send_response(f"An error occurred: {e}")

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'Logged in as {bot.user}')

# Run the bot with your token
bot.run(os.getenv('DISCORD'))
