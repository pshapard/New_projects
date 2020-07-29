#!/usr/bin/python
# Created 04/10/2020
# This script was created to create functions witht the many data types and how they work.


class DataTypes(object):

    def __init__(self, num1=2, num2=4, num3=6):
        self.num1 = num1
        self.num2 = num2
        self.num3 = num3

    def octBinHex(self):
        """This function is used to represent octal,
            binary, hexadecimal representation."""
        print(
            f'This is oct repo: {oct(self.num1)}, this is binary: {bin(self.num2)}, this is hexadecimal: {hex(self.num3)}')

    def floats(self):
        num_float = self.num3 / self.num2
        print(f'This is a float: {num_float}')


def main():
    numObj = DataTypes(20, 30, 100)
    numObj.octBinHex()
    numObj.floats()


if __name__ == '__main__':
    main()
