#Python data types

a = 1

b = 5

c = 10

e = a + b + c

print(e)
print(f' variable e is type {type(e)}')

print(f'Convert variable e to a hex, octal, and binary')

o, b, h = oct(e), bin(e), hex(e)

print(f'e variable converted to octal: {o}, binary: {b}, hexidecimal: {h}')

print('#'*90)

#FLOATS
#whenever you divide using 2 integers python will always return a float

f = 17
g = 5
print('This will return a float with decimal')
h = f / g

print(type(h))
print(h)
print('This will return a float, but without the decimal or remainder')
i = f // g
print(type(h))
print(i)
print('You can convert an integer into a float')
j = float(f)
print(type(j))
print(f'You can convert an integer to a float by: j = float(f)')

print('You can also use scientific notation, ex: k = 4e3 which equals 4000')

k = 4e3
print(k)
print(type(k))

print('You can also use scientific notation negative exponent, ex: l = 4e-3 which equals .003')
l = 4e-3
print(l)
print(type(l))

print('#'*90)

#Dictionary.  Please note the following.  Use the get() to access a key value in a dictionary.

a = dict()
a['age'] = 48
a['name'] = 'Patrick'
print(a['age'])

#But what if you tried to get a key/value does not exist, pyton will throw an error exception

#print(a['country'])

#So, instead, use the get() method
print(a.get('country'))

print('#'*90)
#Math operators

abs(5)
abs(-5)
var1 = 15 % 4
print(var1)
print(type(var1))
print(divmod(15,4))

print(divmod(10,3))

list1 = [1,2,38,6,10,20, 90]
list2 = [-2, 3, -7, -1]
print(max(list1))

print(min(list2))

print(pow(3, 2))
#This is the same as this
print(3**2)

print(pow(3, 2, 2))
#This is 3^2 devide by 2 or (3 x 3) /2, result is remainder of 1

print(round(4.5987, 2))

print('The sum() function returns the the total sum of tyhe integers')
print(sum([1,2,3,4,5]))

print('if you add the start value, 20, it returns the sum of the integers starting with 20')
print(sum([1,2,3,4,5], 20))

print('#'*90)
#Type conversions

my_dict = {'name' : 'Patrick', 'age' : 52}
my_tuple = (1, 2, 3,5 ,6)
my_set = set(my_tuple)

print(chr(97))
print(chr(98))
print(chr(68))
print(chr(0x06a4))
print(ord('a'))
print(ord('A'))

print(type('h'))
print(type(8))
print(type(4.5))
print(type(True))
print(type(list1))
print(type(my_dict))
print(type(my_tuple))
print(type(my_set))

#type conversions

print(int('1234'))
print(int('1234', base=16))
print(int('11010', base=2))

#binary repro of 10
print(bin(10))
#octal repro of 10
print(oct(10))
#hexadecimal repro of 10
print(hex(10))
print(float(10))
print(complex(10))

print(str(1234))
print(bool(0))
print(bool(1))
print(bool(1234))

print('#'*90)
#iterables and iterators
a = [1,2,3,4,5,6,7,8,9]
len(a)
#returns the number of elements in list

a = [True, True, True]
b = [True, False, True]
c = [False, False, False]

print(any(a))
print(any(b))
print(any(c))

print(all(a))
print(all(b))
print(all(c))

d = [1,2,5,6,7,8,9,10,2,43,65,10]
print(len(d))
e= reversed(d)
print(list(e))

f = sorted(d)
print(f)


print(range(10))

print(list(range(10)))

print(list(range(0,10,2)))

print('#'*90)
print('iterators - enumerate')

peoples = ['Jane','Patrick','Steve','Beatriz','Joseph']


for idx, person in enumerate(peoples):
    print(idx, person)

print('#'*90)
print('iterators - zip')

countries = ['UK','USA','Japan']
continents = ['Eurpoe','North America','Asia']

#The old of doing this operation is

for i in range(len(countries)):
    print(countries[i], continents[i])

#the more pythonic way is uring zip.  Zip combines the 2 lists

merged = zip(countries, continents)

country_list = list(merged)

for country, continent in country_list:
    print(country, continent)

print('#'*90)
#iter and next
a = iter(['test','me','now','true','dat'])

print(next(a))
print(next(a))
print(next(a))
print(next(a))
print(next(a))
print('#'*90)
#print() function
#The below for loop will print out 1 thru 50 up the screen
#for i in range(50):
#    print(i)
#
for i in range(50):
    print(i, end = ' ')

print('#'*90)
#The dir() function allows you to see the attributes and methods available in a python object
print(dir(a))
print(a.__class__)
print(a.__doc__)
print(a.__format__)

print(help(len))
print(help(abs))
print(help(print))

print(dir(peoples))

a = 'Main Menu'
b = a.upper()
print(b.center(60))

import logging
import datetime
print(dir(datetime))
print('#'*90)
print(dir(logging))

s = 'Patrick'
#s is an iterables

t = iter(s)
#t is an iterator
print(type(t))

string = [x for x in countries]

print(string)

for x in string:
    print(x)

print(dir(t))

print('#'*90)
print(dir(string))
print(type(string))

a = 'broadcom'
print(a)

z = iter(a)
print(z)

x = [h for h in z]
print(x)
print('#'*120)
dict1 = vars()


for key, value in list(dict1.items()):
    print(key, '-->' ,value)


