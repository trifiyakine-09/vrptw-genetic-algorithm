"""
Solveur VRPTW (Vehicle Routing Problem with Time Windows) par algorithme
génétique, appliqué aux instances de Solomon.

Ce module contient le cœur de l'algorithme (lecture des instances,
faisabilité, coût, représentation chromosomique, initialisation, sélection,
croisement, mutation, boucle évolutive) ainsi qu'un CLI qui compare les
12 combinaisons d'opérateurs.

Utilisation en ligne de commande (depuis la racine du projet) :
    python src/core.py [--seed 42]
"""

import argparse
import math
import random
import copy
import sys
import time
import os

# Une route est une liste d'indices de clients encadrée par le dépôt (0),
# une solution est une liste de routes.
Route    = list[int]
Solution = list[Route]

# Chemins relatifs à la racine du projet (dossier parent de src/)
ROOT_DIR      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INSTANCES_DIR = os.path.join(ROOT_DIR, "instances")
RESULTS_DIR   = os.path.join(ROOT_DIR, "results")


# =============================================================================
# STRUCTURES DE BASE
# =============================================================================

class Customer:
    """Client (ou dépôt pour l'indice 0) d'une instance de Solomon."""

    def __init__(self, id, x, y, demand, ready, due, service):
        self.id      = id
        self.x       = x
        self.y       = y
        self.demand  = demand
        self.ready   = ready
        self.due     = due
        self.service = service
        self.dist    = []   # ligne de la matrice de distances (cf. build_distance_matrix)


def read_vrptw_file(filename: str) -> tuple[list[Customer], int, int]:
    """
    Lire une instance de Solomon depuis un fichier .txt.
    Retourne (clients, nombre de véhicules, capacité) ; le dépôt est
    l'élément d'indice 0 de la liste des clients.
    """
    customers = []

    with open(filename, 'r') as f:
        lines = f.readlines()

    for i, line in enumerate(lines):
        if "NUMBER" in line and "CAPACITY" in line:
            parts       = lines[i + 1].split()
            nb_vehicles = int(parts[0])
            capacity    = int(parts[1])
            break

    start = False
    for line in lines:
        if "CUST NO." in line:
            start = True
            continue
        if start:
            parts = line.split()
            if len(parts) == 7:
                customers.append(Customer(
                    id      = int(parts[0]),
                    x       = float(parts[1]),
                    y       = float(parts[2]),
                    demand  = int(parts[3]),
                    ready   = int(parts[4]),
                    due     = int(parts[5]),
                    service = int(parts[6]),
                ))

    build_distance_matrix(customers)
    return customers, nb_vehicles, capacity

def read_vrptw_content(content: str) -> tuple[list[Customer], int, int]:
    """
    Lire le fichier depuis une chaîne (pour Streamlit file_uploader).
    Même format de retour que read_vrptw_file.
    """
    customers = []
    lines = content.splitlines()

    for i, line in enumerate(lines):
        if "NUMBER" in line and "CAPACITY" in line:
            parts       = lines[i + 1].split()
            nb_vehicles = int(parts[0])
            capacity    = int(parts[1])
            break

    start = False
    for line in lines:
        if "CUST NO." in line:
            start = True
            continue
        if start:
            parts = line.split()
            if len(parts) == 7:
                customers.append(Customer(
                    id      = int(parts[0]),
                    x       = float(parts[1]),
                    y       = float(parts[2]),
                    demand  = int(parts[3]),
                    ready   = int(parts[4]),
                    due     = int(parts[5]),
                    service = int(parts[6]),
                ))

    build_distance_matrix(customers)
    return customers, nb_vehicles, capacity


def distance(c1: Customer, c2: Customer) -> float:
    """Distance euclidienne entre deux clients."""
    return math.sqrt((c1.x - c2.x) ** 2 + (c1.y - c2.y) ** 2)


