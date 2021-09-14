# UofT Verification Bot written by Snow
from __future__ import unicode_literals

import os

import sqlalchemy as db

import discord
from dotenv import load_dotenv

from random import randrange

import smtplib, ssl
from validate_email import validate_email

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = int(os.getenv('DISCORD_GUILD'))
SENDER = os.getenv('EMAIL')
PASSWORD = os.getenv('PASSWORD')
SERVER = os.getenv('SERVER')
PORT = os.getenv('SERVER_PORT')
uri = os.getenv('DATABASE_URL')

if uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)

engine = db.create_engine(uri)
connection = engine.connect()
metadata = db.MetaData()
users = db.Table('Users', metadata, autoload=True, autoload_with=engine)

intents = discord.Intents.all()
client = discord.Client(intents=intents)


@client.event
async def on_member_join(member):
    await member.send("To gain access to the server, please verify your UofT email. \n"
                      "Enter '!email' followed by your UofT email, or '!help' for more commands.")
    await initiate(member)


@client.event
async def on_ready():
    print("Ready")


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.channel.type != discord.ChannelType.private:
        return

    user_id = str(message.author.id)

    if not user_exists(user_id):
        await initiate(message.author)
        # await message.author.send('You do not seem to be a member of UofTCTF. Please join and try again.')

    if message.content[:7] == "!email ":
        email = message.content.split(' ')[1].strip()
        if not resendable(user_id):
            await message.author.send("You have been blocked from requesting your verification code. "
                                      "Please contact us directly.")
        elif email_valid(email):
            store_email(user_id, email)
            if send_email(email, get_code(user_id)):
                decrement_resends(user_id)
                await message.author.send("A code has been sent to your email. "
                                          "Please enter '!code' followed by your code.")
            else:
                await message.author.send("An email could not be sent to your email. Please contact us directly.")
        else:
            await message.author.send("Your email appears to be invalid/restricted. Please enter your email again.")
    elif message.content[:6] == "!code ":
        code = message.content.split(' ')[1].strip()
        if not attemptable(user_id):
            await message.author.send("You have been blocked for too many attempts. Please contact us directly.")
        else:
            decrement_attempts(user_id)
            if code_valid(user_id, code):
                await verify(message.author)
                await message.author.send("Your email has been validated successfully - welcome!")
            else:
                await message.author.send("The code you have entered is invalid, please try again or request the code "
                                          "again.")
    elif message.content[:8] == "!resend ":
        email = message.content.split(' ')[1].strip()
        if not resendable(user_id):
            await message.author.send("You have been blocked from requesting your verification code. "
                                      "Please contact us directly.")
        elif email_valid(email):
            store_email(user_id, email)
            if send_email(email, get_code(user_id)):
                decrement_resends(user_id)
                await message.author.send("A code has been sent to your email. "
                                          "Please enter '!code' followed by your code.")
            else:
                await message.author.send("An email could not be sent to your email. Please contact us directly.")
        else:
            await message.author.send("Your email appears to be invalid/restricted. Please enter your email again.")
    elif message.content[:6] == "!help":
        await message.author.send("!email {your email address}: Submit your UofT email for verification. \n"
                                  "!code {your verification code}: Enter the code sent to your UofT email. \n"
                                  "!resend {your email address}: Request a new code to be sent to your UofT email")
    elif message.content == "":
        pass
    elif message.content[:1] == "!":
        await message.author.send("Command not recognized. Type '!help' for a list of commands.")


def code_valid(user_id, code):
    query = db.select([users])
    query = query.where(users.columns.id == user_id)
    result = connection.execute(query)
    return code == result.fetchall()[0].code


def get_code(user_id):
    query = db.select([users])
    query = query.where(users.columns.id == user_id)
    result = connection.execute(query)
    return result.fetchall()[0].code


def get_email(user_id):
    query = db.select([users])
    query = query.where(users.columns.id == user_id)
    result = connection.execute(query)
    return result.fetchall()[0].email


def email_valid(email):
    if not validate_email(email, check_smtp=False):
        return False
    if email[email.find('@') + 1:] != "mail.utoronto.ca":
        return False
    return True


def user_exists(user_id):
    query = db.select([users])
    query = query.where(users.columns.id == user_id)
    result = connection.execute(query)
    return result.first() is not None


def store_email(user_id, email):
    query = db.update(users).values(email=email)
    query = query.where(users.columns.id == user_id)
    connection.execute(query)


async def initiate(member):
    if not user_exists(str(member.id)):
        query = db.insert(users).values(id=member.id, code=randrange(100000, 1000000), resends=5, attempts=5)
        connection.execute(query)


def decrement_resends(user_id):
    query = db.select([users])
    query = query.where(users.columns.id == user_id)
    result = connection.execute(query)

    resends = result.fetchall()[0].resends - 1
    query = db.update(users).values(resends=resends)
    query = query.where(users.columns.id == user_id)
    connection.execute(query)
    return resends


def decrement_attempts(user_id):
    query = db.select([users])
    query = query.where(users.columns.id == user_id)
    result = connection.execute(query)

    attempts = result.fetchall()[0].attempts - 1
    query = db.update(users).values(attempts=attempts)
    query = query.where(users.columns.id == user_id)
    connection.execute(query)
    return attempts


def log():
    # print(users.columns.keys())
    # print(repr(metadata.tables['Users']))
    query = db.select([users])
    result = connection.execute(query)
    print(result.fetchall())


def send_email(email, code):
    try:
        server = smtplib.SMTP(SERVER, PORT)
        server.connect(SERVER, PORT)
        server.starttls()
        server.login(SENDER, PASSWORD)
        server.sendmail(SENDER, email, f"Your verification code is: {code}")
        server.quit()
        return True
    except Exception as e:
        print(e)
        return False


def get_guild():
    for guild in client.guilds:
        if guild.id == GUILD:
            return guild


async def verify(user):
    guild = get_guild()
    member = guild.get_member(user.id)
    role = discord.utils.get(guild.roles, name="verified")
    await member.add_roles(role)


def resendable(user_id):
    query = db.select([users])
    query = query.where(users.columns.id == user_id)
    result = connection.execute(query)

    resends = result.fetchall()[0].resends
    return resends > 0


def attemptable(user_id):
    query = db.select([users])
    query = query.where(users.columns.id == user_id)
    result = connection.execute(query)

    attempts = result.fetchall()[0].attempts
    return attempts > 0


if __name__ == "__main__":
    client.run(TOKEN)
