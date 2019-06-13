import asyncio
import discord
import sqlite3

import player
from bot_utils import *
import player_state as p_state

# CONSTANTS
BOT_ID = ''
DEFAULT_MESSAGE_DELAY = 2
DEFAULT_NEW_PLAYER_CARD = 'money button'
KEY_PATH = 'key.txt'

# GLOBALS
conn = sqlite3.connect('test_db.db')
players_in_session = []

client = discord.Client()


@client.event
def on_ready():
    print('Ready.')


@client.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    session_player = player.get_player(conn, message.author.id)
    if session_player is None:
        await message.channel.send('Please create an account with !join')
        return
    if not message.content.startswtih('!'):
        return
    # Block player from being handled twice at once
    players_in_session.append(session_player)
    terms = message.content[1:].split(' ')
    command = terms[0]
    if len(terms) > 1:
        terms = terms[1:]
    terms = terms[1:]
    if command == 'inventory':
        await inventory_command(message, session_player)
    elif command == 'row':
        await row_command(message, session_player, int(terms[0]))
    elif command == 'select':
        if len(terms) == 2:
            await select_command(message, session_player, int(terms[0]), int(terms[1]))
        else:
            await select_command(message, session_player, int(terms[0]))
    elif command == 'card':
        await card_command(message, session_player, terms[0], terms[1])
    elif command == 'help':
        pass
    else:
        pass
    players_in_session.remove(session_player)


async def inventory_command(message: discord.Message, session_player: player.Player):
    msg = '```'+session_player.render()+'```'
    await message.channel.send(msg)
    p_state.set_player_state(session_player.get_discord_id(), p_state.InventoryState())


async def row_command(message: discord.Message, session_player: player.Player, row_index: int):
    msg = '```'+session_player.get_row(row_index).render()+'```'
    await message.channel.send(msg)
    p_state.set_player_state(session_player.id, p_state.RowState(row_index))


async def card_command(message: discord.Message, session_player: player.Player, row_index: int, card_index: int):
    msg = '```'+session_player.get_row(row_index).get_card(card_index).render()+'```'
    await message.channel.send(msg)
    p_state.set_player_state(session_player.id, p_state.CardState(row_index, card_index))


async def shop_command(message: discord.Message, session_player: player.Player, shop_index):
    pass  # TODO: show shop (need to implement first)


async def shop_menu_command(message: discord.Message, session_player: player.Player):
    pass  # TODO: show shop menu(need to implement first)


async def select_command(message: discord.Message, session_player: player.Player, param1: int, param2: int=None):
    state = p_state.get_player_state(session_player.id)
    if isinstance(state, p_state.RowState):  # Browsing 1 row
        await card_command(message, session_player, state.row_index, param1)
    elif isinstance(state, p_state.InventoryState):  # Looking at all rows
        await row_command(message, session_player, param1)
    elif isinstance(state, p_state.ShopMenuState):  # Looking at all shops
        pass  # TODO
    elif isinstance(state, p_state.ShopState):  # Browsing 1 shop
        pass  # TODO
    else:
        msg = 'Nothing to select!'
        await message.channel.send(msg)


async def help_command(message: discord.Message, session_player: player.Player):
    pass
    # TODO: Show general help menu, and state specific help if applicable


async def player_creation(message):
    channel = message.channel
    p_name = await player_input(message, 'What do you want to be named?')
    new_player = player.register_new_player(conn, message.author.id, p_name)
    row = new_player.add_row()
    row.add_card(DEFAULT_NEW_PLAYER_CARD)
    channel.send('You are now registered to play.' +
                 'I\'ve given you a card to start you off.')

    response = await yes_or_no(message, 'Do the (short) tutorial?')
    if response == 'yes':
        await tutorial(message, new_player)
    else:
        channel.send('Alright. You have been given one card to start off. Type !help to see commands. Good Luck!')


async def tutorial(message, session_player: player.Player):
    channel = message.channel
    await channel.send('In this game, you collect Cards that work together in unique ways to create resources.')
    await asyncio.sleep(DEFAULT_MESSAGE_DELAY)
    await ask_loop(message, 'Lets look at that card I gave you.\n' +
                            'Pull up your inventory with !inventory.', ['!inventory'],
                            restated_question='Pull up your inventory with !inventory.')
    await channel.send('Your inventory is organised into rows, and each as several slots for storing cards. ' +
                       'As a new player, you only have 1 row.')
    await asyncio.sleep(DEFAULT_MESSAGE_DELAY)
    await ask_loop(message, 'Pull it up with !select 1.', ['!select 1'])
    # TODO Display rows
    await channel.send('As you can see, you only have 1 card in this row. Each row can have a maximum of 12 cards. ' +
                       'In the future, you can quickly pull up a row at any time with !row <index>.')
    await asyncio.sleep(DEFAULT_MESSAGE_DELAY)
    await ask_loop(message, 'Now, pull up your first card with !select 1.', ['!select 1'])
    # TODO: Display the card
    await channel.send('As you can see, Each card has a Name, a Rarity(Top right), a description, ' +
                       'and resources(on the bottom).')
    await asyncio.sleep(DEFAULT_MESSAGE_DELAY)
    await channel.send('This card can store money, of which it has 0 out of a maximum of 50.')
    await asyncio.sleep(DEFAULT_MESSAGE_DELAY)
    await channel.send('Cards do a wide variety of things: produce all sorts of resources, boost the production ' +
                       'of other cards, convert between resources, and even form complex card-machines.\n' +
                       'This card, however, just produces money when you use it.')
    await asyncio.sleep(DEFAULT_MESSAGE_DELAY)
    await channel.send('Each card either does these things passively, when activated with !use, or both.')
    await asyncio.sleep(DEFAULT_MESSAGE_DELAY)
    await ask_loop(message, 'To "use" a card, Type !use. Try it now.', ['!use'], 'Type !use to use this card.')
    # TODO: show the changed card
    await channel.send('Look. Now you have 1 money.')
    await asyncio.sleep(DEFAULT_MESSAGE_DELAY)
    await ask_loop(message, 'Next, check out the shop menu. Type !shop.',
                   ['!shop'],
                   'Please pull up the shop menu with !shop.')
    # TODO: Show shop menu
    await ask_loop(message, 'Here you will see all the shops you can buy cards from. '
                            'For now, you only have one unlocked. Select it with !select 1.',
                            ['select 1'],
                            'Select it with !select 1.')
    # TODO: Show shop
    await channel.send('That\'s a lot of information. As you can see, the seller has several cards for sale.')
    await asyncio.sleep(DEFAULT_MESSAGE_DELAY)
    await channel.send('When you buy a card, its cost is automatically deducted from cards in your inventory. ' +
                       'Since you only have 1 money, you can\'t afford any of these cards just yet.')
    await asyncio.sleep(DEFAULT_MESSAGE_DELAY)
    await ask_loop(message, 'Lets examine a card for sale. Type !select 5.', ['!select 5'])
    await channel.send('This card has rarity EPIC -- quite a bit more powerful (and expensive) than what you have. ' +
                       'With enough patience, planning, and teamwork, ' +
                       'you will be able to fill your inventory with cards like this.')
    await asyncio.sleep(DEFAULT_MESSAGE_DELAY)
    channel.send('That should be enough for you to learn the ropes. Feel free to ask around for help, ' +
                 'and type !help to show the command list. Good luck!')

if __name__ == '__main__':
    with open(KEY_PATH, 'r') as f:
        key = f.read()
    client.run(key)