def build_distance_matrix(customers: list[Customer]) -> list[list[float]]:
    """
    Précalculer la matrice n×n des distances, une seule fois après lecture
    de l'instance. La ligne i est rattachée au client i (customers[i].dist),
    ainsi customers[i].dist[j] == distance(customers[i], customers[j]).

    La matrice voyage avec la liste des clients : pas de variable globale,
    donc plusieurs sessions Streamlit sur des instances différentes ne se
    marchent pas dessus. Les valeurs sont calculées par distance() : elles
    sont identiques au bit près aux appels directs.
    """
    matrix = [[distance(c1, c2) for c2 in customers] for c1 in customers]
    for c, row in zip(customers, matrix):
        c.dist = row
    return matrix


# =============================================================================
# FAISABILITÉ
# =============================================================================

def check_time(route: Route, customers: list[Customer]) -> bool:
    """
    Vérifier les fenêtres de temps d'une route.
    Le temps de trajet vaut la distance ; on attend si on arrive avant
    l'ouverture (ready) et la route est invalide si on arrive après la
    fermeture (due).
    """
    time = 0
    for i in range(len(route) - 1):
        c1 = customers[route[i]]
        c2 = customers[route[i + 1]]
        time += c1.dist[route[i + 1]]
        if time < c2.ready:
            time = c2.ready
        if time > c2.due:
            return False
        time += c2.service
    return True


def check_capacity(route: Route, customers: list[Customer], capacity: int) -> bool:
    """Vérifier que la demande totale de la route ne dépasse pas la capacité."""
    load = sum(customers[i].demand for i in route if i != 0)
    return load <= capacity


def is_feasible(solution: Solution, customers: list[Customer], capacity: int) -> bool:
    """
    Vérifier qu'une solution est réalisable : capacité et fenêtres de temps
    respectées sur chaque route, et chaque client visité exactement une fois.
    """
    visited = []
    for route in solution:
        clients = [i for i in route if i != 0]
        visited.extend(clients)
        if not check_capacity(route, customers, capacity):
            return False
        if not check_time(route, customers):
            return False
    all_clients = set(range(1, len(customers)))
    if set(visited) != all_clients or len(visited) != len(all_clients):
        return False
    return True


# =============================================================================
# COÛT
# =============================================================================

def total_distance(solution: Solution, customers: list[Customer]) -> float:
    """Somme des distances parcourues sur toutes les routes de la solution."""
    dist = 0
    for route in solution:
        for i in range(len(route) - 1):
            dist += customers[route[i]].dist[route[i + 1]]
    return dist


def cost(solution: Solution, customers: list[Customer],
         alpha: float = 50, beta: float = 1) -> float:
    """
    Fonction objectif à minimiser :
    alpha × nombre de véhicules + beta × distance totale.
    """
    return alpha * len(solution) + beta * total_distance(solution, customers)


# =============================================================================
# REPRÉSENTATION : CHROMOSOME
# Un chromosome = liste plate de clients (sans dépôt)
# Exemple : [3, 1, 7, 2, 5, 4, 6, 8]
# On la décode en routes selon capacité + fenêtres de temps
# =============================================================================

def solution_to_chromosome(solution: Solution) -> list[int]:
    """Convertit une solution (liste de routes) en chromosome (liste plate)."""
    chrom = []
    for route in solution:
        for c in route:
            if c != 0:
                chrom.append(c)
    return chrom


def chromosome_to_solution(chrom: list[int], customers: list[Customer],
                           capacity: int) -> Solution:
    """
    Décode un chromosome en routes valides.
    Les clients sont ajoutés dans l'ordre à la route courante tant que la
    capacité et les fenêtres de temps le permettent ; sinon une nouvelle
    route est ouverte.
    """
    depot    = 0
    solution = []
    route    = [depot]
    load     = 0

    for cid in chrom:
        c      = customers[cid]
        test   = route + [cid, depot]

        if load + c.demand <= capacity and check_time(test, customers):
            route.append(cid)
            load += c.demand
        else:
            route.append(depot)
            solution.append(route)
            route = [depot, cid]
            load  = c.demand

    route.append(depot)
    solution.append(route)
    return solution


# =============================================================================
# INITIALISATION DE LA POPULATION
# =============================================================================

