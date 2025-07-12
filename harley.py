import discord
from discord import app_commands
from discord.ext import commands, tasks
from discord.ext.tasks import loop
import logging
from dotenv import load_dotenv
import os
import traceback
import random
import asyncio

# Load environment variables
load_dotenv()
token = os.getenv('DISCORD_TOKEN')

# Set up logging
handler = logging.FileHandler(
    filename='blackjackbot.log', 
    encoding='utf-8', 
    mode='w'
    )

# Configure bot intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Create the bot client and command tre
client = commands.Bot(command_prefix="/", intents=intents)
tree = client.tree  # commands.Bot already has a tree attribute

# Start up message
@client.event
async def on_ready():
    print(f'Logged in as {client.user.name}')
    print('----------------------------')

    try:
        synced = await client.tree.sync()
        print(f'Synced {len(synced)} command(s)')
        print('----------------------------')
    except Exception as e:
        print(f'Failed to sync commands: {e}')
    
    # Starts status rotation
    if not status_change.is_running():
        status_change.start()

################################################################################

# Blackjack function goes here
class blackjack_game:
    def create_deck(self):
        # Create a standard deck of 52 cards
        suits = ['♥', '♦', '♣', '♠']
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        deck = [(rank, suit) for suit in suits for rank in ranks]
        return deck
    
    # Initialize the game state
    def __init__(self):
        self.deck = self.create_deck()
        random.shuffle(self.deck)  # Shuffle the deck
        self.player_hand = []
        self.dealer_hand = []
        self.player_bust = False
        self.dealer_bust = False
        self.value = 0
        self.aces = 0

     # Function to deal cards to player and dealer
    def deal_initial_cards(self):
        for i in range(2):
            self.player_hand.append(self.deck.pop())

        for i in range(1): # Dealer gets one card initially
            self.dealer_hand.append(self.deck.pop())

        player_value = self.calculate_hand_value(self.player_hand)
        dealer_value = self.calculate_hand_value(self.dealer_hand)
        
        # Check for initial blackjack
        if self.calculate_hand_value(self.player_hand) == 21:
            self.dealer_bust = True # Dealer busts if player has blackjack
            

    # Function to calculate the value of a hand
    def calculate_hand_value(self, hand):
        value = 0
        aces = 0  
        # Iterate through the hand to calculate the value
        # Aces are counted as 11 initially, but adjusted later if necessary
        for card, _ in hand:
            if card in ['J', 'Q', 'K']:
                value += 10
            elif card == 'A':
                value += 11
                aces += 1  # Track the number of aces in the hand
            else:
                value += int(card)

        # Adjust for aces if value exceeds 21
        while value > 21 and aces:
            value -= 10
            aces -= 1
        return value
    
    # Function to hit (draw a card)
    def hit(self):
        if not self.player_bust:
            self.player_hand.append(self.deck.pop())
            self.check_bust()

    # Function to stand (end turn)
    def stand(self):
        self.check_bust()
        if not self.dealer_bust:
            if self.calculate_hand_value(self.dealer_hand) < 17:
                self.dealer_hand.append(self.deck.pop())
        self.check_bust()

    # Function to check if the player or dealer has busted
    def check_bust(self):   
        if self.calculate_hand_value(self.player_hand) > 21:
            self.player_bust = True
        if self.calculate_hand_value(self.dealer_hand) > 21:
            self.dealer_bust = True

    
