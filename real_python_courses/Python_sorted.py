#Sort() amd sorted() functions in python

#Please note, the sorted() returns the object in a sorted fashion.  it does not change the original list.
#In order to do that, you would have to assign the sorted list to a new variable.

import os

print(help(sorted))

print('#'*120)
num = [1, 3, 6, 9, 2, 100, 33, 290]

print('list not sorted'.capitalize())
print(num)
print('list sorted'.capitalize())
print(sorted(num))

num_sorted = sorted(num)
print(num_sorted)

string_list = ['Zebra','Stork','Bear','Cat']

print('list not sorted'.upper())
print(string_list)

print('list sorted'.upper())
print(sorted(string_list))

str_list_sorted = sorted(string_list)
print('This is a sorted list:', str_list_sorted)
print('#'*120)

num_tuple = (1, 8, 4, 2, 7)

sorted_tuple = sorted(num_tuple)
print('This is a sorted tuple:', sorted_tuple)

num_set = {87, 34, 31, 94, 31, 55}

print(num_set)

num_set_sorted = sorted(num_set)

print('This is a sorted set:', num_set_sorted)

print('#'*120)
string_num = '5378912'
sorted_string_num = sorted(string_num)
print(sorted_string_num)

string_words = 'I like to write python code'

sorted_string_words = sorted(string_words)
print(sorted_string_words)

sorted_string_words = sorted(string_words.split())
print(' '.join(sorted_string_words))


print('#'*120)
print("The locals() is a built-in function which displays all the objects in the current module")
#print(help(locals()))
print(locals())

print('#'*120)
#Sorted() using customized options, e.g., reverse.

num_sorted_rev = sorted(num, reverse=True)
print(num_sorted_rev)

string_list = ['Zebra','Stork','Bear','Cat']
string_list_sort = sorted(string_list, key=len)
print(string_list_sort)

string_list = ['Zebra','Stork','Bear','Cat']
string_list_sort = sorted(string_list, key=str)
print(string_list_sort)
"""
print(dir(str))
print(dir(list))
print(dir(dict))
"""
#One thing to note about sort(), it does not return anything, or it returns None.  sort() occurs in place

names = ['timmy','jonny','mary','amy']
names.sort()
print('names list using the sort(): ', names)

#Python sorts letters based on the unicode code point value.  Capital letters then lower 






