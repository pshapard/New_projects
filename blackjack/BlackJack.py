#!/usr/bin/python
#Author: Patrick Shapard
#Created: 04/26/2020
#Blackjack game written with python 3.8.2

import random

deck_of_cards = {1: 2,
                  2: 3,
                  3: 4,
                  4: 5,
                  5: 6,
                  6: 7,
                  7: 8,
                  8: 9,
                  9: 10,
                  10: 10,
                  11: 10,
                  12: 10,
                  13: 11,
                  14: 2,
                  15: 3,
                  16: 4,
                  17: 5,
                  18: 6,
                  19: 7,
                  20: 8,
                  21: 9,
                  22: 10,
                  23: 10,
                  24: 10,
                  25: 10,
                  26: 11,
                  27: 2,
                  28: 3,
                  29: 4,
                  30: 5,
                  31: 6,
                  32: 7,
                  33: 8,
                  34: 9,
                  35: 10,
                  36: 10,
                  37: 10,
                  38: 10,
                  39: 11,
                  40: 2,
                  41: 3,
                  42: 4,
                  43: 5,
                  44: 6,
                  45: 7,
                  46: 8,
                  47: 9,
                  48: 10,
                  49: 10,
                  50: 10,
                  51: 10,
                  52: 11}

class BlackJack(object):

    def __init__(self):
        pass

    def __repr__(self):
       pass

    def __str__(self):
        pass

    def deal_card(self):
        for key, value in deck_of_cards.items():
            if key:
                deal = random.randrange(key, 53)
                if deal not in deck_of_cards:
                    continue
                else:
                    card = deck_of_cards[deal]
                    deck_of_cards.pop(deal, None)
            return card

    def player(self):
        """Player is dealt two cards. Player is asked if they
           want another card. If player's points is greater
           than 21, player has busted"""
        obj = BlackJack()
        card1 = obj.deal_card()
        card2 = obj.deal_card()
        if card1 == 11 and card2 == 11:
            print("Both cards are aces, you want 12 or 2")
        else:
            pass
        points = card1 + card2
        print(f'Player has:  {points}')
        if points == 21:
            print("Blackjack!")
            #return points
        elif points <= 21:
            while points <= 21:
                response = input("Do you want to hit? (y)es,(n)o: ")
                if response == 'yes' or response == 'y':
                    card = obj.deal_card()
                    print(f'Player is dealt {card}')
                    points = points + card
                    print(f"Player has {points}")
                    if points == 21:
                        break
                    elif points < 21:
                        continue
                elif response == 'no' or response == 'n':
                    print(f"Player has {points}")
                    break
        return points

    def dealer(self, card=None):
        """Function deals two cards to dealer.
           If dealer has less than 17, dealer will
           be dealt a card. if dealer has 17, dealer
           points will be returned."""
        obj = BlackJack()
        card1 = obj.deal_card()
        if card == None:
            points = card1
        else:
            points = card + card1
            print(f'Dealer is dealt {card1}')
        print(f'Dealer has:  {points}')
        return points

    def win_lose(self, player_cards, dealer_cards):
        if player_cards > 21 and dealer_cards <= 21:
            print("Player busted, Dealer wins.  Good luck next time.")
        elif player_cards == dealer_cards:
            print("It's a push.")
        elif dealer_cards > 21 and player_cards <= 21:
            print("Dealer busted, player wins")
        elif player_cards < dealer_cards and dealer_cards <= 21:
            print("Dealer wins.  Good luck next time")
        elif dealer_cards < player_cards and player_cards <= 21:
            print("Player wins")


def main():

    obj = BlackJack()
    dealer_card = obj.dealer()
    player_cards = obj.player()
    dealer_cards = obj.dealer(dealer_card)
    if dealer_cards == 21:
        print("Dealer has Blackjack!")
    elif dealer_cards <= 16:
        while dealer_cards < 17:
            card = obj.deal_card()
            print(f'Dealer is dealt {card}')
            dealer_cards = dealer_cards + card
            print(f"The Dealer has {dealer_cards}")
    
    obj.win_lose(player_cards, dealer_cards)



if __name__ == '__main__':
    main()



