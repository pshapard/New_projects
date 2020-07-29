#

class PrintThis(object):
    
    def __init__(self):
        """funtion to initialize a class"""
        pass

    def HashTag120(self):
        """Function to print out 120 hashtags"""
        print('#'*120)

printme = PrintThis()
printme.HashTag120()


my_dict = {'color': 'red', 'fruit': 'apple', 'species':'dog'}

my_dict['color']
print("Iterate over a dictionary and get the KEY:VALUE pair")
for key, value in my_dict.items():
    print(key, '-->', value)

#This is a built-in python function

#print(vars())
#print(locals())

#print(dir(my_dict))

#If you want to access just the value in a dict do this
print("If you want to access just the VALUE in a dict do this")
for value in my_dict.values():
    print(value)
print("If you want to access just the KEY in a dict do this")
for key in my_dict.keys():
    print(key)

print(my_dict.values())
print(my_dict.keys())
print("This will print out the item in each item".upper())
for item in my_dict.items():
    print(item[1])
print("This will print out the key in each item".capitalize())
for item in my_dict.items():
    print(item[0])

prices = {'brcm':'25.34', 'hpe':'14.75', 'msft':'155'}

for key, value in prices.items():
    print(key, '-->', value)

prices['brcm'] = 33.52
print('The price of brcm went up')
for key, value in prices.items():
    print(key, '-->', value)

prices['Intel'] = 75.47
print('Added Intel stock to the dictionary')
for key, value in prices.items():
    print(key, '-->', value)

printme.HashTag120()

incomes = {'Patrick': 120000, 'Beatriz': 75000, 'Joseph': 45000}

total_incomes = 0

for key, income in incomes.items():
    total_incomes += income

print("The total income of the family {:,}" .format(total_incomes, '.2d'))

print(f'The total income of the family {total_incomes:,}')

print('Dictionary comprehension'.upper)

colors = ['Red','Blue','Orange']
objects = ['Car','Blouse','Tophat']
print(colors)
print(objects)
print('Example of taking two lists, using the zip(), and creating a dictionary using dict comprehension\n')
new_dict = {key: value for key, value in zip(colors, objects)}
print(new_dict)

print('Using the new_dict, we\'ll a dict comprehension to swap key:value pair')

new_dict2 = {value: key for key, value in new_dict.items()}

print(f'This is the new dictionary: {new_dict2}')

next_dict = {key: value for key, value in new_dict.items() if key == 'Red'}

print(next_dict)

printme.HashTag120()
dict1 = vars()


for key, value in list(dict1.items()):
    print(key, '-->' ,value)




