
import os
import sys
#print(vars())

os_contains = dir(os)


cpu = os.cpu_count()
login = os.getlogin()
cur_dir = os.getcwd()
env = os.environ
#walk_me = 
#print(help(os.walk))


print(cpu)
print(login)
print(cur_dir)
#print(walk_me)


for key, value in env.items():
    #print(key, value)
    if key == 'PYTHONPATH':
        python_path = value
    elif key == 'PROCESSOR_REVISION':
        proc_rev = value

print(python_path)
print(proc_rev)

#os.system()
#list = iter(os_contains)

#for x in list:
#   print(x)


