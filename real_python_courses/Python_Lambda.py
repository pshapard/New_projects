#Lambda function, aka, anonymous function
#x =lambda a: a%2 == 1

print('#'*40)
my_list = [5749, 22, 342, 110, 249, 135, 1036, 1]

list_odd = list(filter(lambda x: x%2 == 1, my_list))
print(list_odd)

odd_list_sorted = sorted(list_odd)
print('Odd list sorted:', odd_list_sorted)
print('#'*40)

list_even = list(filter(lambda x: x%2 == 0, my_list))
print(list_even)
even_list_sorted = sorted(list_even)
print('Even list sorted:', even_list_sorted)

print('#'*40)
x, y, z = 1, 2, 3

def myfunc(x, y, z):
    result = x + y +z
    return result

sum = lambda x, y, z: x + y + z


#Appropriate use of a lambda unction

def second(x):
    return x[1]

a = [(1,2), (2,5), (3,1), (4,15)]
a.sort(key=second)

a.sort(key=lambda x: x[1])

square = lambda x: x**2
print(square(3))

#You can also use a default value for a lambda expression

multi = lambda x, y=3: x * y

print(multi(5, 5))

print('#'*120)
cmp = ['Michael Collins','Richard Gordon','Jack Swagert',\
       'Stuart Roose','Alfred Worden','Ken Mattingly','Ron Evans']

print(cmp)
cmp.sort()
print(cmp)
#Now, if you want to sort the list by last name using a lambda function

cmp.sort(key=lambda x: x.split()[-1])
print(cmp)
print('#'*120)
people = [('Steve', 35),('Karen',28),('Gerald', 58),('Joseph', 72 )]
print('List sorted by Name using a lambda function', '\n', people)
people.sort(key=lambda x: x[1])
print('List sorted by age using a lambda function', '\n' ,people)


class Person():

    def __init__(self, name, age):
        self.name = name
        self.age = age

    def __repr__(self):
        return f'{self.name}: {self.age}'


eddie = Person('Eddie', 70)
julie = Person('Julie', 34)
stuart = Person('Stuart', 54)

p = [eddie, julie, stuart]
print(p)
print('The list is sorted by age', p)
p.sort(key=lambda x: x.age)
print('The list is sorted by name', p)
p.sort(key=lambda x: x.name)
print('#'*120)
print("The use of the filter funtion with the lambda function")

nums = list(range(1, 21))
print(nums)
evens = list(filter(lambda x: x % 2 == 0, nums))
print('List of even nums using lambda function', evens)

odd = list(filter(lambda x: x % 2 != 0, nums))
print('List of odd nums using lambda function', odd)

from statistics import mean

data = list(range(1, 21))
avg = mean(data)

above_avg = list(filter(lambda x: x > avg, data))

print(data)
print(avg)
print(above_avg)



