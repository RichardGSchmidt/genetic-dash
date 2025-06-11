import random
from model.vehicle import Vehicle
import datetime


class Genome:
    def __init__(self, trucks, packages, departure_time=datetime.timedelta(hours=8)):
        self.trucks = trucks
        self.package_list = packages.keys()
        self.departure_time = departure_time
        self.packages = packages
        self.truck_count = len(trucks)
        #stuff for output
        self.totalmiles = 0
        self.late_packages = []
        self.active_trucks = -1



    def append_to_truck(self, pack_id ,truck_index):
        target_truck = self.trucks[truck_index]
        self.remove_from_trucks(pack_id)
        target_truck.packages.append(pack_id)

    def make_copy(self):
        trucks = [
            Vehicle(
                t.capacity,
                t.speed,
                list(t.packages),  # shallow copy of package IDs
                0,  # reset mileage
                0,  # reset address
                t.depart_time
            )
            for t in self.trucks
        ]
        return Genome(trucks, self.packages)


    def swap_packages(self, pid1, pid2):
        #if the roll is for the same append to last truck
        if pid1 == pid2:
            self.remove_from_trucks(pid1)
            self.trucks[-1].packages.append(pid1)
            self.sort_genome()
            return

        truck1=truck2=None
        index1=index2=-1

        for truck in self.trucks:
            if pid1 in truck.packages:
                truck1 = truck
                index1 = truck.packages.index(pid1)
            if pid2 in truck.packages:
                truck2 = truck
                index2 = truck.packages.index(pid2)
            #if both exist, swap them
            if truck1 and truck2:
                if len(truck1.packages) > truck1.capacity or len(truck2.packages) > truck2.capacity:
                    return  # cancel swap if invalid
                truck1.packages[index1], truck2.packages[index2] = truck2.packages[index2], truck1.packages[index1]
        self.sort_genome()
        return


    def remove_from_trucks(self, pack_id):
        for truck in self.trucks:
            if pack_id in truck.packages:
                truck.packages.remove(pack_id)
        self.sort_genome()

    #This keeps the genome organized and prevents genes from fighting other rearrangements of themselves
    #It narrows the solution space quite a bit
    def sort_genome(self):
        self.trucks.sort(
            key=lambda truck: (
                -len(truck.packages), #more loaded trucks up top
                truck.packages[0] if truck.packages else float("inf") #Then by first package
            )
        )

    def sort_truck_routes_by_location(self, d_matrix):
        for truck in self.trucks:
            if not truck.packages:
                continue

            current_address = 0  # start at hub
            sorted_route = []
            remaining = list(truck.packages)

            while remaining:
                # Get closest package to current address
                closest_pkg = min(
                    remaining,
                    key=lambda pid: d_matrix[current_address][self.packages.get(pid).address]
                )
                sorted_route.append(closest_pkg)
                current_address = self.packages.get(closest_pkg).address
                remaining.remove(closest_pkg)

            truck.packages = sorted_route

    def distribute_packages(self):
        for truck in self.trucks:
            truck.packages = []

        truck_caps = [truck.capacity for truck in self.trucks]
        truck_loads = [0] * len(self.trucks)

        for pkg_id in self.package_list:
            for i in range(len(self.trucks)):
                if truck_loads[i] < truck_caps[i]:
                    self.trucks[i].packages.append(pkg_id)
                    truck_loads[i] += 1
                    break
            else:
                raise ValueError("Not enough capacity to assign all packages!")

    def fill_randomly(self):
        for truck in self.trucks:
            truck.packages = []

        package_ids = list(self.package_list)
        random.shuffle(package_ids)

        # Track truck loads
        truck_loads = [0] * len(self.trucks)
        truck_caps = [truck.capacity for truck in self.trucks]

        for pack_id in package_ids:
            # Only pick trucks that have room
            valid_trucks = [i for i, load in enumerate(truck_loads) if load < truck_caps[i]]
            if not valid_trucks:
                raise ValueError("Not enough capacity to assign all packages!")

            chosen_index = random.choice(valid_trucks)
            self.trucks[chosen_index].packages.append(pack_id)
            truck_loads[chosen_index] += 1

        self.sort_genome()

    def __str__(self):
        output = "Genome Truck Assignments:\n"
        for i, truck in enumerate(self.trucks):
            output += f"Truck {i + 1}: {truck.packages}\n"
        return output