def init_urgency(customers: list[Customer], capacity: int, k: int = 5) -> Solution:
    """
    Construction gloutonne par urgence : à chaque étape, choisir au hasard
    parmi les k clients faisables dont la fin de fenêtre (due) est la plus
    proche. Une nouvelle route est ouverte quand plus aucun client n'est
    insérable.
    """
    depot     = 0
    unvisited = set(range(1, len(customers)))
    solution  = []

    while unvisited:
        route = [depot]
        load  = 0
        while True:
            feasible = [i for i in unvisited
                        if customers[i].demand + load <= capacity
                        and check_time(route + [i, depot], customers)]
            if not feasible:
                break
            feasible.sort(key=lambda i: customers[i].due)
            chosen = random.choice(feasible[:min(k, len(feasible))])
            route.append(chosen)
            load += customers[chosen].demand
            unvisited.remove(chosen)
        route.append(depot)
        solution.append(route)

    return solution


def init_nearest(customers: list[Customer], capacity: int, k: int = 5) -> Solution:
    """
    Construction gloutonne par plus proche voisin : choisir au hasard parmi
    les k clients faisables les plus proches du dernier client de la route.
    """
    depot     = 0
    unvisited = set(range(1, len(customers)))
    solution  = []

    while unvisited:
        route = [depot]
        load  = 0

        while True:
            last = route[-1]

            feasible = [i for i in unvisited
                        if customers[i].demand + load <= capacity
                        and check_time(route + [i, depot], customers)]

            if not feasible:
                break

            # 🔥 tri par distance
            feasible.sort(key=lambda i: customers[last].dist[i])

            # 🔥 choix aléatoire parmi les k plus proches
            chosen = random.choice(feasible[:min(k, len(feasible))])

            route.append(chosen)
            load += customers[chosen].demand
            unvisited.remove(chosen)

        route.append(depot)
        solution.append(route)

    return solution


def init_farthest(customers: list[Customer], capacity: int, k: int = 5) -> Solution:
    """
    Construction gloutonne par éloignement : choisir au hasard parmi les k
    clients faisables les plus éloignés du dépôt.
    """
    depot     = 0
    unvisited = set(range(1, len(customers)))
    solution  = []

    while unvisited:
        route = [depot]
        load  = 0

        while True:
            feasible = [i for i in unvisited
                        if customers[i].demand + load <= capacity
                        and check_time(route + [i, depot], customers)]

            if not feasible:
                break

            # 🔥 tri décroissant
            feasible.sort(key=lambda i: -customers[depot].dist[i])

            # 🔥 choix aléatoire parmi les k plus éloignés
            chosen = random.choice(feasible[:min(k, len(feasible))])

            route.append(chosen)
            load += customers[chosen].demand
            unvisited.remove(chosen)

        route.append(depot)
        solution.append(route)

    return solution


def init_random(customers: list[Customer], capacity: int) -> Solution:
    """Construction aléatoire : choisir un client faisable au hasard."""
    depot     = 0
    unvisited = set(range(1, len(customers)))
    solution  = []

    while unvisited:
        route = [depot]
        load  = 0
        while True:
            feasible = [i for i in unvisited
                        if customers[i].demand + load <= capacity
                        and check_time(route + [i, depot], customers)]
            if not feasible:
                break
            chosen = random.choice(feasible)
            route.append(chosen)
            load += customers[chosen].demand
            unvisited.remove(chosen)
        route.append(depot)
        solution.append(route)

    return solution


def generate_population(customers: list[Customer], capacity: int,
                        population_size: int) -> list[Solution]:
    """
    Mélange des 4 méthodes :
      30% Urgence | 25% Nearest | 25% Farthest | 20% Aléatoire
    Seules les solutions faisables sont conservées, puis la population est
    mélangée.
    """
    n_urgency  = int(population_size * 0.30)
    n_nearest  = int(population_size * 0.25)
    n_farthest = int(population_size * 0.25)
    n_random   = population_size - n_urgency - n_nearest - n_farthest

    population = []

    for _ in range(n_urgency):
        sol = init_urgency(customers, capacity)
        if is_feasible(sol, customers, capacity):
            population.append(copy.deepcopy(sol))

    for _ in range(n_nearest):
        sol = init_nearest(customers, capacity)
        if is_feasible(sol, customers, capacity):
            population.append(copy.deepcopy(sol))

    for _ in range(n_farthest):
        sol = init_farthest(customers, capacity)
        if is_feasible(sol, customers, capacity):
            population.append(copy.deepcopy(sol))

    for _ in range(n_random):
        sol = init_random(customers, capacity)
        if is_feasible(sol, customers, capacity):
            population.append(copy.deepcopy(sol))

    random.shuffle(population)
    return population


