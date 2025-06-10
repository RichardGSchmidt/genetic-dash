#Initialization section
import vehicle
import datetime
from package import get_header, Package
from genetic_algorithm import genetic_algorithm, simulate_delivery
from fileops import load_data


matrices, addresses, packages = load_data()

HUB = 0

#function to get a string output off all packages status and details
def str_all_packages(package_hashmap):
    keys = package_hashmap.keys()

    #get package header
    return_string = f'\n{get_header()}\n'

    #add all package printouts after the header string
    for ki in keys:
        return_string = return_string + f'{package_hashmap.get(ki)}\n'
    return return_string

#function to update the status of all packages for a given time
def update_all_packages(query_time,package_hashmap):
    for ki in package_hashmap.keys():
        pack = package_hashmap.get(ki)
        pack.update(query_time)
        if ki == 9:
            if query_time >= datetime.timedelta(hours=10, minutes=20):
                pack.address = 19
            else:
                pack.address = 12
#function that returns a string to display truck status for a given route
def get_truck_status(trucks, truck_index, query_time, package_hashmap, address_map):
    truck = trucks[truck_index]
    tmp_packs_delivered = []
    str_out = ''
    #must be by value otherwise this breaks
    tmp_packs_left = list(truck.packages)
    #divide keys up into what's delivered and what's left based on query time.
    for key in truck.packages:
        if package_hashmap.get(key).time_delivered <= query_time:
            tmp_packs_delivered.append(key)
            tmp_packs_left.remove(key)
    truck_distance = 0
    #if the truck hasn't left yet
    if truck.depart_time > query_time:
        str_out = f'Truck {truck_index + 1} for {query_time}-\tAwaiting Departure\t\tRemaining: {tmp_packs_left} Mileage = {truck_distance:.1f}\n'
    #in the event the truck has left the hub but hasn't reached the first package
    elif len(tmp_packs_delivered) == 0:
        truck_distance = truck.speed * (query_time - truck.depart_time).total_seconds() / 3600
        str_out = f'Truck {truck_index +1} for {query_time}-\tDelivering Package {tmp_packs_left[0]}\tRemaining: {tmp_packs_left} Mileage = {truck_distance:.1f}\n'
    #in the event the vehicle is between two delivery points
    elif len(tmp_packs_left) > 0 and len(tmp_packs_delivered) > 0:
        truck_distance = truck.speed * (query_time - truck.depart_time).total_seconds() / 3600
        str_out = f'Truck {truck_index +1} for {query_time}-\tDelivering Package {tmp_packs_left[0]}\tDelivered: {tmp_packs_delivered}\tRemaining: {tmp_packs_left} Mileage = {truck_distance:.1f}\n'
    #in the event the route is complete
    elif len(tmp_packs_left) == 0:
        truck_distance = truck.mileage
        #logic splits as only truck 1 (at index 0) returns to the hub in accordance with the requirements.
        if truck_index == 1 or truck_index == 2:
            address_string = f"{address_map[tmp_packs_delivered[-1]][1]}"
            str_out = f'Truck {truck_index + 1} for {query_time}-\tParked at {address_string}\tDelivered: {tmp_packs_delivered} Mileage = {truck.mileage:.1f}\n'
        else:
            if query_time < truck.time:
                str_out = f'Truck {truck_index +1} for {query_time}-\tIn Route to Hub\t\tDelivered: {tmp_packs_delivered} Mileage = {truck.mileage:.1f}\n'
            else:
                str_out = f'Truck {truck_index +1} for {query_time}-\tAt Hub - Done\tDelivered: {tmp_packs_delivered} Mileage = {truck.mileage:.1f}\n'
    return str_out, truck_distance

#Method that cycles through all trucks and gets status text
def get_all_trucks_status(trucks, query_time, package_hashmap, address_map):
    string_out = ''
    total_miles = 0
    for t in range(len(trucks)):
        tmp_str_out, tmp_distance = get_truck_status(trucks, t, query_time, package_hashmap, address_map)
        string_out += tmp_str_out
        total_miles += tmp_distance
    string_out += f'Total Miles for all trucks: {total_miles:.1f}\n'
    return string_out


