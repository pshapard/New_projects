#!/usr/bin/python
# Created: 04/17/2020
# Author: Patrick Shapard
# The simple Calculator written with python 3.8.2


def Calculate(x, y, oper):
    """Input 3 variables(x, y, operation) and returns the answer """
    if oper == 'add':
        return("{:,.2f}".format(x + y))

    elif oper == 'sub':
        return("{:,.2f}".format(x - y))

    elif oper == 'mul':
        return("{:,.2f}".format(x * y))

    elif oper == 'div':
        try:
            return("{:,.2f}".format(x / y))
        except ZeroDivisionError:
            return("division by zero error")


def user_input():
    """Takes user input for x, y, and oper variables, then performs operation. """
    while True:
        try:
            x = float(input("Input first number: "))
            break
        except ValueError:
            print("Please input a number")
    while True:
        try:
            y = float(input("Input second number: "))
            break
        except ValueError:
            print("Please input a number")
    while True:
        oper = input("add, sub, mul, div: ")
        if oper == '':
            print("Please select an operation")
        elif oper == 'add' or oper == 'sub' or oper == 'mul' or oper == 'div':
            print(Calculate(x, y, oper))
            break
        else:
            continue


def main():
    user_input()


if __name__ == '__main__':
    main()