# =============================================================================
# SÉLECTION
# =============================================================================

def tournament_selection(population: list[Solution], customers: list[Customer],
                         k: int = 2) -> Solution:
    """
    Tournoi : choisir k individus au hasard, retourner le meilleur.
    """
    participants = random.sample(population, min(k, len(population)))
    best = min(participants, key=lambda sol: cost(sol, customers))
    return copy.deepcopy(best)


def roulette_selection(population: list[Solution], customers: list[Customer]) -> Solution:
    """
    Roulette : probabilité proportionnelle à la fitness inversée
    (les meilleures solutions ont plus de chances d'être choisies).
    """
    costs      = [cost(sol, customers) for sol in population]
    max_cost   = max(costs)
    weights    = [max_cost - c + 1e-6 for c in costs]
    total      = sum(weights)
    r          = random.uniform(0, total)
    cumulative = 0
    for sol, w in zip(population, weights):
        cumulative += w
        if cumulative >= r:
            return copy.deepcopy(sol)
    return copy.deepcopy(population[-1])


# =============================================================================
# CROISEMENT (CROSSOVER)
# =============================================================================

def ox_crossover(parent1: Solution, parent2: Solution,
                 customers: list[Customer], capacity: int) -> Solution:
    """
    Order Crossover (OX) :
    1. Prendre un segment du parent1
    2. Compléter avec les clients manquants dans l'ordre du parent2
    3. Décoder en routes valides + vérifier faisabilité
    """
    seq1 = solution_to_chromosome(parent1)
    seq2 = solution_to_chromosome(parent2)
    n    = len(seq1)

    i, j = sorted(random.sample(range(n), 2))

    child   = [None] * n
    child[i:j + 1] = seq1[i:j + 1]
    segment = set(seq1[i:j + 1])

    fill = [c for c in seq2 if c not in segment]
    pos  = 0
    for k in range(n):
        if child[k] is None:
            child[k] = fill[pos]
            pos += 1

    solution = chromosome_to_solution(child, customers, capacity)

    # ✓ Vérification faisabilité après croisement
    if is_feasible(solution, customers, capacity):
        return solution
    return copy.deepcopy(random.choice([parent1, parent2]))  # fallback : retourner le parent


def pmx_crossover(parent1: Solution, parent2: Solution,
                  customers: list[Customer], capacity: int) -> Solution:
    """
    Partially Mapped Crossover (PMX) :
    1. Copier un segment du parent1
    2. Suivre la chaîne de mapping pour les positions restantes
    3. Décoder en routes valides + vérifier faisabilité
    """
    seq1 = solution_to_chromosome(parent1)
    seq2 = solution_to_chromosome(parent2)
    n    = len(seq1)

    i, j = sorted(random.sample(range(n), 2))

    child       = [None] * n
    child[i:j + 1] = seq1[i:j + 1]
    segment_set = set(seq1[i:j + 1])
    seg1        = seq1[i:j + 1]
    seg2        = seq2[i:j + 1]

    for k in list(range(0, i)) + list(range(j + 1, n)):
        val      = seq2[k]
        max_iter = n
        while val in segment_set and max_iter > 0:
            idx  = seg1.index(val)
            val  = seg2[idx]
            max_iter -= 1
        child[k] = val

    # Corriger les éventuels doublons ou None
    all_clients = set(range(1, len(customers)))
    present     = set(x for x in child if x is not None)
    missing     = list(all_clients - present)
    random.shuffle(missing)
    m = 0
    for k in range(n):
        if child[k] is None and m < len(missing):
            child[k] = missing[m]
            m += 1

    solution = chromosome_to_solution(child, customers, capacity)

    # ✓ Vérification faisabilité après croisement

    if is_feasible(solution, customers, capacity):
        return solution

    return copy.deepcopy(random.choice([parent1, parent2]))
    #return chromosome_to_solution(random.sample(seq1, len(seq1)), customers, capacity)


