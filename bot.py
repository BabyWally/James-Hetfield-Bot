import discord
from discord.ext import commands, tasks
import asyncio
import random
from datetime import datetime, timedelta
import logging
import os
import pytz
import threading
import time
import requests
from flask import Flask

# Set up logging for debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# Bot Intents
intents = discord.Intents.default()
intents.message_content = True  # Enable message content intent
intents.reactions = True  # Enable reaction events
bot = commands.Bot(command_prefix="!", intents=intents)

# Get the bot token from environment variables
TOKEN = os.getenv("DISCORD_BOT_TOKEN")  # Make sure this is set

# List of channel IDs where messages will be sent
CHANNEL_IDS = [
    1349240997367910431,
    1346995577493262417,
    1346996270492811335,
    1346996294081712129,
    1346986331112341604,
    1347021777271787520
]

# List of possible messages
MESSAGES = [
    "Howy fuwcking shit. I want to bang James Hetfield so goddamn bad...",
    "Holy fucking shit. I want to bang James Hetfield so goddamn bad...",
    "-# Oh, my heavens, what an utterly astonishing and profoundly breathtaking situation..."
]

# Time zone setup
timezone = pytz.timezone('America/Denver')  # Change this as needed

# Store scheduled message times
next_times = []
stop_replies = False  # Default: Replies are enabled
sent_message_ids = {}  # Store bot message IDs for reply tracking

### === KEEP-ALIVE SCRIPT === ###
def keep_alive():
    """Keep the bot alive by pinging the Replit server periodically."""
    url = 'https://replit.com/@aoruaglendal/James-Hetfield-Bot?v=1'  # Replace with your Replit URL
    while True:
        try:
            requests.get(url)
            print("Pinged the server!")
        except requests.exceptions.RequestException as e:
            print(f"Error pinging server: {e}")
        time.sleep(300)  # Ping every 5 minutes

# Run keep-alive in a separate thread
threading.Thread(target=keep_alive, daemon=True).start()

### === BOT EVENTS === ###

@bot.event
async def on_ready():
    """Triggered when the bot successfully connects."""
    print(f"✅ Logged in as {bot.user}")
    logger.info(f"✅ Logged in as {bot.user}")

    schedule_next_messages()
    if not daily_message.is_running():
        daily_message.start()

def schedule_next_messages():
    """Schedules 1-2 messages at random times between 8 AM - 10 PM."""
    global next_times
    now = datetime.now(timezone)
    next_times = []

    for _ in range(random.choice([1, 2])):  # Randomly choose 1 or 2 messages per day
        random_time = now.replace(
            hour=random.randint(8, 22),
            minute=random.randint(0, 59),
            second=0,
            microsecond=0
        )
        if random_time < now:
            random_time += timedelta(days=1)  # Ensure scheduling in the future
        next_times.append(random_time)

    next_times.sort()
    print(f"📅 Scheduled messages at: {', '.join(t.strftime('%H:%M %Z') for t in next_times)}")
    logger.info(f"📅 Scheduled messages at: {', '.join(t.strftime('%H:%M %Z') for t in next_times)}")

@tasks.loop(minutes=1)
async def daily_message():
    """Sends a random message to all channels at scheduled times."""
    global next_times
    now = datetime.now(timezone)

    for scheduled_time in next_times[:]:  # Iterate over a copy
        if now >= scheduled_time:
            message = random.choice(MESSAGES)
            for channel_id in CHANNEL_IDS:
                channel = bot.get_channel(channel_id)
                if channel:
                    sent_message = await channel.send(message)
                    sent_message_ids.setdefault(channel_id, []).append(sent_message.id)  # Track sent messages
            next_times.remove(scheduled_time)  # Remove sent message time

    if not next_times:  # Reschedule for the next day
        schedule_next_messages()

### === MESSAGE HANDLER === ###
@bot.event
async def on_message(message):
    """Handles message responses and reactions."""
    global stop_replies

    if message.author == bot.user:  # Prevent bot from reacting to itself
        return

    # Allow commands to work even if replies are stopped
    if message.content.startswith('!'):
        await bot.process_commands(message)
        return

    # If stop_replies is True, don't react or reply
    if stop_replies:
        return

    content_lower = message.content.lower()  # Convert to lowercase

    # "james, do it jiggle" Trigger
    if "james, do it jiggle" in content_lower:
        emoji = discord.PartialEmoji(name="noose", id=1350638418341924944)  # Custom emoji ID
        try:
            await message.add_reaction(emoji)
        except discord.HTTPException:
            await message.channel.send("🚫 I can't add the reaction!")

        phrase = random.choice(["No, it doesn't.", "kill yourself"])
        sticker_id = 1350651458738982952  # Correct sticker ID
        sticker = discord.utils.get(message.guild.stickers, id=sticker_id)

        if sticker:
            await message.channel.send(phrase, stickers=[sticker])
        else:
            await message.channel.send(phrase)  # Send phrase even if sticker isn't found

    # "ride the lightning" Trigger
    elif "ride the lightning" in content_lower:
        emoji = discord.PartialEmoji(name="jamcheeks", id=1349242680160419860)  # Custom emoji ID
        try:
            await message.add_reaction(emoji)
        except discord.HTTPException:
            await message.channel.send("⚡ I can't react with the lightning emoji!")

        phrase = random.choice([
            f"{message.author.mention} Who wants to ride my lightning? ⚡",
            f"{message.author.mention} ME ME ME!"
        ])
        await message.channel.send(phrase)

    # Allow other bot commands to process
    await bot.process_commands(message)