#Vehicles to be tested in the algorithm
wgups1 = vehicle.Vehicle(16,18,None,[1,13,14,15,16,19,20,21,27,29,30,34,35,37,39,40],0.0, HUB, datetime.timedelta(hours=8))
wgups2 = vehicle.Vehicle(16,18,None,[3,6,7,11,12,18,22,23,24,25,26,31,32,36,38],0.0, HUB, datetime.timedelta(hours=9, minutes= 5))
wgups3 = vehicle.Vehicle(16,18,None,[2,4,5,8,9,10,17,28,33],0.0, HUB, datetime.timedelta(hours=10, minutes= 20))


# Run the genetic algorithm
best_solution, best_distance = genetic_algorithm(
    [wgups1, wgups2, wgups3],
    packages,
    matrices,
    pop_size=4000,
    generations=32,
    crossover_rate=0.9,
    mutation_rate= 0.05
)

# Simulate delivery with the optimized solution
optimized_trucks, total_mileage, optimized_packages = simulate_delivery(best_solution, [wgups1,wgups2,wgups3], packages, matrices)

print(f"\nbest solution:\nTruck 1: {best_solution[0]}\nTruck 2: {best_solution[1]}\nTruck 3: {best_solution[2]}")

go_time = datetime.timedelta(hours=23, minutes=59)
update_all_packages(go_time,optimized_packages)
print(f'optimized packages:{str_all_packages(optimized_packages)}')
print(f'total milage: {total_mileage:.1f}, Truck1 = {optimized_trucks[0].mileage:.1f}, Truck2 = {optimized_trucks[1].mileage:.1f}, Truck3 = {optimized_trucks[2].mileage:.1f}')


#Interactive UI Segment
package_string = 'All'
#control loop
while package_string.lower() != "q" and package_string.lower() != "quit":
    #Try / except blocks along with the raise value error are used to scan for bad user inputs and to exit the program
    #in the event bad inputs are passed to the program
    try:
        package_string = input('Please select a package number, enter A for all packages, or Q to quit:')
        #requesting to quit breaks to the loop immediately, where the loop is exited.
        if package_string.lower() == "q" or package_string.lower() == "quit":
            break
        #if a printout of all packages is requested, the method for displaying all packages is called for the target
        #time
        if package_string.lower() == "a" or package_string.lower() == "all" or package_string.lower() == "al":
            time_string = input('Please enter a Time group in the following format (HH:MM:SS) with leading zeroes:')
            go_time = datetime.timedelta(hours=int(time_string[0:2]), minutes=int(time_string[3:5]), seconds=int(time_string[6:8]))
            update_all_packages(go_time, optimized_packages)
            print(f'\nDisplaying all packages for time {go_time}')
            #print out all packages
            print(str_all_packages(optimized_packages))
            #print out truck status
            tmp_string = get_all_trucks_status(optimized_trucks, go_time, optimized_packages, addresses)
            print(tmp_string)
        #if a printout of a specific package is requested, the display method for the individual package is used instead.
        elif int(package_string) in optimized_packages.keys():
            time_string = input('Please enter a Time group in the following format (HH:MM:SS) with leading zeroes:')
            go_time = datetime.timedelta(hours=int(time_string[0:2]), minutes=int(time_string[3:5]), seconds=int(time_string[6:8]))
            update_all_packages(go_time, optimized_packages)
            #print out all packages
            print(f'Packages {package_string} for time {go_time}\n{get_header()}\n{optimized_packages.get(int(package_string))}')
            #print out truck status
            tmp_string = get_all_trucks_status(optimized_trucks, go_time, optimized_packages, addresses)
            print(tmp_string)
        #if the first input doesn't match any of the designated inputs, raise and exception to close the program
        else:
            raise ValueError('Invalid input. CLosing the program')
    except ValueError:
        print('Invalid input. Closing the program.')
        exit(1)
#goodbye text once the loop is exited and the program has closed normally.
print(f"Exiting program, have a nice day!")