# =============================================================================
# MUTATION
# =============================================================================

def swap_mutation(solution: Solution, customers: list[Customer], capacity: int) -> Solution:
    """
    Swap : échanger deux clients aléatoires dans le chromosome.
    """
    chrom    = solution_to_chromosome(solution)
    i, j     = random.sample(range(len(chrom)), 2)
    chrom[i], chrom[j] = chrom[j], chrom[i]

    new_sol = chromosome_to_solution(chrom, customers, capacity)

    # ✓ Vérification faisabilité après mutation
    if is_feasible(new_sol, customers, capacity):
        return new_sol
    return solution


def insertion_mutation(solution: Solution, customers: list[Customer], capacity: int) -> Solution:
    """
    Insertion : retirer un client et le réinsérer à la meilleure position.
    Recommandé pour le VRPTW.
    """
    chrom  = solution_to_chromosome(solution)
    idx    = random.randint(0, len(chrom) - 1)
    client = chrom.pop(idx)

    best_pos  = None
    best_cost = float('inf')

    for pos in range(len(chrom) + 1):
        candidate = chrom[:pos] + [client] + chrom[pos:]
        new_sol   = chromosome_to_solution(candidate, customers, capacity)
        if is_feasible(new_sol, customers, capacity):
            c = cost(new_sol, customers)
            if c < best_cost:
                best_cost = c
                best_pos  = pos

    if best_pos is not None:
        new_chrom = chrom[:best_pos] + [client] + chrom[best_pos:]
        return chromosome_to_solution(new_chrom, customers, capacity)

    # Aucune position valide → remettre à la place originale
    chrom.insert(idx, client)
    return chromosome_to_solution(chrom, customers, capacity)


def inversion_mutation(solution: Solution, customers: list[Customer], capacity: int) -> Solution:
    """
    Inversion : inverser un sous-segment aléatoire du chromosome.
    """
    chrom          = solution_to_chromosome(solution)
    i, j           = sorted(random.sample(range(len(chrom)), 2))
    chrom[i:j + 1] = chrom[i:j + 1][::-1]

    new_sol = chromosome_to_solution(chrom, customers, capacity)

    # ✓ Vérification faisabilité après mutation
    if is_feasible(new_sol, customers, capacity):
        return new_sol
    return solution


# =============================================================================
# ALGORITHME GÉNÉTIQUE
# =============================================================================

# =============================================================================
# BOUCLE GA (À PARTIR D'UNE POPULATION EXISTANTE)
# Utilisée par l'interface Streamlit après génération et affichage de la pop.
# =============================================================================

