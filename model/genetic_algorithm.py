# Genetic Algorithm for Vehicle Routing Optimization
import random
from model.vehicle import Vehicle
from model.genome import Genome
random.seed("WGUPS")



# Initial population with constraints
# Constant time operation O(p) where p is population size (a constant)
def create_initial_population(pop_size, base_genome,seed_genomes=None):
    if seed_genomes is None:
        seed_genomes = []
    population = []

    for seed in seed_genomes:
        population.append(seed.make_copy())
        if len(population) >= pop_size:
            return population[:pop_size]

    # Create the initial population
    while len(population) < pop_size:
        # Deep-copy trucks so each genome has its own independent route state
        genome = base_genome.make_copy()
        genome.fill_randomly()
        population.append(genome)
    return population

# Evaluate fitness of the population
def evaluate_fitness(population, matrices):
    fitness_scores = []
    d_matrix, t_matrix = matrices

    for genome in population:
        genome.sort_truck_routes_by_location(d_matrix)
        for pkg_id in genome.package_list:
            pkg = genome.packages.get(pkg_id)
            pkg.time_delivered = None
        genome.late_packages = []
        # Calculate distance for each truck's route
        for pkg_id in genome.package_list:
            pkg = genome.packages.get(pkg_id)
            pkg.time_delivered = None
        for truck in genome.trucks:
            truck.mileage = 0.0
            truck.time = genome.departure_time
            truck.departure_time = genome.departure_time
            truck.address = 0
            truck.delivery_log = []#to hold deliveries for Dash
            for idx, package_id in enumerate(truck.packages):
                #if the vehicle is empty it goes to the station to refill if there are more packages
                #if idx % truck.capacity == 0 and idx != 0:
                #    truck.mileage += d_matrix[truck.address][0]
                #    truck.time += t_matrix[truck.address][0]
                #    truck.address = 0

                #get package from the genome
                pkg = genome.packages.get(package_id)
                next_address = pkg.address

                #go to next address and deliver the package
                truck.mileage += d_matrix[truck.address][next_address]
                truck.time += t_matrix[truck.address][next_address]
                truck.address = next_address

                pkg.time_delivered = truck.time
                truck.delivery_log.append((package_id, truck.time))
                if not pkg.ontime(truck.time):
                    genome.late_packages.append(package_id)

            #return to hub at the end of the day
            if truck.address != 0:
                truck.mileage += d_matrix[truck.address][0]
                truck.time += t_matrix[truck.address][0]

        active_trucks = 0
        total_mileage = 0.0
        for truck in genome.trucks:
            if len(truck.packages) > 0:
                active_trucks += 1
                total_mileage += truck.mileage
        total_cost = total_mileage + len(genome.late_packages) * 20.0 + active_trucks * 20

        # Fitness is inversely proportional to total cost.
        fitness = 1.0 / (total_cost + 1)
        fitness_scores.append((genome, fitness, total_cost))
    
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
        if i + 1 >= len(parents):
            break

        parent1 = parents[i]
        parent2 = parents[i + 1]

        if random.random() < crossover_rate:
            child1 = parent1.make_copy()
            child2 = parent2.make_copy()

            # Step 1: Clear child truck routes
            for truck in child1.trucks:
                truck.packages = []
            for truck in child2.trucks:
                truck.packages = []

            assigned1 = set()
            assigned2 = set()

            # Step 2: Randomly pick half of the trucks from each parent
            truck_indices = list(range(len(parent1.trucks)))
            random.shuffle(truck_indices)
            half = len(truck_indices) // 2

            for idx in truck_indices[:half]:
                child1.trucks[idx].packages = list(parent1.trucks[idx].packages)
                assigned1.update(parent1.trucks[idx].packages)

                child2.trucks[idx].packages = list(parent2.trucks[idx].packages)
                assigned2.update(parent2.trucks[idx].packages)

            # Step 3: Assign missing packages to remaining trucks
            all_ids = set(parent1.package_list)
            remaining1 = list(all_ids - assigned1)
            remaining2 = list(all_ids - assigned2)

            # Distribute remaining1 to child1, respecting capacity
            fill_remaining_packages(child1.trucks, remaining1)

            # Distribute remaining2 to child2, respecting capacity
            fill_remaining_packages(child2.trucks, remaining2)

            child1.sort_genome()
            child2.sort_genome()
            offspring.append(child1)
            offspring.append(child2)
        else:
            offspring.append(parent1.make_copy())
            offspring.append(parent2.make_copy())

    return offspring

def fill_remaining_packages(trucks, remaining_packages):
    truck_loads = [len(t.packages) for t in trucks]
    truck_caps = [t.capacity for t in trucks]

    for pkg in remaining_packages:
        valid_trucks = [i for i in range(len(trucks)) if truck_loads[i] < truck_caps[i]]
        if not valid_trucks:
            raise ValueError("Not enough truck capacity to place all packages during crossover!")
        choice = random.choice(valid_trucks)
        trucks[choice].packages.append(pkg)
        truck_loads[choice] += 1


# Mutation function
def mutation(offspring, mutation_rate):
    mutated = []

    for g in offspring:
        genome = g.make_copy()

        if random.random() < mutation_rate:
            #Pick two random package ID's to swap
            pkg_ids = list(genome.package_list)
            if len(pkg_ids) >= 2:
                pid1, pid2 = random.sample(pkg_ids,2)
                genome.swap_packages(pid1,pid2)
        mutated.append(genome)

    return mutated

# Genetic algorithm
def genetic_algorithm(truck_count, truck_capacity, truck_speed, packages, matrices, pop_size=50, generations=100, crossover_rate=0.9, mutation_rate=0.2,best_solutions_out=None,seed_genomes=None):
    # Create initial population
    if best_solutions_out is None:
        best_solutions_out = []
    else:
        best_solutions_out.clear()
    trucks = []
    for i in range(truck_count):
         trucks.append(Vehicle(truck_capacity, truck_speed, [], 0, 0))
    genome = Genome(trucks, packages)

    population = create_initial_population(pop_size, genome,seed_genomes=seed_genomes)
    
    best_solutions = []
    best_distance = float('inf')

    # Evolution process
    for generation in range(generations):
        population_fitness = evaluate_fitness(population, matrices)
        current_best = population_fitness[0]
        current_cost = current_best[2]

        # Only save if this is a new best solution
        if current_cost < best_distance:
            best_distance = current_cost
            print(f"Generation {generation}: New best cost = {best_distance:.1f}.")
            print(current_best[0])

            best_solutions_out.append({
                'generation': generation,
                'genome': current_best[0],
                'total_cost': current_cost
            })

        
        # Select parents based on fitness score for the population, reproductive success rate (which is really it's
        # inverse here) determines how many parents are selected from the total population.
        reproductive_success_rate = 2
        parents = selection(population_fitness, pop_size // reproductive_success_rate)
        
        # Crossover
        offspring = crossover(parents, crossover_rate)
        
        # Mutation
        offspring = mutation(offspring, mutation_rate)
        
        # Create new population with elitism (keep the best (pop_size / survival_rate) solution)
        survival_rate = 10
        elite_count = max(5,pop_size//survival_rate)
        elites = [e[0] for e in population_fitness[:elite_count]]
        population = elites + offspring[:(pop_size-elite_count)]

    return best_solutions, best_distance