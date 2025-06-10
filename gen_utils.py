import csv
import datetime
from model.hashchain import HashChain
from model.package import Package

#used to load distance matrix and time matrix.  Imported from my c950 project.


def load_distances():
    # Load distances from csv file as a symmetrical distance map
    with open("data/distances.csv", 'r') as myFile:
        tmp = list(csv.reader(myFile))
        d_matrix = []
        for i, row in enumerate(tmp):
            row_values = []
            for j in range(len(row)):
                if row[j] == '':
                    row_values.append(float(tmp[j][i]))
                else:
                    row_values.append(float(row[j]))
            d_matrix.append(row_values)
    return d_matrix

#Pregenerate a time matrix so slow math (division) only needs to be calculated once
def get_time_matrix(d_matrix, speed):
    time_matrix = [
        [datetime.timedelta(hours=val / speed) for val in row]
        for row in d_matrix
    ]
    return time_matrix

#get both distance and time matrix as a tuple
def get_matrices():
    d_matrix = load_distances()
    t_matrix = get_time_matrix(d_matrix, 18)
    return d_matrix, t_matrix

def load_packages():
    # Load packages
    packages = HashChain()
    with open("./data/packages.csv", 'r') as myFile:
        items = list(csv.reader(myFile))
        for item in items:
            # Create package object
            pkg = Package(
                int(item[0]),  # package id
                item[1],  # address
                item[2])  # time_due
            # item = Package(0,1,2,3,4,5,6,7,8)
            # Insert into hash chain in accordance with ta
            packages.insert(int(item[0]), pkg)
        return packages