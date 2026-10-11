# 🚚 VRPTW Genetic Algorithm Solver

A **Genetic Algorithm (GA)** for the **Vehicle Routing Problem with Time Windows (VRPTW)**, evaluated on the Solomon benchmark instances.

The project provides:

- a **command-line interface** that compares the 12 combinations of genetic operators on one instance;
- an interactive **Streamlit interface** with a live run log, a comparison table, a cost chart and a route map.

---

## Table of contents

- [Problem](#problem)
- [Algorithm](#algorithm)
- [Project structure](#project-structure)
- [Installation](#installation)
- [Usage](#usage)
- [Reproducibility](#reproducibility)
- [Recorded results](#recorded-results)
- [Input format](#input-format)
- [Author](#author)

---

## Problem

A fleet of vehicles with identical capacity, starting and ending at a single depot, must serve every customer exactly once. Each customer has a demand, a service time and a time window `[ready, due]`. A vehicle that arrives early waits until `ready`; arriving after `due` makes the route infeasible.

The objective minimised by the solver (`cost` in `src/core.py`) is:

```text
cost = 50 × (number of vehicles) + 1 × (total distance)
```

Travel time between two customers equals their Euclidean distance.

## Algorithm

| Step | Implementation |
|---|---|
| **Representation** | A chromosome is a flat permutation of customers (depot excluded). It is decoded greedily into routes: a customer is appended to the current route while capacity and time windows allow it, otherwise a new route is opened. |
| **Initial population** | Mix of four randomised constructive heuristics: 30 % *urgency* (earliest due date), 25 % *nearest neighbour*, 25 % *farthest from depot*, 20 % *random*. The three greedy ones pick at random among the 5 best candidates. Only feasible solutions are kept. |
| **Selection** | Tournament (size 2) or roulette wheel (weight = `max_cost − cost`). |
| **Crossover** | OX (Order Crossover) or PMX (Partially Mapped Crossover) on the chromosome. If the child is infeasible, a parent is returned instead. |
| **Mutation** | Swap (two customers), insertion (one customer moved to its best feasible position) or inversion (segment reversed). Applied with probability `mutation_rate`. |
| **Replacement** | Elitist: parents and children are merged, sorted by cost, and the best *distinct* solutions are kept. |
| **Diversity** | After 10 generations without improvement, 2 newly generated solutions are injected. |
| **Stopping criterion** | Time limit only. The global budget is shared equally among the combinations still to be run. |

The 12 tested combinations are every pairing of {tournament, roulette} × {OX, PMX} × {swap, insertion, inversion}.

**Performance note.** Distances are precomputed once per instance into an n×n matrix (`build_distance_matrix`). This was verified to produce bit-identical results to the original on-the-fly computation.

## Project structure

```text
VRPTW-GA/
├── src/
│   ├── core.py          # GA (all operators) + CLI comparing the 12 combinations
│   └── interface.py     # Streamlit interface (imports core.py)
├── instances/           # Solomon benchmark instances (C1, C2, R1, R2, RC1, RC2)
├── results/
│   └── resultat.txt     # Output of a full CLI run (see "Recorded results")
├── docs/
│   └── ameliorations-proposees.md   # Known limitations and proposed improvements
├── requirements.txt
├── run.bat              # Windows one-click launcher for the Streamlit app
└── README.md
```

## Installation

Requirements: Python 3.11 or newer (pandas 3 needs it; the project was run with Python 3.12).

```bash
git clone <repository-url>
cd VRPTW-GA
python -m venv venv
```

Activate the virtual environment:

```bash
# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

`core.py` itself uses only the Python standard library. The dependencies (`streamlit`, `pandas`, `plotly`) are needed only for the interface.

## Usage

All commands are run from the project root.

### Streamlit interface

```bash
streamlit run src/interface.py
```

On Windows you can also double-click **`run.bat`**. It creates the virtual environment if needed, installs the dependencies and starts the app.

Then, in the browser:

1. Upload a Solomon `.txt` instance (for example `instances/C101.txt`).
2. Set the population size, time limit, mutation rate and random seed.
3. Tick the combinations to compare.
4. Click **RUN GENETIC ALGORITHM**.

The *Run Log* tab shows the initial population and a summary per combination. *Comparison Table* ranks the combinations by cost. *Route Map* draws the best solution of the selected combination.

### Command line

```bash
python src/core.py              # random seed 42 (default)
python src/core.py --seed 7     # another seed
```

The CLI interactively asks for:

- the instance file name, looked up in `instances/` (e.g. `R101.txt`);
- the population size;
- the **global** time budget in seconds;
- the mutation rate;
- for each of the 12 combinations, whether to test it (`oui` / `non`).

For each combination, it prints the final population and the best solution (vehicles, distance, cost, feasibility). It ends with a table ranked by cost. Everything printed after the combination choice is also written to `results/resultat.txt`. **That file is overwritten on every run.**

## Reproducibility

Both the CLI (`--seed`, default `42`) and the interface (*Random Seed* field, default `42`) seed Python's `random` module before running.

Because the GA stops on a **wall-clock time limit**, the number of generations depends on the speed and load of the machine. A fixed seed therefore reproduces the initial populations, but not necessarily the final results across machines or runs. See `docs/ameliorations-proposees.md` (point A1).

## Recorded results

`results/resultat.txt` holds the output of one CLI run: all 12 combinations, population size 20, total execution time 120.42 s. The instance and mutation rate used are not recorded in the file. Ranking (lower cost is better):

| Rank | Configuration | Vehicles | Distance | Cost |
|---:|---|---:|---:|---:|
| 1 | tournament + ox + swap | 26 | 2411.53 | 3711.53 |
| 2 | tournament + pmx + swap | 28 | 2461.98 | 3861.98 |
| 3 | roulette + pmx + swap | 27 | 2558.47 | 3908.47 |
| 4 | tournament + ox + insertion | 27 | 2566.69 | 3916.69 |
| 5 | roulette + ox + insertion | 26 | 2632.20 | 3932.20 |
| 6 | tournament + ox + inversion | 26 | 2652.92 | 3952.92 |
| 7 | roulette + ox + inversion | 27 | 2616.45 | 3966.45 |
| 8 | tournament + pmx + insertion | 29 | 2615.72 | 4065.72 |
| 9 | roulette + pmx + insertion | 28 | 2699.90 | 4099.90 |
| 10 | tournament + pmx + inversion | 29 | 2686.53 | 4136.53 |
| 11 | roulette + ox + swap | 28 | 2787.88 | 4187.88 |
| 12 | roulette + pmx + inversion | 30 | 2878.26 | 4378.26 |

All 12 best solutions were reported feasible. This is a **single run** on a single instance. It illustrates the output format and does not support general conclusions about which operators perform best.

## Input format

Standard Solomon VRPTW text files:

```text
C101

VEHICLE
NUMBER     CAPACITY
  25         200

CUSTOMER
CUST NO.  XCOORD.   YCOORD.    DEMAND   READY TIME  DUE DATE   SERVICE   TIME

    0      40         50          0          0       1236          0
    1      45         68         10        912        967         90
  ...
```

The line after `NUMBER CAPACITY` gives the number of vehicles and their capacity. Every 7-column line after `CUST NO.` is a customer. Customer `0` is the depot.

## Author

- **Trifi Yakine**

## References

- M. M. Solomon (1987), *Algorithms for the Vehicle Routing and Scheduling Problems with Time Window Constraints*, Operations Research 35(2) — origin of the benchmark instances.
