# Project: Master Thesis
# Author: Yuanlin Dong
# Date of creation: 2023-04-11


import csv
from csv import DictReader

def infile_2_list(filepath, filename):
    file = filepath + filename
    python_list = []
    with open(file, 'r') as f:
        for line in csv.reader(f):
            python_list.append(line)
    return python_list