# Define the allowed user ID (Replace with actual Discord ID)
ALLOWED_USER_ID = 470801649221500938  # Change this to the ID of the user who can use restricted commands

# Function to check if the user is allowed
def is_allowed_user():
    async def predicate(ctx):
        if ctx.author.id != ALLOWED_USER_ID:
            await ctx.send("❌ You do not have permission to use this command!")
            return False
        return True
    return commands.check(predicate)

@bot.command()
@is_allowed_user()
async def countdown(ctx):
    """Counts down from 10 and then pings the user."""
    user_id = 1076322897389441054  # Target user ID
    user = await bot.fetch_user(user_id)  # Fetch user by ID

    if not user:
        await ctx.send("User not found!")
        return

    for i in range(10, 0, -1):  # Countdown from 10 to 1
        await ctx.send(f"{i}...")
        await asyncio.sleep(1)  # Wait 1 second between messages

    await ctx.send(f"{user.mention}, TIME'S UP FUCKER! ⏳")

@bot.command()
@commands.has_permissions(administrator=True)
async def kill_monkeys(ctx):
    """Kills all monkeys in the server. Only admins can use this."""
    await ctx.send("Killing all monkeys in the server...")

@bot.command()
async def ping(ctx):
    """Responds with the bot's latency."""
    latency = round(bot.latency * 1000)  # Convert to milliseconds
    await ctx.send(f"Pong! 🏓 {latency}ms")

@bot.command()
@is_allowed_user()
async def stopreplies(ctx):
    """Stops the bot from replying to messages."""
    global stop_replies
    stop_replies = True
    await ctx.send("Replies have been stopped.")

@bot.command()
@is_allowed_user()
async def startreplies(ctx):
    """Starts the bot replying to messages again."""
    global stop_replies
    stop_replies = False
    await ctx.send("Replies have been started again.")

@bot.command()
@is_allowed_user()
async def compliment(ctx):
    """Compliments a specific user."""
    user_id = 470801649221500938  # Hardcoded user ID
    user = await bot.fetch_user(user_id)  # Fetch user by ID
    if user:
        compliment = random.choice([
            "You are amazing!",
            "You're an absolute legend!",
            "You're the best!",
            "I hope you know how awesome you are!",
            "You brighten up everyone's day!",
            "You're incredibly talented!",
            "You're a superstar!",
            "You are one of a kind!"
        ])  # Choose a random compliment
        await ctx.send(f"{user.mention}, {compliment}")
    else:
        await ctx.send("User not found!")

@bot.command()
@is_allowed_user()
async def metallica_explosion(ctx):
    """Creates a Metallica Explosion using a custom emoji."""
    metallica_emoji = "<:metallica_explosion:1350222287621722113>"  # Custom emoji format

    explosion = f"""
    {metallica_emoji}💥💥💥💥{metallica_emoji}
    💥🔥🔥🔥💥
    💥🔥{metallica_emoji}🔥💥
    💥🔥🔥🔥💥
    {metallica_emoji}💥💥💥💥{metallica_emoji}
    """

    await ctx.send(explosion)

OWNER_ID = 470801649221500938  # Your Discord user ID

@bot.event
async def on_message(message):
    if message.author.id == OWNER_ID and isinstance(message.channel, discord.DMChannel):
        if message.content.lower() == "stop":
            await message.channel.send("Shutting down...")
            await bot.close()
        elif message.content.lower() == "status":
            await message.channel.send("Bot is running.")
        elif message.content.lower() == "send":
            channel = bot.get_channel(1349240997367910431)
            if channel:
                await channel.send("Hello from the owner!")
                await message.channel.send("Message sent.")
            else:
                await message.channel.send("Channel not found.")
    await bot.process_commands(message)  # Allow other commands to work


### === FLASK SERVER === ###

app = Flask('')

@app.route('/')
def home():
    return 'James is running! Better go catch him! HAHA...'

def run():
    app.run(host='0.0.0.0', port=8080)

# Run Flask in a separate thread to keep bot alive
threading.Thread(target=run).start()

### === RUN BOT === ###

while True:
        try:
            bot.run(TOKEN)
        except discord.errors.HTTPException as e:
            if e.status == 429:  # Rate limit error
                retry_after = e.response.headers.get('Retry-After', 30)
                print(f"Rate limited. Waiting {retry_after} seconds...")
                time.sleep(float(retry_after))
                continue
            raise  # Re-raise other HTTP exceptions
        except Exception as e:
            print(f"Error occurred: {e}")
            time.sleep(60)  # Wait before retry
            continue
