# Genetic Algorithm for Vehicle Routing Optimization
import random
from model.vehicle import Vehicle
from model.genome import Genome
random.seed("WGUPS")



# Initial population with constraints
# Constant time operation O(p) where p is population size (a constant)
def create_initial_population(pop_size, base_genome):
    population = []
    # Create the initial population
    for i in range(pop_size):
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
        genome.late_packages = []
        # Calculate distance for each truck's route
        for truck in genome.trucks:
            truck.mileage = 0.0
            truck.time = truck.depart_time
            truck.address = 0
            for idx, package_id in enumerate(truck.packages):
                #if the vehicle is empty it goes to the station to refill if there are more packages
                if idx % truck.capacity == 0 and idx != 0:
                    truck.mileage += d_matrix[truck.address][0]
                    truck.time += t_matrix[truck.address][0]
                    truck.address = 0

                #get package from the genome
                pkg = genome.packages.get(package_id)
                next_address = pkg.address

                #go to next address and deliver the package
                truck.mileage += d_matrix[truck.address][next_address]
                truck.time += t_matrix[truck.address][next_address]
                truck.address = next_address
                pkg.time_delivered = truck.time
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
        total_cost = total_mileage + len(genome.late_packages) * 20.0 + active_trucks * 100

        # Fitness is inversely proportional to total cost.
        fitness = 1.0 / (total_cost + 1.1)
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
        if i + 1 < len(parents):
            parent1 = parents[i]
            parent2 = parents[i + 1]

            if random.random() < crossover_rate:
                # Crossover point at the truck level
                cut = random.randint(1, len(parent1.trucks) - 1)

                # Create new truck lists
                trucks1 = []
                trucks2 = []

                for t in range(len(parent1.trucks)):
                    source1 = parent1.trucks[t] if t < cut else parent2.trucks[t]
                    source2 = parent2.trucks[t] if t < cut else parent1.trucks[t]

                    # Clone truck state (without linking the same object)
                    trucks1.append(Vehicle(source1.capacity, source1.speed, list(source1.packages), 0, 0, source1.depart_time))
                    trucks2.append(Vehicle(source2.capacity, source2.speed, list(source2.packages), 0, 0, source2.depart_time))

                # Create child genomes
                child1 = Genome(trucks1, parent1.packages)
                child2 = Genome(trucks2, parent2.packages)

                offspring.append(child1)
                offspring.append(child2)
            else:
                # No crossover, deep copy the parent genomes
                offspring.append(parent1.make_copy())
                offspring.append(parent2.make_copy())

    return offspring

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
def genetic_algorithm(truck_count, truck_capacity, truck_speed, packages, matrices, pop_size=50, generations=100, crossover_rate=0.9, mutation_rate=0.2,best_solutions_out=None):
    # Create initial population
    if best_solutions_out is None:
        best_solutions_out = []
    trucks = []
    for i in range(truck_count):
         trucks.append(Vehicle(truck_capacity, truck_speed, [], 0, 0))
    genome = Genome(trucks, packages)

    population = create_initial_population(pop_size, genome)
    
    best_solutions = []
    best_distance = float('inf')

    # Evolution process
    for generation in range(generations):

        # Evaluates fitness of the population members
        population_fitness = evaluate_fitness(population, matrices)
        
        # Store the best solution for the generation
        current_best = population_fitness[0]
        if current_best[2] < best_distance:
            best_solution = current_best[0]
            best_distance = current_best[2]
            # this print statement uses \r and an end="" to keep updating the text in place.
            print(f"\rGeneration {generation}: New best cost = {best_distance:.1f} miles (not including return leg).", end="")
            #stores every improving solution
            best_solutions_out.append({
                'generation': generation,
                'genome': current_best[0],
                'total_cost':current_best[2],
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
        survival_rate = 20
        elite_count = max(1,pop_size//survival_rate)
        elites = [e[0] for e in population_fitness[:elite_count]]
        population = elites + offspring[:(pop_size-elite_count)]

    return best_solutions, best_distance