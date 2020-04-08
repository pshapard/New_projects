import sys
import getpass



def OutPutToCountryLog():
    """Open and reads main log file, TestResults.txt
       Searches main log file and retrieves data for each country
       and outputs the data to each country's log file """
    filename = 'TestResults.txt'
    
    output_file = {'World':'logfile_world.txt',
                   'Us':'logfile_usa.txt',
                   'France':'logfile_france.txt',
                   'Spain':'logfile_spain.txt',
                   'Germany':'logfile_germany.txt',
                   'Uk':'logfile_uk.txt',
                   'Iran':'logfile_iran.txt',
                   'Italy':'logfile_italy.txt'}
    
    for string, logfile in output_file.items():
        with open(filename) as f:
            datafile = f.readlines()
            string_found = [line for line in datafile if string in line]
            with open(logfile, 'w') as inf:
                for line in string_found:
                    inf.write(line)


