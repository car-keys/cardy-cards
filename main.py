# lol, TODO
import discord, sqlite3, player, asyncio
BOT_ID = ''
conn = sqlite3.connect('test_db.db')

client = discord.Client()


@client.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    session_player = player.get_player(message.author.id, conn)
    if session_player is None:
        await message.channel.send('Please create an account with !join')


async def ask_loop(message: discord.Message, question: str, responses: list,
                   restated_question: str = None, tries: int = -1,
                   timeout: int = 60, case_sensitive=False) -> str:
    """
    Asks for a response. Will keep asking until a correct response is given, the message times out,
    or the user runs out of tries.
    Parameters:
        message: Discord Message from the player in the correct channel.
        question: The question to ask.
        restated_question: A (shortened) form when repeating the question.
        tries: How many times to try asking before giving up. If set to -1, will try forever.
        timeout: How long to wait before giving up. In seconds.
        responses: List of valid responses.
        case_sensitive: if no, all responses are converted to lowercase.
    """
    message.channel.send(question)

    def check(m: discord.Message):
        return m.author == message.author and m.channel == message.channel

    if restated_question is None:
        restated_question = question
    while 1:
        msg = await message.channel.wait_for('message', check=check, timeout=timeout)
        if case_sensitive:
            if msg.content in responses:
                return msg.content
        else:
            if msg.content.lower() in responses:
                return msg.content
        tries -= 1
        if tries == 0:
            raise asyncio.TimeoutError('Out of tries')
        message.channel.send(restated_question)


async def yes_or_no(message: discord.Message, question: str,
                    restated_question: str = None, tries: int = -1, timeout: int = 60):
    """Special case of ask_loop, to ask a yes or no question. Do not include the (y/n) in the message."""
    question += ' (y/n)'
    restated_question += ' (y/n)'
    yeses = ['yes', 'y', 'yep', 'ye', 'yep', 'yeet']
    nos = ['no', 'n', 'nope', 'nada']
    response = await ask_loop(message, question, yeses+nos, restated_question, tries, timeout)
    if response in yeses:
        return 'yes'
    return 'no'


async def player_input(message: discord.Message, question: str, timeout: int = 60):
    """Asks for a response to given question."""
    def check(m):
        return m.channel == message.channel and m.author == message.author
    return message.channel.wait_for(question, check=check, timeout=timeout)


async def player_creation(message):
    channel = message.channel
    p_name = await player_input(message, 'What do you want to be named?')
    # TODO: make a new player, add first card (money_button)
    channel.send('You are now registered to play. say !inventory to see an overview of your inventory --' +
                 'I\'ve given you a card to start you off.')

    response = await yes_or_no(message, 'Do the (short) tutorial?')
    if response == 'yes':
        await tutorial(message.channel)
    else:
        channel.send('Alright. You have been given one card to start off. Type !help to see commands. Good Luck!')


async def tutorial(channel):
    channel.send('In this game, you collect Cards that work together in unique ways to create resources.')
    channel.send('Lets look at that card I gave you. Its in the first slot of the first row of your inventory.\n' +
                 'Pull up your inventory with !inventory.')
    channel.send('Your inventory is organised into rows, and each as several slots for storing cards. ' +
                 'As a new player, you only have 1 row.')
    channel.send('Pull it up with !select 1.')
    channel.send('As you can see, you only have 1 card in this row. Pull it up with !select 1.')
    channel.send('Please Pull up the card with !card 1 1')
    channel.send('As you can see, Each card has a Name, a Rarity(Top right), a description, ' +
                 'and resources(on the bottom).')
    channel.send('This card can store money, of which it as 0 out of a maximum of 50.')
    channel.send('Each card either does things passively, is activated with !use, or both.')
    channel.send('Cards do a wide variety of things: produce all sorts of resources, boost the production ' +
                 'of other cards, convert between resources, and even form complex card-machines.\n' +
                 'This card, however, just produces money when you use it.')
    channel.send('To use a card, Type !use. Try it now.')
    channel.send('Type !use to use this card.')
    channel.send('Look. Now you have 1 money.')
    channel.send('Next, check out the shop menu. Type !shop.')
    channel.send('Please pull up the shop menu with !shop.')
    channel.send('Here you will see all the shops you can buy cards from. '
                 'For now, you only have one unlocked. Select it with !select 1.')
    channel.send('That\'s a lot of information. As you can see, the seller has several cards for sale.')
    channel.send('When you buy a card, its cost is automatically deducted from cards in your inventory. ' +
                 'Since you only have 1 money, you can\'t afford any of these cards just yet. ' +
                 'Lets examine a card for sale. Type !select 5.')
    channel.send('This card has rarity EPIC -- quite a bit more powerful (and expensive) than what you have. ' +
                 'With enough patience, planning, and teamwork, ' +
                 'you will be able to fill your inventory with cards like this.')
    channel.send('That should be enough for you to learn the ropes. Feel free to ask around for help, ' +
                 'and type !help to show the command list. Good luck!')


@client.event
def on_ready():
    print('Ready.')
