# Genetic Algorithm for Vehicle Routing Optimization
import random
from vehicle import Vehicle
random.seed("WGUPS")


# Helper functions for distance calculation and to see if everything will be on time
# Function to calculate route distance
def calculate_route_distance(route, matrices, packages, start_time, hub=0):
    if not route:
        return 0

    d_matrix, t_matrix = matrices
    
    total_distance = 0
    current_address = hub
    tmp_packs = packages.safe_copy()
    time = start_time
    ontime = True
    
    # Calculate distance through all stops
    for package_id in route:
        package = tmp_packs.get(package_id)
        next_address = package.address
        total_distance += d_matrix[current_address][next_address]
        time += t_matrix[current_address][next_address]
        #running logic to check to see if the route produces on time deliveries for all packages
        ontime = package.ontime() and ontime
        current_address = next_address


    #return to hub
    #This is skipped in the fitness evaluation in order to speed computation rate as it has minimal effect
    #on overall fitness
    #total_distance += d_matrix[current_address][hub]
    
    return total_distance, ontime


# Initial population with constraints
# Constant time operation O(p) where p is population size (a constant)
def create_initial_population(pop_size, trucks):
    population = []
    # Create the initial population
    for i in range(pop_size):
        # Create a new solution
        solution = []
        
        # Copy package lists by value
        tmp1_pkgs = list(trucks[0].packages)
        tmp2_pkgs = list(trucks[1].packages)
        tmp3_pkgs = list(trucks[2].packages)
        
        # Shuffle each truck's route
        random.shuffle(tmp1_pkgs)
        random.shuffle(tmp2_pkgs)
        random.shuffle(tmp3_pkgs)
        
        # Add to solution
        solution.append(tmp1_pkgs)
        solution.append(tmp2_pkgs)
        solution.append(tmp3_pkgs)
        
        # Add the solution to the population
        population.append(solution)
    
    return population

# Evaluate fitness of the population
def evaluate_fitness(population, my_packages, matrices, trucks):
    fitness_scores = []

    for solution in population:
        total_distance = 0
        solution_ontime = True
        # Calculate distance for each truck's route
        for i, route in enumerate(solution):
            start_time = trucks[i].depart_time
            tmp_distance, tmp_ontime = calculate_route_distance(route, matrices, my_packages, start_time)
            total_distance += tmp_distance
            solution_ontime = solution_ontime and tmp_ontime

        # Fitness is inversely proportional to distance and being a solution that delivers all on time flips the sign
        # meaning it will always be preferred.
        if solution_ontime:
            fitness = 1.0 / total_distance
        else:
            fitness = -1.0 * total_distance
        fitness_scores.append((solution, fitness, total_distance))
    
    # Sorts by fitness (x->x[1] maps to fitness_scores[x[1]], higher is better, so it's reversed)
    fitness_scores.sort(key=lambda x: x[1], reverse=True)
    return fitness_scores

# Selection function
def selection(population_fitness, num_parents):
    # Tournament selection
    selected_parents = []

    for _ in range(num_parents):
        # Select random competitors
        tournament_size = min(5, len(population_fitness))
        competitors = random.sample(population_fitness, tournament_size)

        # Select the best competitor and add them to the selected parents
        best = max(competitors, key=lambda x: x[1])
        selected_parents.append(best[0])

    return selected_parents

# Crossover function
def crossover(parents, crossover_rate):
    offspring = []
    
    for i in range(0, len(parents), 2):
        if i + 1 < len(parents):
            parent1 = parents[i]
            parent2 = parents[i + 1]
            
            if random.random() < crossover_rate:
                # Create two new offspring
                child1 = []
                child2 = []
                
                # For each truck route
                for j in range(len(parent1)):
                    # Create route maps for quick lookup
                    p1_route = parent1[j]
                    p2_route = parent2[j]
                    
                    # Pick crossover point
                    crossover_point = random.randint(1, min(len(p1_route), len(p2_route)) - 1)
                    
                    # Create children by combining routes
                    c1_route = p1_route[:crossover_point] + [pkg for pkg in p2_route if pkg not in p1_route[:crossover_point]] 
                    c2_route = p2_route[:crossover_point] + [pkg for pkg in p1_route if pkg not in p2_route[:crossover_point]]
                    
                    child1.append(c1_route)
                    child2.append(c2_route)
                
                offspring.append(child1)
                offspring.append(child2)
            else:
                # No crossover, just copy parents
                offspring.append(parent1)
                offspring.append(parent2)
    
    return offspring

