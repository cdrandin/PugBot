import json
# Commands #
from commands.pug_orm import pug
from commands.utils import pug_set_calls

import discord

with open('config.json', 'r') as infile:
    config = json.loads(infile.read())  # Load Configs
    DISCORD_TOKEN = config["discord_token"]

client = discord.Client()


@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')


@client.event
async def on_message(message):
    if message.content.startswith('!info') or message.content.startswith('!help'):
        await client.send_message(message.channel, "I'm PugBot, the pug analyzer!\n"
                                                   "Use: !pug <name> <server> \n"
                                                   "Example: !pug Basimot Lightbringer")

    if message.content.startswith('!pug'):
        await pug(client, message)

client.run(DISCORD_TOKEN)
