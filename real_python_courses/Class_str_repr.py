class Car:
    def __init__(self, color, mileage):
        self.color = color
        self.mileage = mileage

    def __repr__(self):
    
	
my_car = Car('red', 37281)
print(my_car)

#__str__ ==> easy to read, for human consuption
#__repr__ ==> unambiguous, more for developers to read

import datetime

today = datetime.date.today()

print(str(today))
print(repr(today))
print(today)