import math
import random


class Customer:
    def __init__(self, id, x, y, demand, ready, due, service):
        self.id = id
        self.x = x
        self.y = y
        self.demand = demand
        self.ready = ready
        self.due = due
        self.service = service


def read_vrptw_file(filename):
    customers = []

    with open(filename, 'r') as f:
        lines = f.readlines()

    for i, line in enumerate(lines):
        if "NUMBER" in line and "CAPACITY" in line:
            parts = lines[i+1].split()
            nb_vehicles = int(parts[0])
            capacity = int(parts[1])
            break

    start = False

    for line in lines:
        if "CUST NO." in line:
            start = True
            continue

        if start:
            parts = line.split()
            if len(parts) == 7:
                id = int(parts[0])
                x = float(parts[1])
                y = float(parts[2])
                demand = int(parts[3])
                ready = int(parts[4])
                due = int(parts[5])
                service = int(parts[6])

                customers.append(
                    Customer(id, x, y, demand, ready, due, service)
                )

    return customers, nb_vehicles, capacity


def distance(c1, c2):
    return math.sqrt((c1.x - c2.x)**2 + (c1.y - c2.y)**2)


def check_time(route, customers):
    time = 0

    for i in range(len(route) - 1):
        c1 = customers[route[i]]
        c2 = customers[route[i + 1]]

        time += distance(c1, c2)

        if time < c2.ready:
            time = c2.ready

        if time > c2.due:
            return False

        time += c2.service

    return True


# --------------------------------------------------
# Random total method
# --------------------------------------------------
def initial_solution_random(customers, capacity):

    depot = 0
    unvisited = set(range(1, len(customers)))
    solution = []

    while unvisited:

        route = [depot]
        load = 0

        while True:

            feasible_clients = []

            for i in unvisited:
                c = customers[i]

                if load + c.demand > capacity:
                    continue

                test_route = route + [i, depot]
                if check_time(test_route, customers):
                    feasible_clients.append(i)

            if not feasible_clients:
                break

            chosen = random.choice(feasible_clients)

            route.append(chosen)
            load += customers[chosen].demand
            unvisited.remove(chosen)

        route.append(depot)
        solution.append(route)

    return solution


def generate_population(customers, capacity, population_size):

    population = []

    for _ in range(population_size):
        solution = initial_solution_random(customers, capacity)
        population.append(solution)

    return population


# --------------------------------------------------
# New cost function
# --------------------------------------------------
def cost(solution, customers, alpha=1000, beta=1):

    total_distance = 0

    for route in solution:
        for i in range(len(route) - 1):
            total_distance += distance(
                customers[route[i]],
                customers[route[i + 1]]
            )

    nb_vehicles = len(solution)

    total_cost = alpha * nb_vehicles + beta * total_distance

    return total_cost, nb_vehicles, total_distance


# --------------------------------------------------
# MAIN
# --------------------------------------------------
if __name__ == "__main__":

    filename = "R101.txt"

    customers, nb_vehicles, capacity = read_vrptw_file(filename)

    print("Max Vehicles available =", nb_vehicles)
    print("Capacity =", capacity)
    print("Nb clients =", len(customers))

    population = generate_population(customers, capacity, population_size=7)

    for i, sol in enumerate(population):
        print("\n===== Solution", i+1, "=====")

        total_cost, nb_used, total_distance = cost(sol, customers)

        print("Routes :", sol)
        print("Nb véhicules utilisés :", nb_used)
        print("Distance totale :", round(total_distance, 2))
        print("Cost pondéré :", round(total_cost, 2))