def run_ga_from_population(population: list[Solution], customers: list[Customer],
                           capacity: int,
                           selection_method: str, crossover_method: str,
                           mutation_method: str,
                           mutation_rate: float,
                           time_limit: float) -> tuple[list[Solution], Solution]:
    """
    Lance la boucle évolutive sur une population déjà générée.
    Retourne (population_finale, meilleure_solution).

    selection_method : 'tournament' | 'roulette'
    crossover_method : 'ox' | 'pmx'
    mutation_method  : 'swap' | 'insertion' | 'inversion'
    time_limit       : budget en secondes (critère d'arrêt unique)

    À chaque génération : remplacement élitiste avec déduplication, puis
    injection de 2 nouvelles solutions après 10 générations sans amélioration.
    """
    population_size = len(population)
    best_sol        = min(population, key=lambda s: cost(s, customers))
    best_cost       = cost(best_sol, customers)
    stagnation      = 0
    start           = time.time()

    while True:
        if time.time() - start >= time_limit:
            break

        new_population = []

        for _ in range(population_size):
            if time.time() - start >= time_limit:
                break

            # Sélection
            if selection_method == 'tournament':
                parent1 = tournament_selection(population, customers)
                parent2 = tournament_selection(population, customers)
            else:
                parent1 = roulette_selection(population, customers)
                parent2 = roulette_selection(population, customers)

            # Croisement
            if crossover_method == 'ox':
                child = ox_crossover(parent1, parent2, customers, capacity)
            else:
                child = pmx_crossover(parent1, parent2, customers, capacity)

            # Mutation
            if random.random() < mutation_rate:
                if mutation_method == 'swap':
                    child = swap_mutation(child, customers, capacity)
                elif mutation_method == 'insertion':
                    child = insertion_mutation(child, customers, capacity)
                else:
                    child = inversion_mutation(child, customers, capacity)

            if is_feasible(child, customers, capacity):
                new_population.append(child)
            else:
                new_population.append(copy.deepcopy(random.choice(population)))

        # Remplacement élitiste avec déduplication
        combined = sorted(population + new_population, key=lambda s: cost(s, customers))
        new_pop  = []
        seen     = set()
        for sol in combined:
            key = tuple(solution_to_chromosome(sol))
            if key not in seen:
                new_pop.append(sol)
                seen.add(key)
            if len(new_pop) == population_size:
                break

        if len(new_pop) < population_size:
            random.shuffle(combined)
            for sol in combined:
                if sol not in new_pop:
                    new_pop.append(sol)
                if len(new_pop) == population_size:
                    break

        population = new_pop

        current_best = population[0]
        current_cost = cost(current_best, customers)

        if current_cost < best_cost:
            best_sol   = copy.deepcopy(current_best)
            best_cost  = current_cost
            stagnation = 0
        else:
            stagnation += 1

        if stagnation >= 10:
            # 🔥 injection de nouvelles solutions pour relancer la diversité
            population += generate_population(customers, capacity, 2)
            population  = sorted(population, key=lambda s: cost(s, customers))[:population_size]
            stagnation  = 0

    return population, best_sol


# =============================================================================
# ALGORITHME GÉNÉTIQUE COMPLET (CLI)
# =============================================================================

def genetic_algorithm(customers: list[Customer], capacity: int,
                      population_size: int  = 20,
                      selection_method: str = 'tournament',
                      crossover_method: str = 'ox',
                      mutation_method: str  = 'insertion',
                      mutation_rate: float  = 0.3,
                      time_limit: float     = 10) -> tuple[list[Solution], Solution]:
    """
    Algorithme génétique complet : génère la population initiale puis lance
    run_ga_from_population. Retourne (population_finale, meilleure_solution).
    """
    population = generate_population(customers, capacity, population_size)
    population, best_sol = run_ga_from_population(
        population, customers, capacity,
        selection_method, crossover_method, mutation_method,
        mutation_rate, time_limit
    )
    return population, best_sol

def afficher_population(population: list[Solution], customers: list[Customer],
                        capacity: int, f=None) -> None:
    """
    Afficher chaque solution de la population (routes, nombre de véhicules,
    distance, coût) dans le terminal, et dans le fichier f s'il est fourni.
    """
    output = f"\nPopulation generee : {len(population)}\n"

    for i, sol in enumerate(population):
        nb_v = len(sol)
        dist = round(total_distance(sol, customers), 2)
        c    = round(cost(sol, customers), 2)

        output += f"===== Solution {i+1} =====\n"
        output += f"Routes: {sol}\n"
        output += f"Nb vehicules utilises : {nb_v}\n"
        output += f"Distance totale : {dist}\n"
        output += f"Cost : {c}\n\n"

    print(output) # Affiche dans le terminal
    if f:
        f.write(output) # Ecrit dans le fichier si fourni

