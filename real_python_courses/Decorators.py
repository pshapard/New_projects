"""
What is a decorator:

It's a function that takes another function
Extends the behavior of that function
without explicitly modifying the function
"""
import functools
def decorator_func(org_func):
    def wrapper_function():
        return org_func()
    return wrapper_function

def display():
    print('display function ran')

dec_display = decorator_func(display)
dec_display()


def my_decorator(func):
    @functools.wraps(func)
    def wrapper():
        print("something happen before calling func")
        func()
        print("something happen after calling func")
    return wrapper

def say_whee():
    print("Whee!")
#This is one way to call the decorator, but there is a better way
say_whee = my_decorator(say_whee)
say_whee()
print('='*70)
print("Below is the preferred way using the @my_decoratortwo placed just above say_whee()".upper())
def my_decoratortwo(func):
    @functools.wraps(func)
    def wrapper():
        print("something happen before calling func")
        func()
        print("something happen after calling func")
    return wrapper

@my_decoratortwo
def say_whee():
    print("Whee!")

say_whee()
print('='*70)
print("Below is an example of passing and return an argument to the decorator")

def decorator_func(org_func):
    @functools.wraps(org_func)
    def wrapper_function(*args, **kargs):
        #org_func(*args, **kargs)
        return org_func(*args, **kargs)
    return wrapper_function

@decorator_func
def display():
    print('display function ran')

display()
print('='*70)
print("Return a value from a decorator")

@decorator_func
def say_something(var1, var2):
    print(f'This is how you pass the first argument {var1} and second argument {var2}')
    return f'This is {var1}, I\'m learning {var2}'

@decorator_func
def greet(name):
    print(f'Creating greeting')
    return f'Hi {name}, look at me learning decorators in python'


say_hello = greet("World")
print(say_hello)

isaid_it = say_something('Patrick','Python')
print(isaid_it)

"""
The @functools.wraps(func)
This takes a function used in a decorator and adds the 
functionality of copying over the function name, docstring, arguments list, etc. 
"""

print(help(greet))




