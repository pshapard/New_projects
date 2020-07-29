#Python while loops


while True:
    print("hello")
    break


n = 5

while n > 0:
    n -= 1
    if n == 2:
        print("n is now two, quitting")
        break
    else:
        print(n)

x = 5
while x > 0:
    x -= 1
    if x == 2:
        print("x is now two, moving on")
        continue
    else:
        print(x)

print("One line while loop")

a = 5
while a > 0: a -= 1; print(a)