# =============================================================================
# MAIN — TESTER TOUTES LES COMBINAISONS
# =============================================================================

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Compare les combinaisons d'opérateurs du GA sur une instance de Solomon.")
    parser.add_argument("--seed", type=int, default=42,
                        help="graine aléatoire pour la reproductibilité (défaut : 42)")
    args = parser.parse_args()
    random.seed(args.seed)

    print("\n===== CONFIGURATION DE L'ALGORITHME =====\n")

    print(" Paramètres :")
    print("1. Population size : nombre de solutions dans chaque génération")
    print("3. Mode temps : arrêter après X secondes (global)")
    print("4. Mutation rate : probabilité de modification des solutions\n")

    filename = input(" Nom du fichier (ex: R101.txt) : ")
    filepath = os.path.join(INSTANCES_DIR, filename)
    customers, nb_vehicles, capacity = read_vrptw_file(filepath)

    print(f"\nDataset : {len(customers)-1} clients | capacité = {capacity}\n")

    # ── PARAMÈTRES ─────────────────────────────────────────
    population_size = int(input(" Population size : "))

    TIME_LIMIT = float(input("Temps d'execution (secondes) : "))

    mutation_rate = float(input(" Mutation rate (ex: 0.6) : "))

    print("\n Sélection : tournament = rapide | roulette = plus diversifié")
    print(" Croisement : ox | pmx")
    print(" Mutation : swap | insertion | inversion\n")

    # ── CHOIX DES COMBINAISONS ─────────────────────────────
    combinations = [
        ('tournament', 'ox',  'swap'),
        ('tournament', 'ox',  'insertion'),
        ('tournament', 'ox',  'inversion'),
        ('tournament', 'pmx', 'swap'),
        ('tournament', 'pmx', 'insertion'),
        ('tournament', 'pmx', 'inversion'),
        ('roulette',   'ox',  'swap'),
        ('roulette',   'ox',  'insertion'),
        ('roulette',   'ox',  'inversion'),
        ('roulette',   'pmx', 'swap'),
        ('roulette',   'pmx', 'insertion'),
        ('roulette',   'pmx', 'inversion'),
    ]

    selected_combinations = []

    print("\n===== CHOIX DES COMBINAISONS =====")
    f = open(os.path.join(RESULTS_DIR, "resultat.txt"), "w", encoding="utf-8")

# classe pour écrire dans terminal + fichier
    class Tee:
        """Flux qui duplique chaque écriture vers plusieurs fichiers."""
        def __init__(self, *files):
            self.files = files
        def write(self, obj):
            for file in self.files:
                file.write(obj)
        def flush(self):
            for file in self.files:
                file.flush()

    # redirection
    sys.stdout = Tee(sys.stdout, f)

    for sel, cross, mut in combinations:
        config = f"{sel} + {cross} + {mut}"
        choix = input(f"Tester {config} ? (oui/non) : ").strip().lower()

        if choix == "oui":
            selected_combinations.append((sel, cross, mut))
        print(f"Nombre de combinaisons à tester : {len(selected_combinations)}")

    # ── EXÉCUTION ──────────────────────────────────────────
    print("\n===== EXECUTION =====\n")

    start_global = time.time()
    results = []

    for sel, cross, mut in selected_combinations:
        config = f"{sel} + {cross} + {mut}"
        print(f"\n-- {config} ...")
        remaining_time = TIME_LIMIT - (time.time() - start_global)

        if remaining_time <= 0:
            print("Temps global atteint !")
            break
        n_restantes = len(selected_combinations) - len(results)
        time_per_config = remaining_time / max(n_restantes, 1)
        population, best = genetic_algorithm(
            customers, capacity,
            population_size  = population_size,
            selection_method = sel,
            crossover_method = cross,
            mutation_method  = mut,
            mutation_rate    = mutation_rate,

            time_limit = time_per_config
        )

        afficher_population(population, customers, capacity)

        nb_v   = len(best)
        dist   = round(total_distance(best, customers), 2)
        c      = round(cost(best, customers), 2)
        valid  = is_feasible(best, customers, capacity)

        results.append((config, nb_v, dist, c, valid))

        print(f"Vehicules : {nb_v} | Distance : {dist} | Cout : {c} | Faisable : {'ok' if valid else 'no'}")

    # ── RÉSULTATS ──────────────────────────────────────────
    elapsed = time.time() - start_global
    print("\n" + "=" * 75)
    print(f"{'Configuration':<35} {'Veh.':<8} {'Distance':<14} {'Cout':<14} {'OK'}")
    print("-" * 75)

    results.sort(key=lambda x: x[3])

    for rank, (config, nb_v, dist, c, valid) in enumerate(results, 1):
        mark = "champion" if rank == 1 else ""
        print(f"{config:<35} {nb_v:<8} {dist:<14} {c:<14} {'ok' if valid else 'no'} {mark}")

    print("=" * 75)

    if results:
        print(f"\n Meilleure configuration : {results[0][0]}")

    print(f"Temps execution : {round(elapsed,2)} sec")
    f.close()