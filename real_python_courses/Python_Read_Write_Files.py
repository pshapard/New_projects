#Reading and writing files
"""
file = open('xmlfiles.txt')

file.close()

#Better way is using a context manager

read(5) this reads the first 5 bytes of the file
readline() this reads the first line of the files
readlines() This reads the all lines in the files and creates a list
with each line as an element

write() used to write a single line
writelines() is used to write a list of elements which are lines

The default mode of opening a file is read, which does not require an argument





with open('c:\\python38\\RealPython\\xmlfiles.txt', 'r') as file:
    datafile = file.readlines()
    print(datafile)


with open('c:\\python38\\RealPython\\test_file.txt', 'w') as file:
    line = 'This is the line to write to the new file\r\n'
    file.write(line)
    new_line = 'This is another newline to write to the new file\r\n'
    file.write(new_line)


with open('c:\\python38\\RealPython\\another_file.txt', 'w') as file:
    datafile = ['First line\r\n','Second line\r\n','Third line\r\n','Fourth line\r\n']
    file.writelines(datafile)


with open('c:\\python38\RealPython\\xmlfiles.txt', 'r') as fileIn, \
    open('c:\\python38\RealPython\\nex_new_file.txt', 'a') as fileOut:
    datafile = fileIn.readlines()
    for line in datafile:
        fileOut.write(line.upper())

with open('c:\\python38\\RealPython\\test_file.txt', 'a') as fileObj:
    content = 'You can use either write() or writelines()\r\n'
    fileObj.write(content)

import os
folder_path = os.path.join('C:', os.sep, 'Drivers','Drivers_fw', 'new_file.txt')

with open(folder_path, 'a') as fileObj:
    content = 'You can use either write() or writelines()\r\n'
    fileObj.write(content)


with open(filename, 'r') as fileIn, open('c:\\python38\RealPython\\Warning.log', 'w') as fileOut:
    datafile = fileIn.readlines()
    for line in datafile:
        if 'WARN' in line:
            fileOut.writelines(line)
"""
filename = 'c:\\SupportDumps\\Eagle21\\ciDebug.log'
output_file = {'ERROR': 'ERROR.log',
               'INFO': 'INFO.log',
               'WARN': 'WARN.log'}

for string, logfile in output_file.items():
    with open(filename, 'r') as fileIn:
        datafile = fileIn.readlines()
        string_found = [line for line in datafile if string in line]
        with open(logfile, 'w') as fileOut:
            for line in string_found:
                fileOut.writelines(line)


