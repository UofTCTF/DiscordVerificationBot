# UofT Verification Bot written by Snow
from __future__ import unicode_literals

import os

import sqlalchemy as db

import discord
from dotenv import load_dotenv

from random import randrange

from validate_email import validate_email

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = int(os.getenv('DISCORD_GUILD'))

engine = db.create_engine('sqlite:///site.db')
connection = engine.connect()
metadata = db.MetaData()
users = db.Table('Users', metadata, autoload=True, autoload_with=engine)

intents = discord.Intents.all()
client = discord.Client(intents=intents)


@client.event
async def on_member_join(member):
    await initiate(member)


@client.event
async def on_ready():
    for guild in client.guilds:
        print(guild.name)


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if not user_exists(str(message.author.id)):
        await message.author.send('You do not seem to be a member of UofTCTF. Please join and try again.')

    if message.content[:7] == "!email ":
        email = message.content.split(' ')[1].strip()
        if email_valid(email):
            store_email(message.author.id, email)
            await message.author.send("A code has been sent to your email. Please enter your code.")
        else:
            await message.author.send("Your email appears to be invalid/restricted. Please enter your email again.")
    elif message.content[:6] == "!code ":
        code = message.content.split(' ')[1].strip()
        if code_valid(message.author.id, code):
            await message.author.send("Your email has been validated successfully - welcome!")
        else:
            await message.author.send("The code you have entered is invalid, please try again or request the code "
                                      "again.")
    elif message.content[:6] == "!help":
        await message.author.send("!email {your email address} \n"
                                  "!code {your verification code}")
    elif message.content == "":
        pass
    else:
        await message.author.send("Command not recognized. Type '!help' for a list of commands.")


def code_valid(user_id, code):
    query = db.select([users])
    query = query.where(users.columns.id == user_id)
    result = connection.execute(query)
    return code == result.fetchall()[0].code


def email_valid(email):
    if not validate_email(email, check_smtp=False):
        return False
    if email.split("@")[1] != "mail.utoronto.ca":
        return False
    return True


def user_exists(user_id):
    query = db.select([users])
    result = connection.execute(query)
    for user in result:
        if user_id == user[0]:
            return True
    return False


def store_email(user_id, email):
    query = db.update(users).values(email=email)
    query = query.where(users.columns.id == user_id)
    connection.execute(query)


async def initiate(member):
    await member.send('To gain access to the server, please verify your UofT email. \n'
                      'Enter "!email" followed by your UofT email, or "!help" for more commands.')
    if not user_exists(str(member.id)):
        query = db.insert(users).values(id=member.id, code=randrange(100000, 1000000))
        connection.execute(query)


def log():
    # print(users.columns.keys())
    # print(repr(metadata.tables['Users']))
    query = db.select([users])
    result = connection.execute(query)
    print(result.fetchall())


client.run(TOKEN)
