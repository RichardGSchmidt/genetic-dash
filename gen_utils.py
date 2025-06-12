import csv
import datetime
import random

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
def get_matrices(speed):
    d_matrix = load_distances()
    t_matrix = get_time_matrix(d_matrix, speed)
    return d_matrix, t_matrix

def load_packages(qty,d_matrix):
    packages = HashChain()
    existing_ids = set()
    address_count = len(d_matrix)

    with open("./data/packages.csv", 'r') as myFile:
        items = list(csv.reader(myFile))
        for item in items:
            pkg_id = int(item[0])
            pkg = Package(pkg_id, item[1], item[2])
            packages.insert(pkg_id, pkg)
            existing_ids.add(pkg_id)
            qty -= 1
            if qty == 0:
                return packages

    # If qty not yet met, generate dummy entries with placeholder address/time_due
    next_id = max(existing_ids) + 1 if existing_ids else 1
    while qty > 0:
        if random.random() > 0.2:
            addr = random.randrange(0,address_count)
            packages.insert(next_id, Package(next_id,addr , "EOD"))
        else:
            #random time between 9:30 and 12:30
            addr = random.randrange(0, address_count)
            base_time = 9 * 60 + 30
            end_time = 12 * 60 + 30
            random_minutes = random.randrange(base_time, end_time + 1, 5)
            hours = random_minutes // 60
            minutes = random_minutes % 60
            time_due = f"{hours:02d}:{minutes:02d}"
            packages.insert(next_id, Package(next_id, addr, time_due))
        next_id += 1
        qty -= 1

    return packages