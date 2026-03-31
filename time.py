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

                customers.append(Customer(id, x, y, demand, ready, due, service))

    return customers, nb_vehicles, capacity


def distance(c1, c2):
    return math.sqrt((c1.x - c2.x) ** 2 + (c1.y - c2.y) ** 2)


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



def initial_solution_urgent_random(customers, capacity, k=3):

    depot = 0
    unvisited = set(range(1, len(customers)))
    solution = []

    while unvisited:

        route = [depot]
        load = 0

        while True:

            feasible = []

            for i in unvisited:
                c = customers[i]

                if load + c.demand > capacity:
                    continue

                test_route = route + [i, depot]
                if check_time(test_route, customers):
                    feasible.append(i)

            if not feasible:
                break

            
            feasible.sort(key=lambda i: customers[i].due)

            top_k = feasible[:min(k, len(feasible))]

            chosen = random.choice(top_k)

            route.append(chosen)
            load += customers[chosen].demand
            unvisited.remove(chosen)

        route.append(depot)
        solution.append(route)

    return solution



def generate_population(customers, capacity, population_size):

    population = []

    for _ in range(population_size):
        sol = initial_solution_urgent_random(customers, capacity, k=3)
        population.append(sol)

    return population


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

    return total_cost

if __name__ == "__main__":

    filename = "R101.txt"

    customers, nb_vehicles, capacity = read_vrptw_file(filename)

    population = generate_population(customers, capacity, population_size=5)

    print("Population générée :", len(population))

    for i, sol in enumerate(population):
        print("\n===== Solution", i+1, "=====")
        print("Routes:", sol)

        nb_used = len(sol)
        total_distance = sum(
            distance(customers[r[i]], customers[r[i+1]])
            for r in sol
            for i in range(len(r)-1)
        )

        print("Nb véhicules utilisés :", nb_used)
        print("Distance totale :", round(total_distance, 2))
        print("Cost :", round(cost(sol, customers), 2))