# Mutation function
def mutation(offspring, mutation_rate):
    mutated_offspring = []
    
    for solution in offspring:
        if random.random() < mutation_rate:
            # Making a copy by value, failing to do this was the cause of a bug that
            # I missed early on which caused the mutated offspring to alter their parent solution during data
            # manipulation.
            mutated_solution = [list(route)for route in solution]

            # Choose a random truck route to mutate
            truck_idx = random.randint(0, len(mutated_solution) - 1)
            route = mutated_solution[truck_idx]
            
            if len(route) >= 2:
                # Swap mutation - swap two random positions
                idx1, idx2 = random.sample(range(len(route)), 2)
                route[idx1], route[idx2] = route[idx2], route[idx1]
            
            # Insert the mutated solution
            mutated_offspring.append(mutated_solution)
        else:
            # No mutation append a copy of the solution
            mutated_offspring.append([list(route)for route in solution])
    
    return mutated_offspring

# Genetic algorithm
def genetic_algorithm(trucks, packages, matrices, pop_size=50, generations=100, crossover_rate=0.9, mutation_rate=0.2):
    # Create initial population
    population = create_initial_population(pop_size, trucks)
    
    best_solution = None
    best_distance = float('inf')
    
    # Evolution process
    for generation in range(generations):

        # Evaluates fitness of the population members
        population_fitness = evaluate_fitness(population, packages, matrices, trucks)
        
        # Store the best solution for the generation
        current_best = population_fitness[0]
        if current_best[2] < best_distance:
            best_solution = current_best[0]
            best_distance = current_best[2]
            # this print statement uses \r and an end="" to keep updating the text in place.
            print(f"\rGeneration {generation}: New best distance = {best_distance:.1f} miles (not including return leg).", end="")
        
        # Select parents based on fitness score for the population, reproductive success rate (which is really it's
        # inverse here) determines how many parents are selected from the total population.
        reproductive_success_rate = 2
        parents = selection(population_fitness, pop_size // reproductive_success_rate)
        
        # Crossover
        offspring = crossover(parents, crossover_rate)
        
        # Mutation
        offspring = mutation(offspring, mutation_rate)
        
        # Create new population with elitism (keep the best (pop_size / survival_rate) solution)
        survival_rate = 20
        elite_count = max(1,pop_size//survival_rate)
        elites = [e[0] for e in population_fitness[:elite_count]]
        population = elites + offspring[:(pop_size-elite_count)]


    return best_solution, best_distance

# Function to simulate delivery with the optimized routes.
def simulate_delivery(solution, trucks, packages, matrices):
    hub_address = 0
    d_matrix, t_matrix = matrices

    # Clone the trucks
    truck_clones = [Vehicle(t.capacity,t.speed,t.load,t.packages, t.mileage, t.address, t.depart_time) for t in trucks]

    #reset mileage
    for truck in truck_clones:
        truck.mileage = 0.0

    # Update each truck's package list with the optimized route
    for i, route in enumerate(solution):
        truck_clones[i].packages = route
   #     print(f'precheck test for travel time on truck {calculate_route_distance(route,distances,addresses,packages,hub_address)} for route {route}')

    # find the best truck to return

    # Simulate the delivery for each truck
    for t in range(len(truck_clones)):
        current_address = hub_address
        current_time = truck_clones[t].depart_time


        # Process each package in the route
        for package_id in truck_clones[t].packages:
            package = packages.get(package_id)
            next_address = package.address
            distance = d_matrix[current_address][next_address]
            travel_time = t_matrix[current_address][next_address]

            #update truck position and time
            truck_clones[t].mileage += distance
            current_time += travel_time

            #Update Package Status
            package.time_departed = truck_clones[t].depart_time
            package.time_delivered = current_time
            package.update(current_time)

            current_address = next_address

        # Send vehicle 1 to the hub to pick up vehicle 3.
        # upon further inspection of the requirements, this isn't needed, day ends at 40 packages delivered, trucks
        # CAN return to depot, but it is not actually a stated requirement.
        if t == 0:
            truck_clones[t].mileage += d_matrix[current_address][0]
            current_time += t_matrix[current_address][0]
            truck_clones[2].depart_time = max(current_time, truck_clones[2].depart_time)
            print(f'\nTruck {t+1} is selected to return to hub to retrieve Vehicle 3, returned at time {current_time}')

    
    # Calculate total mileage
    total_mileage = sum(truck.mileage for truck in truck_clones)
    
    return truck_clones, total_mileage, packages
