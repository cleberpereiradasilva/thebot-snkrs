import discord
from discord.ext import commands
import random


client = commands.Bot(command_prefix = ">", case_sensitive = True)

@client.event
async def on_ready():
    print("Entramos {0.user}".format(client))

@client.command()
async def numero(ctx):
    await ctx.send('{}'.format(str(random.randint(1,10))))

client.run('ODcyMTMxNjcwMTcyNjQzMzkw.YQlZ6Q.zA0cQSXd3-o1lE47Ni-o3r692_Q')
