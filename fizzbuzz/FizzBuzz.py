#!/usr/bin/python
#Author: Patrick Shapard
#Created: 05/04/2020
#Fizzbuzz is a popular coding question asked in interviews

fizz_list = []
buzz_list = []
fizbuz_list = []

def func(v1, v2):
    """Function takes two variables
       Loops thru the range of v1 thru v2
       Prints fizz when x is evenly divisible by 3 
       Prints buzz when x is evenly divisible by 5
       Prints fizzbuzz when x is evenly divisible by 3 and 5.
    """
    for x in range(v1, v2):
        if x % 3 == 0 and x % 5 == 0:
            fizbuz_list.append(x)
            print("Fizzbuzz")
        elif x % 3 == 0:
            fizz_list.append(x)
            print("Fizz")
        elif x % 5 == 0:
            buzz_list.append(x)
            print("Buzz")
        else:
            print(x)


def main():
    func(1, 101)
    print(f"The number of elements in the fizzbuzz list is:", len(fizbuz_list))
    print(f"The number of elements in the fizz list is:", len(fizz_list))
    print(f"The number of elements in the buzz list is:", len(buzz_list))
    print(help(func2))

if __name__ == '__main__':
    main()