# Hit and stand buttons 
# Need to figure out how to enable repeated button presses 
class blackjack_view(discord.ui.View):
    def __init__(self, game, user):
        super().__init__()
        self.game = game
        self.user = user
        self.stopped = False

    @discord.ui.button(label="Hit", style=discord.ButtonStyle.green)
    async def on_hit(self, interaction, button):
        try:
            # Check if the interaction user is the same as the game user
            if interaction.user != self.user:
                await interaction.response.send_message(
                    "This is not your hand!", 
                    ephemeral=True
                    )
                return
            
            self.game.hit()
            self.game.check_bust()
            player_value = self.game.calculate_hand_value(self.game.player_hand)
            dealer_value = self.game.calculate_hand_value(self.game.dealer_hand)

            # Makes appropriate responses based on the hand values
            if self.game.player_bust:
                embed = discord.Embed(title = "================================")
                embed.add_field(
                    name = "Dealer hand:", 
                    value = f"{format_hand(self.game.dealer_hand)} " +
                    f"| Value: **{dealer_value}**!", 
                    inline=True
                    )
                embed.add_field(
                    name = "Player hand:", 
                    value = f"{format_hand(self.game.player_hand)} " +
                    f"| Value: **{player_value}**!", 
                    inline=True
                    )
                embed.set_footer(text = "Sorry, you bust!")
                self.stopped = True

            elif self.game.dealer_bust:
                embed = discord.Embed(title = "================================")
                embed.add_field(
                    name = "Dealer hand:", 
                    value = f"{format_hand(self.game.dealer_hand)} " +
                    f"| Value: **{dealer_value}**!", 
                    inline=True
                    )
                embed.add_field(
                    name = "Player hand:", 
                    value = f"{format_hand(self.game.player_hand)} " +
                    f"| Value: **{player_value}**!", 
                    inline=True
                    )
                embed.set_footer(text = "Dealer bust. You win!")
                self.stopped = True

            elif player_value == 21:
                embed = discord.Embed(title = "================================")
                embed.add_field(
                    name = "Dealer hand:", 
                    value = f"{format_hand(self.game.dealer_hand)} " +
                    f"| Value: **{dealer_value}**!", 
                    inline=True
                    )
                embed.add_field(
                    name = "Player hand:", 
                    value = f"{format_hand(self.game.player_hand)} " +
                    f"| Value: **{player_value}**!", 
                    inline=True
                    )
                embed.set_footer(text = "You hit Blackjack. You win!")
                self.stopped = True

            else:
                embed = discord.Embed(title = "================================")
                embed.add_field(
                    name = "Dealer hand:", 
                    value = f"{format_hand(self.game.dealer_hand)} " +
                    f"| Value: **{dealer_value}**!", 
                    inline=True
                    )
                embed.add_field(
                    name = "Player hand:", 
                    value = f"{format_hand(self.game.player_hand)} " +
                    f"| Value: **{player_value}**!", 
                    inline=True
                    )
            
            # Update the message with the final hand values; 
            # Only reproduce buttons if the game is not over
            await interaction.response.edit_message(
                embed=embed,
                view=None if self.stopped else self
                )
            return

        except Exception as e:
            print(traceback.print_exc())

    @discord.ui.button(label="Stand", style=discord.ButtonStyle.blurple)
    async def on_stand(self, interaction, button):
        try:
            # Check if the interaction user is the same as the game user
            if interaction.user != self.user:
               await interaction.response.send_message(
                   "This is not your hand!", 
                   ephemeral=True
                   )
               return
            
            self.game.stand()
            self.game.check_bust()
            player_value = self.game.calculate_hand_value(self.game.player_hand)
            dealer_value = self.game.calculate_hand_value(self.game.dealer_hand)

            # Loop for dealer's turn; Repeat dealer hit until reaching 17 or bust
            while not self.game.dealer_bust and dealer_value < 17:
                self.game.stand()
                dealer_value = self.game.calculate_hand_value(self.game.dealer_hand)
                embed = discord.Embed(title = "================================")
                embed.add_field(name = "Dealer hits.")
                embed.add_field(
                    name = "Dealer hand:", 
                    value = f"{format_hand(self.game.dealer_hand)} " +
                    f"| Value: **{dealer_value}**!", 
                    inline=True
                    )
                embed.add_field(
                    name = "Player hand:", 
                    value = f"{format_hand(self.game.player_hand)} " +
                    f"| Value: **{player_value}**!", 
                    inline=True
                    )
                self.game.check_bust()

            # Makes appropriate responses based on the hand values
            if self.game.dealer_bust:
                embed = discord.Embed(title = "================================")
                embed.add_field(
                    name = "Dealer hand:", 
                    value = f"{format_hand(self.game.dealer_hand)} " +
                    f"| Value: **{dealer_value}**!", 
                    inline=True
                    )
                embed.add_field(
                    name = "Player hand:", 
                    value = f"{format_hand(self.game.player_hand)} " +
                    f"| Value: **{player_value}**!", 
                    inline=True
                    )
                embed.set_footer(text = "Dealer bust. You win!")
                self.stopped = True

            elif dealer_value == player_value == 21:
                embed = discord.Embed(title = "================================")
                embed.add_field(
                    name = "Dealer hand:", 
                    value = f"{format_hand(self.game.dealer_hand)} " +
                    f"| Value: **{dealer_value}**!", 
                    inline=True
                    )
                embed.add_field(
                    name = "Player hand:", 
                    value = f"{format_hand(self.game.player_hand)} " +
                    f"| Value: **{player_value}**!", 
                    inline=True
                    )
                embed.set_footer(text = "Push! Both you and dealer hit Blackjack")
                self.stopped = True

            # Script shits itself without this condition
            elif dealer_value == player_value >= 17: 
                embed = discord.Embed(title = "================================")
                embed.add_field(
                    name = "Dealer hand:", 
                    value = f"{format_hand(self.game.dealer_hand)} " +
                    f"| Value: **{dealer_value}**!", 
                    inline=True
                    )
                embed.add_field(
                    name = "Player hand:", 
                    value = f"{format_hand(self.game.player_hand)} " +
                    f"| Value: **{player_value}**!", 
                    inline=True
                    )
                embed.set_footer(text = "Push! Both you and dealer have equal value")
                self.stopped = True

            elif dealer_value == 21:
                embed = discord.Embed(title = "================================")
                embed.add_field(
                    name = "Dealer hand:", 
                    value = f"{format_hand(self.game.dealer_hand)} " +
                    f"| Value: **{dealer_value}**!", 
                    inline=True
                    )
                embed.add_field(
                    name = "Player hand:", 
                    value = f"{format_hand(self.game.player_hand)} " +
                    f"| Value: **{player_value}**!", 
                    inline=True
                    )
                embed.set_footer(text = "Dealer has Blackjack. You lose!")
                self.stopped = True

            elif player_value < dealer_value <= 21:
                embed = discord.Embed(title = "================================")
                embed.add_field(
                    name = "Dealer hand:", 
                    value = f"{format_hand(self.game.dealer_hand)} " +
                    f"| Value: **{dealer_value}**!", 
                    inline=True
                    )
                embed.add_field(
                    name = "Player hand:", 
                    value = f"{format_hand(self.game.player_hand)} " +
                    f"| Value: **{player_value}**!", 
                    inline=True
                    )
                embed.set_footer(text = "Dealer wins!")
                self.stopped = True

            elif 21 >= player_value > dealer_value >= 17:
                embed = discord.Embed(title = "================================")
                embed.add_field(
                    name = "Dealer hand:", 
                    value = f"{format_hand(self.game.dealer_hand)} " +
                    f"| Value: **{dealer_value}**!", 
                    inline=True
                    )
                embed.add_field(
                    name = "Player hand:", 
                    value = f"{format_hand(self.game.player_hand)} " +
                    f"| Value: **{player_value}**!", 
                    inline=True
                    )
                embed.set_footer(text = "You win!")
                self.stopped = True
            
            # Update the message with the final hand values; 
            # Only reproduce buttons if the game is not over
            await interaction.response.edit_message(
                embed=embed,
                view=None if self.stopped else self
                )
            return

        except Exception as e:
            print(traceback.print_exc())
        
