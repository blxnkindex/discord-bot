import discord
import asyncio
import numpy
from discord import Colour
from utils import rand_colour, delete_command_message, resetDeck, parseCards, getPlayerBalance, updatePlayerBalance, ensureAmount, ensureRouletteInput
from utils import rollRoulette
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
        return await ctx.send(f'`{ctx.message.author}` has {balance} dollars')
    
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
        return await ctx.send(f'`{ctx.message.author}` has paid {amount}, remaining balance {balance} ')

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
        
        if type(bet) == str:
            if bet == 'green' and bet == color:
                resultStr = f'`{ctx.message.author}` bet on `{bet}` with `{amount}` and wins `{amount * 14}`'
                balance += amount * 14
                updatePlayerBalance('casino', getPlayerBalance('casino') - amount*14)
            elif (bet == 'red' or bet == 'black') and bet == color:
                resultStr = f'`{ctx.message.author}` bet on `{bet}` with `{amount}` and wins `{amount * 2}`'
                balance += amount * 2
                updatePlayerBalance('casino', getPlayerBalance('casino') - amount*2)
            elif bet == 'high' and num >= 8:
                resultStr = f'`{ctx.message.author}` bet on `{bet}` with `{amount}` and wins `{amount * 2}`'
                balance += amount * 2
                updatePlayerBalance('casino', getPlayerBalance('casino') - amount*2)
            elif bet == 'low' and num < 8:
                resultStr = f'`{ctx.message.author}` bet on `{bet}` with `{amount}` and wins `{amount * 2}`'
                balance += amount * 2
                updatePlayerBalance('casino', getPlayerBalance('casino') - amount*2)
            else:
                resultStr = f'`{ctx.message.author}` bet on `{bet}` and lost `{amount}`'
        elif type(bet) == int:
            if num == bet:
                resultStr = f'`{ctx.message.author}` bet on `{bet}` with `{amount}` and wins `{amount * 14}`'
                balance += amount * 14
                updatePlayerBalance('casino', getPlayerBalance('casino') - amount*14)
            else:
                resultStr = f'`{ctx.message.author}` bet on `{bet}` and lost `{amount}`'
       
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
            player = ctx.message.author
            balance -= amount
            updatePlayerBalance('casino', getPlayerBalance('casino') + amount)
            updatePlayerBalance(ctx.message.author.id, balance)

            gameMsg = await ctx.send(embed=self.bjEmbed(playerCards, dealerCards, player, amount))
            actionMsg = await ctx.send('Drawing cards...')
            while len(playerCards) < 2:
                await asyncio.sleep(0.55)
                card = random.choice(deck)
                playerCards.append(card)
                deck.remove(card)
                playerScore = self.calcScore(playerCards)
                await asyncio.sleep(0.55)
                await actionMsg.edit(content=f"You're dealt {parseCards(card)}...")
                await asyncio.sleep(0.5)
                await gameMsg.edit(embed=self.bjEmbed(playerCards, dealerCards, player, amount))

                card = random.choice(deck)
                dealerCards.append(card)
                if len(dealerCardsDisplay) == 0:
                    dealerCardsDisplay.append(card)
                else:
                    dealerCardsDisplay.append('hidden')
                deck.remove(card)
                dealerScore = self.calcScore(dealerCards)
                await asyncio.sleep(0.55)
                if len(dealerCards) == 1:
                    await actionMsg.edit(content=f"Dealer's dealt {parseCards(card)}...")
                else:
                    await actionMsg.edit(content=f"Dealer is drawing a card...")
                await asyncio.sleep(0.5)
                await gameMsg.edit(embed=self.bjEmbed(playerCards, dealerCardsDisplay, player, amount))
                
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
                    await asyncio.sleep(1)
                    card = random.choice(deck)
                    playerCards.append(card)
                    deck.remove(card)
                    playerScore = self.calcScore(playerCards)
                    await asyncio.sleep(1)
                    await actionMsg.edit(content=f"You drew {parseCards(card)}...")
                    await asyncio.sleep(0.5)
                    await gameMsg.edit(embed=self.bjEmbed(playerCards, dealerCardsDisplay, player, amount))
                    if playerScore == 21:
                        return await self.endBlackJack(ctx, f'{player} has blackjack, {player} wins', playerCards, dealerCards, True, actionMsg, gameMsg, amount)
                    elif playerScore > 21:
                        return await self.endBlackJack(ctx, f'{player} is bust, {player} loses', playerCards, dealerCards, False, actionMsg, gameMsg, amount)
                    if dealerScore < 17:
                        await asyncio.sleep(1)
                        await actionMsg.edit(content=f"Dealer is drawing a card...")
                        await asyncio.sleep(1)
                        card = random.choice(deck)
                        dealerCards.append(card)
                        if len(dealerCardsDisplay) == 0:
                            dealerCardsDisplay.append(card)
                        else:
                            dealerCardsDisplay.append('hidden')
                        deck.remove(card)
                        dealerScore = self.calcScore(dealerCards)
                        await asyncio.sleep(1)
                        if len(dealerCards) == 1:
                            await actionMsg.edit(content=f"Dealer's dealt {parseCards(card)}...")
                        else:
                            await actionMsg.edit(content=f"Dealer is drawing a card...")
                        await asyncio.sleep(1)
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
                        dealerScore = self.calcScore(dealerCards)
                        await asyncio.sleep(1)
                        if len(dealerCards) == 1:
                            await actionMsg.edit(content=f"Dealer's dealt {parseCards(card)}...")
                        else:
                            await actionMsg.edit(content=f"Dealer is drawing a card...")
                        await asyncio.sleep(1)
                        await gameMsg.edit(embed=self.bjEmbed(playerCards, dealerCards, player, amount))
                    await asyncio.sleep(1)
                    await actionMsg.edit(content=f"Dealer score over 17, dealer stands...")
                    await asyncio.sleep(1.5)
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
                await gameMsg.edit(embed=self.bjEmbed(playerCards, dealerCardsDisplay, player, amount))
            await actionMsg.delete()
                    
            self.isBlackJack = False
        except Exception as e:
            print(e)

    def calcScore(self, cards):
        c = []
        aceNum = 0
        for card in cards:
            if card.split('_')[0] == 'A':
                aceNum += 1
            c.append(card.split('_')[0])
        score = 0
        for card in c:
            if card.isdigit():
                score += int(card)
            elif card == 'K' or card == 'J' or card == 'Q':
                score += 10
            elif card == 'A' and score > 10:
                score += 1
            elif card == 'A' and score <= 10:
                score += 11
        if score > 21 and 'A' in c:
            if score - 10 <= 21 and aceNum >= 1:
                return score - 10
            elif score - 10 > 21 and score - 20 <= 21 and aceNum == 2:
                return score - 20
        else:
            return score

    async def endBlackJack(self, ctx, str, playerCards, dealerCards, win, actionMsg, gameMsg, amount):
        self.isBlackJack = False
        await actionMsg.delete()
        await gameMsg.edit(embed=self.bjEmbed(playerCards, dealerCards, ctx.message.author, amount))
        winStr = 'wins' if win else 'loses'
        embed = discord.Embed(
            title=f'{ctx.message.author} {winStr}',
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

    def bjEmbed(self, playerCards, dealerCards, player, amount):
        embed = discord.Embed(
            title=f'{player}\'s Blackjack Game',
            description=f'Stakes: {amount}',
            colour=rand_colour()
        )
        playerCards = '\n'.join(list(map(parseCards, playerCards)))
        dealerCards = '\n'.join(list(map(parseCards, dealerCards)))
        if playerCards == '':
            playerCards = ' '
        if dealerCards == '':
            dealerCards = ' '
        
        embed.add_field(name=f'{player}\'s cards', value=f'```{playerCards} ```', inline=False)
        embed.add_field(name=f'Dealer\'s cards', value=f'```{dealerCards} ```', inline=False)
        return embed
    


async def setup(bot):
    await bot.add_cog(Casino(bot))