from vehicle import Vehicle


class Genome:
    def __init__(self, truck_count, capacity, speed, packages, mileage, address, departure_time):
        self.trucks = []

        self.capacity = capacity
        self.speed = speed
        self.packages = packages


    def __str__(self):
        return  (f'Genome Return String')