# Formatting the hand for display
def format_hand(hand):
    return ', '.join([f"`{rank}{suit}`" for rank, suit in hand])


# Blackjack bot command
@client.tree.command(name="blackjack", description="Play a game of blackjack")
async def blackjack(interaction: discord.Interaction):
    print(f"Blackjack command invoked by {interaction.user.name}")
    
    try:
        #Initialize the game and deal initial cards
        game = blackjack_game()
        game.deal_initial_cards()

        # Calculate the initial hand values
        player_value = game.calculate_hand_value(game.player_hand)
        dealer_value = game.calculate_hand_value(game.dealer_hand)

        # Checks if first hand is a blackjack
        game.check_bust()

        if game.dealer_bust == True:
            embed = discord.Embed(title = "================================")
            embed.add_field(
                name = "Dealer hand:", 
                value = f"{format_hand(game.dealer_hand)} " +
                f"| Value: **{dealer_value}**!", 
                inline=True
                )
            embed.add_field(
                name = "Player hand:", 
                value = f"{format_hand(game.player_hand)} " +
                f"| Value: **{player_value}**!", 
                inline=True
                )
            embed.set_footer(text = "Blackjack! You win!")
            
            await interaction.response.send_message(embed=embed, view=view)
            return

        # Enables blackjack buttons
        view = blackjack_view(game, interaction.user)

        embed = discord.Embed(
            title = f"Welcome to the table, {interaction.user.name}"
            )
        embed.add_field(
            name = "Dealer hand:", 
            value = f"{format_hand(game.dealer_hand)} " +
            f"| Value: **{dealer_value}**!", 
            inline=True
            )
        embed.add_field(
            name = "Player hand:", 
            value = f"{format_hand(game.player_hand)} " +
            f"| Value: **{player_value}**!", 
            inline=True
            )
        
        await interaction.response.send_message(embed=embed, view=view)
        return
        

        

    except Exception as e:
        print(traceback.print_exc())
        print(f"An error occurred: {e}")
        return
   
