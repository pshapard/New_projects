#Python variables

a, b = 250, 260

for _ in range(250, 260):
    if a is not b:
        break

    a += 1
    b += 1

print(a)

x = 32804
y = 32804

print(x is y)
print(id(x))
print(id(y))

x = 300;y = 300
print(x is y)

import keyword

print("The following are keywords used by python in which you cannot use to assign a variable". upper())
help("keywords")
help('global')
help('assert')

print(keyword.kwlist)

