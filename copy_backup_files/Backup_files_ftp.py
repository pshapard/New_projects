#/usr/bin/python
#Author: Patrick Shapard
# created: 02/05/2020
# updated: 04/08/2020
#This script automates the backup of files from local hard drvie to windows ftp server.

import logging
from ftplib import FTP
import os
import time


#Global variables
user = 'username used to login'
passwd = 'password used to login'
ftp = FTP('ip address of ftp server')
folders_dict = {'C:\Python27':'Python27'}

def copyFiles(ftp, path):
    """function to copy local files to remote ftp server."""
    for name in os.listdir(path):
        localpath = os.path.join(path, name)
        print(localpath)
        if os.path.isfile(localpath):
            print("STOR", name, localpath)
            ftp.storbinary('STOR ' + name, open(localpath,'rb'))
        elif os.path.isdir(localpath):
            print("MKD", name)


def FtpProgram():
    """Main function to establish and tear down ftp connection. """
    TimeStamp = time.strftime("%m%d%Y_%H%M%S")
    #Create main folder on ftp server
    main_folder = ('Backup_' + TimeStamp)
    ftp.login(user=user, passwd = passwd)
    ftp.mkd(main_folder)
    ftp.cwd(main_folder)
    #for loop to iterate thru folder dict to copy local files to remote ftp server folders
    for path, folder in folders_dict.items():
        ftp.mkd(folder)
        ftp.cwd(folder)
        copyFiles(ftp, path)
        ftp.cwd("..")
    ftp.quit()


def main():
    FtpProgram()

    
if __name__ == '__main__':
    main()
