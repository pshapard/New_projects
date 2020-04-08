#!/usr/bin/python
#Author: Patrick Shapard
#Created: 04/06/2020
#Please note:  If you have multiple frolders in various locations change the source_dir to a list, e.g.
#source_dir_list = ['c:\\folder1', 'c:\\folder2']

import os, shutil

source_dir = ['c:\\folder']
dest_dir = 'd:\\folder'

def BackupFiles(source_dir, dest_dir):
    for source_dir in source_dir_list:
        for src_dir, dirs, files in os.walk(source_dir):
            dst_dir = src_dir.replace(source_dir, dest_dir, 1)
            if not os.path.exists(dst_dir):
                os.makedirs(dst_dir) 
            for file_ in files:
                src_file = os.path.join(src_dir, file_)
                dst_file = os.path.join(dst_dir, file_)
                if os.path.exists(dst_file):
                    os.remove(dst_file)
                print(f"Copying to {dst_file}")
                try:
                    shutil.copy(src_file, dst_dir)
                except PermissionError:
                    print(f'encountered an error copying file: {dest_file}')


def main():
    BackupFiles(source_dir, dest_dir)


if __name__ == '__main__':
    main()