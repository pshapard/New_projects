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

def deal_card():
    for key, value in deck_of_cards.items():
        if key:
            deal = random.randrange(key, 53)
            if deal not in deck_of_cards:
                continue
            else:
                #print(deal, deck_of_cards[deal])
                return deck_of_cards[deal]
        deck_of_cards.pop(deal, None)


def player1():
    card1 = deal_card()
    card2 = deal_card()
    points = card1 + card2
    print(f'Player 1 has:  {points}')
    if points == 21:
        print("Blackjack!")
        return points
    elif points <= 21:
        while points < 21:
            response = input("Do you want to hit? (y)es,(n)o: ")
            if response == 'yes' or response == 'y':
                card = deal_card()
                points = points + card
                print(f"Player has {points}")
            elif response == 'no' or response == 'n':
                return points
        return points
            


def dealer():
    card1 = deal_card()
    card2 = deal_card()
    points = card1 + card2
    print(f'Dealer has:  {points}')
    if points == 21:
        print("You lose!")
        return points
    while points <= 16:
        card = deal_card()
        points = points + card
        print(f"The Dealer has {points}")
        if points > 21:
            print("Dealer busted")
            return points
    return points


def main():

    dealer_cards = dealer()
    player_cards = player1()
    
    if player_cards > 21:
        print("Player busted")
    elif player_cards == dealer_cards:
        print("It's a push.")
    elif dealer_cards < player_cards:
        print("You win, congrats!")
    elif dealer_cards > player_cards:
        print("You lose.")

if __name__ == '__main__':
    main()



