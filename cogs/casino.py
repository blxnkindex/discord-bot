import discord
import asyncio
import numpy
from discord import Colour
from utils import rand_colour, delete_command_message, resetDeck, parseCards, getPlayerBalance, updatePlayerBalance, ensureAmount, ensureRouletteInput, getRoulettePayout, calcScore, rollRoulette, bjEmbed
from discord.ext import commands

import random

class Casino(commands.Cog, name = 'casino'):
    def __init__(self, bot):
        self.isRoulette = False
        self.isBlackJack = False
        self.bot = bot

    @commands.hybrid_command(name = 'balance', description = 'Check your balance', aliases=['bal'])
    async def balance(self, ctx):
        balance = getPlayerBalance(ctx.message.author.id)
        if balance < 0:
            balance = 5000
            updatePlayerBalance(ctx.message.author.id, balance)
        return await ctx.send(f'`{ctx.message.author.display_name}` has {balance} dollars')
    
    @commands.hybrid_command(name = 'adminpay', description = '')
    @commands.is_owner()
    async def adminpay(self, ctx, targetId, amount):
        if amount.isdigit():
            amount = int(amount)
        balance = getPlayerBalance(targetId)
        balance += amount
        updatePlayerBalance(targetId, balance)
        updatePlayerBalance('casino', getPlayerBalance('casino') + amount)
        return await ctx.send(f'You gave {amount} dollars to your target')
    
    @commands.hybrid_command(name = 'casprofits', description = 'How much the casino has profited/lost', aliases=['casinoprofits'])
    async def casinoprofits(self, ctx):
        balance = getPlayerBalance("casino")
        return await ctx.send(f'The casino has profited has {balance} dollars')
    
    @commands.hybrid_command(name = 'pay', description = 'Pay someone, uses id use copy id to pay')
    async def pay(self, ctx, targetId, amount):
        if amount.isdigit():
            amount = int(amount)
        else:
            return await ctx.send(f'Amount needs to be whole postive number')
        balance = await ensureAmount(ctx, amount)
        if not balance:
            return
        balance -= amount
        updatePlayerBalance(ctx.message.author.id, balance)
        targetBal = getPlayerBalance(targetId)
        targetBal += amount
        updatePlayerBalance(targetId, targetBal)
        return await ctx.send(f'`{ctx.message.author.display_name}` has paid {amount}, remaining balance {balance} ')

    @commands.hybrid_command(name = 'roulette', description = 'Play roulette')
    async def roulette(self, ctx, bet=None, amount=None):
        if not await ensureRouletteInput(ctx, bet,amount):
            return
        if amount.isdigit():
            amount = int(amount)
        if bet.isdigit():
            bet = int(bet)

        balance = await ensureAmount(ctx, amount)
        if not balance:
            return
        if self.isRoulette:
            await delete_command_message(ctx)
            return await ctx.send('Another roulette game is in progress, please wait for that to finish', delete_after= 3)
        balance -= amount
        updatePlayerBalance('casino', getPlayerBalance('casino') + amount)
        self.isRoulette = True
        
        table = await rollRoulette(ctx)

        if table[4] == ':green_square:':
            num = 0
            color = 'green'
            embedColor = Colour.from_rgb(0,255,0)
        elif table[4] == ':red_square:':
            num = random.randint(1,7) * 2
            color = 'red'
            embedColor = Colour.from_rgb(255,0,0)
        elif table[4] == ':black_large_square:':
            num = random.randint(1,7) * 2 - 1
            color = 'black'
            embedColor = Colour.from_rgb(0,0,0)
            
        # Tuple (game result bool, winnings/losings)
        gameResult = getRoulettePayout(color, bet, num, amount) 

        winLose = 'wins' if gameResult[0] else 'loses'
        resultStr = f'`{ctx.message.author.display_name}` bet on `{bet}` and {winLose} `{gameResult[1]}`'
        
        if gameResult[0]: updatePlayerBalance('casino', getPlayerBalance('casino') - gameResult[1])
       
        embed = discord.Embed(
            title=f'{table[4]}: {num}',
            description=resultStr,
            colour=embedColor
        )
        embed.set_footer(text=f'Your new balance: {balance} dollars')
        await ctx.send(embed=embed)
        updatePlayerBalance(ctx.message.author.id, balance)
        self.isRoulette = False

    @commands.hybrid_command(name = 'blackjack', description = 'Play blackjack')
    async def blackjack(self, ctx, amount=None):
        if not amount:
            return await ctx.send('Usage: >blackjack betAmount')
        if amount.isdigit():
            amount = int(amount)
        else:
            return await ctx.send('Bet amount needs to be a whole number')

        balance = await ensureAmount(ctx, amount)
        if not balance:
            return
        if self.isBlackJack:
            await delete_command_message(ctx)
            return await ctx.send('Another blackjack game is in progress, please wait for that to finish', delete_after=3)
        try:
            self.isBlackJack = True
            playerScore, playerCards = 0, []
            dealerScore, dealerCards = 0, []
            dealerCardsDisplay = []
            deck = resetDeck()
            print(ctx.message.author.display_name)
            player = ctx.message.author.display_name
            balance -= amount
            updatePlayerBalance('casino', getPlayerBalance('casino') + amount)
            updatePlayerBalance(ctx.message.author.id, balance)

            gameMsg = await ctx.send(embed=bjEmbed(playerCards, dealerCards, player, amount))
            actionMsg = await ctx.send('Drawing cards...')
            while len(playerCards) < 2:
                await asyncio.sleep(0.25)
                card = random.choice(deck)
                playerCards.append(card)
                deck.remove(card)
                playerScore = calcScore(playerCards)
                await asyncio.sleep(0.25)
                await actionMsg.edit(content=f"You're dealt {parseCards(card)}...")
                await asyncio.sleep(0.25)
                await gameMsg.edit(embed=bjEmbed(playerCards, dealerCards, player, amount))

                card = random.choice(deck)
                dealerCards.append(card)
                if len(dealerCardsDisplay) == 0:
                    dealerCardsDisplay.append(card)
                else:
                    dealerCardsDisplay.append('hidden')
                deck.remove(card)
                dealerScore = calcScore(dealerCards)
                await asyncio.sleep(0.25)
                if len(dealerCards) == 1:
                    await actionMsg.edit(content=f"Dealer's dealt {parseCards(card)}...")
                else:
                    await actionMsg.edit(content=f"Dealer is drawing a card...")
                await asyncio.sleep(0.25)
                await gameMsg.edit(embed=bjEmbed(playerCards, dealerCardsDisplay, player, amount))
                
            if playerScore == 21 and dealerScore == 21:
                return await self.endBlackJack(ctx, f'{player} and dealer have blackjack, dealer wins', playerCards, dealerCards, False, actionMsg, gameMsg, amount)
            elif playerScore == 21:
                return await self.endBlackJack(ctx, f'{player} drew blackjack, {player} wins', playerCards, dealerCards, True, actionMsg, gameMsg, amount)
            elif dealerScore == 21:
                return await self.endBlackJack(ctx, f'Dealer drew blackjack, {player} loses', playerCards, dealerCards, False, actionMsg, gameMsg, amount)
            
            def check(reaction, user):
                return user == ctx.message.author
            
            while self.isBlackJack:
                await actionMsg.edit(content='Hit or stand?')
                await actionMsg.clear_reactions()
                await actionMsg.add_reaction(u'\U0001F1ED') # Hit
                await actionMsg.add_reaction(u'\U0001F1F8') # Stand
                reaction = await self.bot.wait_for("reaction_add", check=check)
                if str(reaction[0]) == '🇭':
                    await actionMsg.edit(content=f"You hit. Drawing a card...")
                    await asyncio.sleep(0.5)
                    card = random.choice(deck)
                    playerCards.append(card)
                    deck.remove(card)
                    playerScore = calcScore(playerCards)
                    await asyncio.sleep(0.5)
                    await actionMsg.edit(content=f"You drew {parseCards(card)}...")
                    await asyncio.sleep(0.25)
                    await gameMsg.edit(embed=bjEmbed(playerCards, dealerCardsDisplay, player, amount))
                    if playerScore == 21:
                        return await self.endBlackJack(ctx, f'{player} has blackjack, {player} wins', playerCards, dealerCards, True, actionMsg, gameMsg, amount)
                    elif playerScore > 21:
                        return await self.endBlackJack(ctx, f'{player} is bust, {player} loses', playerCards, dealerCards, False, actionMsg, gameMsg, amount)
                    if dealerScore < 17:
                        await asyncio.sleep(0.75)
                        await actionMsg.edit(content=f"Dealer is drawing a card...")
                        await asyncio.sleep(0.75)
                        card = random.choice(deck)
                        dealerCards.append(card)
                        if len(dealerCardsDisplay) == 0:
                            dealerCardsDisplay.append(card)
                        else:
                            dealerCardsDisplay.append('hidden')
                        deck.remove(card)
                        dealerScore = calcScore(dealerCards)
                        await asyncio.sleep(0.75)
                        if len(dealerCards) == 1:
                            await actionMsg.edit(content=f"Dealer's dealt {parseCards(card)}...")
                        else:
                            await actionMsg.edit(content=f"Dealer is drawing a card...")
                        await asyncio.sleep(0.75)
                    if dealerScore > 21 and playerScore < 21:
                        return await self.endBlackJack(ctx, f'Dealer is bust, {player} win', playerCards, dealerCards, True, actionMsg, gameMsg, amount)
                elif str(reaction[0]) == '🇸':
                    await actionMsg.edit(content=f"You stand")
                    while dealerScore < 17:
                        card = random.choice(deck)
                        
                        dealerCards.append(card)
                        if len(dealerCardsDisplay) == 0:
                            dealerCardsDisplay.append(card)
                        else:
                            dealerCardsDisplay.append('hidden')
                        deck.remove(card)
                        dealerScore = calcScore(dealerCards)
                        await asyncio.sleep(0.75)
                        if len(dealerCards) == 1:
                            await actionMsg.edit(content=f"Dealer's dealt {parseCards(card)}...")
                        else:
                            await actionMsg.edit(content=f"Dealer is drawing a card...")
                        await asyncio.sleep(0.75)
                        await gameMsg.edit(embed=bjEmbed(playerCards, dealerCards, player, amount))
                    await asyncio.sleep(0.75)
                    await actionMsg.edit(content=f"Dealer score over 17, dealer stands...")
                    await asyncio.sleep(0.75)
                    if dealerScore == 21:
                        return await self.endBlackJack(ctx, f'Dealer has blackjack, {player} loses', playerCards, dealerCards, False, actionMsg, gameMsg, amount)
                    elif dealerScore > 21:
                        return await self.endBlackJack(ctx, f'Dealer is bust, {player} win', playerCards, dealerCards, True, actionMsg, gameMsg, amount)
                    elif dealerScore > playerScore:
                        return await self.endBlackJack(ctx, f'Dealer higher score than {player}, {player} lose', playerCards, dealerCards, False, actionMsg, gameMsg, amount)
                    elif dealerScore < playerScore:
                        return await self.endBlackJack(ctx, f'{player} higher score than dealer, {player} win', playerCards, dealerCards, True, actionMsg, gameMsg, amount)
                    elif dealerScore == playerScore:
                        return await self.endBlackJack(ctx, f'Dealer and {player} same score, {player} loses', playerCards, dealerCards, False, actionMsg, gameMsg, amount)
                await gameMsg.edit(embed=bjEmbed(playerCards, dealerCardsDisplay, player, amount))
            await actionMsg.delete()
                    
            self.isBlackJack = False
        except Exception as e:
            print(e)


    async def endBlackJack(self, ctx, str, playerCards, dealerCards, win, actionMsg, gameMsg, amount):
        self.isBlackJack = False
        await actionMsg.delete()
        await gameMsg.edit(embed=bjEmbed(playerCards, dealerCards, ctx.message.author.display_name, amount))
        winStr = 'wins' if win else 'loses'
        embed = discord.Embed(
            title=f'{ctx.message.author.display_name} {winStr}',
            description=str,
            colour=rand_colour()
        )
        balance = getPlayerBalance(ctx.message.author.id)
        print(f'balance after bet {balance}')
        if win:

            balance += int(amount*1.5)
            print(f'balance after win {balance}')
            updatePlayerBalance(ctx.message.author.id, balance)
            updatePlayerBalance('casino', getPlayerBalance('casino') - int(amount*1.5))

        embed.set_footer(text=f'Your new balance: {balance} dollars')
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Casino(bot))