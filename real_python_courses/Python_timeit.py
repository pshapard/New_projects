import timeit


my_time = timeit.timeit('"-".join(str(n) for n in range(100))', number=10000)
print(my_time)
my_time1 = timeit.timeit('"-".join([str(n) for n in range(100)])', number=10000)
print(my_time1)
my_time2 = timeit.timeit('"-".join(map(str, range(100)))', number=10000)
print(my_time2)

