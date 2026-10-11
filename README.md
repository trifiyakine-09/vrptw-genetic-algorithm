# 🚚 VRPTW Genetic Algorithm Solver

## 📌 Overview

This project implements a **Genetic Algorithm (GA)** to solve the **Vehicle Routing Problem with Time Windows (VRPTW)** using Solomon benchmark instances.

It provides:

* A **CLI version** (terminal execution)
* An **interactive Streamlit interface**
* Multiple genetic operators and configurations for experimentation

---

## ⚙️ Features

* ✔ Multiple selection methods:

  * Tournament
  * Roulette

* ✔ Multiple crossover operators:

  * OX (Order Crossover)
  * PMX (Partially Mapped Crossover)

* ✔ Multiple mutation operators:

  * Swap
  * Insertion
  * Inversion

* ✔ Feasibility checks:

  * Capacity constraints
  * Time window constraints

* ✔ Visualization:

  * Comparison table
  * Cost charts
  * Route maps (Streamlit)

---

## 📁 Project Structure

```
📦 VRPTW-GA
 ┣ 📄 final.py          # Core Genetic Algorithm (clean version)
 ┣ 📄 interface.py      # Streamlit interface
 ┣ 📄 README.md         # Project documentation
 ┣ 📄 instances/        # Solomon benchmark files (.txt)
 ┣ 📄 resultat.txt      # les resultats de l'execution  (.txt)
```

---

## 🚀 How to Run


1) Create virtual environment:
   python -m venv venv
2) Activate:
   Windows:
   venv\Scripts\activate
3) Install dependencies:
   pip install -r requirements.txt
4) Run the application:
   streamlit run app.py



## 🚀 Ou bien juste 
   double clique sur run.bat


👉 Then:

1. Upload a `.txt` Solomon instance
2. Set parameters:

   * Population size
   * Mutation rate
   * Time limit
3. Select combinations
4. Click **RUN**

---

## 📊 Input Format

The program uses **Solomon VRPTW instances** (`.txt` files).

Each file must contain:

* Number of vehicles
* Capacity
* Customer data (coordinates, demand, time windows, service time)

---

## 🧠 Algorithm Details

The Genetic Algorithm includes:

1. **Initial Population**

   * Multiple strategies (random, nearest, urgency, etc.)

2. **Selection**

   * Tournament (exploitation)
   * Roulette (exploration)

3. **Crossover**

   * OX: preserves order → best overall
   * PMX: useful in clustered instances

4. **Mutation**

   * Swap (best performance)
   * Insertion (moderate)
   * Inversion (most disruptive)

5. **Elitism + Diversity**

   * Best individuals preserved
   * Duplicate solutions avoided

---

## 📈 Output

### CLI Mode:

* Printed solutions
* Vehicles, distance, cost
* Best configuration

### Streamlit:

* Run log
* Comparison table
* Cost visualization
* Route map

---

## 🧪 Example

```bash
streamlit run interface.py
```

➡ Upload: `C101.txt`
➡ Run combinations
➡ View best solution directly

---

## 📌 Notes

* Results may vary due to randomness
* Use a fixed seed for reproducibility
* Best configuration (in most cases):

```
tournament + ox + swap
```

---

## 👨‍💻 Authors

* Trifi Yacine
* Tlili Malek
* Chibani Jasseur
* Khadhraoui Oussama

---

## 📚 References

* Solomon Benchmark (VRPTW)
* Genetic Algorithms for routing problems

---

## ✅ Status

✔ Fully functional
✔ CLI + UI available
✔ Ready for academic presentation

---