################################################################################

# Unique message prompts
@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    if f"hi {client.user.name.lower()}" in message.content.lower():
        await message.channel.send(
            f"Hello {message.author.mention}!"
            )
        print(
            f"{message.author.name} said hi to Harley in {message.channel.name}"
            )

    if f"sybau {client.user.name.lower()}" in message.content.lower():
        await message.channel.send(
            f"You up at 4 in the morning playin blackjack, fuckin loser"
            )
        print(
            f"{message.author.name} told {client.user.name} to shut her " +
            f"bitch ass up in {message.channel.name}")

    if f"sorry {client.user.name.lower()}" in message.content.lower():
        await message.channel.send(
            f"It's okay :3"
            )
        print(f"{message.author.name} apologized to {client.user.name} in " +
              f"{message.channel.name}"
              )

    await client.process_commands(message)

################################################################################
# Defines rotating activities
statuses = (
    discord.Game(name = "Balatro"),
    discord.Game(name = "Blackjack"),
    discord.Game(name = "Texas Hold'Em"),
    discord.CustomActivity(name = "Mixing drinks and changing lives"),
    discord.Activity(type = discord.ActivityType.listening, name = "Machine Love")
)
activity = random.choice(statuses) 

# Sets loop to rotate statuses
@loop(seconds=600)
# Initially tried to integrate this loop into on_ready; Script hang
async def status_change(): 
    activity = random.choice(statuses)
    await client.change_presence(
        status = discord.Status.do_not_disturb,
        activity = activity
        )
    print(f'Set activity: {activity}')
        

# Waits for bot to initialize before starting loop
try:
    status_change.before_loop(client.wait_until_ready)
except Exception as e:
    print(f'Failed to run status_change: {e}')

################################################################################
client.run(token, log_handler=handler, log_level=logging.DEBUG)


