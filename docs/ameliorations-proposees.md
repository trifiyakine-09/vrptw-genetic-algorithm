# Améliorations proposées (non implémentées)

Ce document liste les points repérés pendant le nettoyage du dépôt et
**volontairement laissés tels quels**, soit parce qu'ils touchent au
comportement de l'algorithme génétique, soit parce qu'ils sortaient du
périmètre du nettoyage. Pour chaque point : le problème, son impact et une
piste de correction.

La seule optimisation appliquée est la matrice de distances précalculée
(`build_distance_matrix`). Sa non-régression a été vérifiée : les résultats
sont identiques au bit près à graine fixée.

---

## A. Algorithme génétique

### A1. Le seul critère d'arrêt est le temps réel
- **Problème** : `run_ga_from_population` s'arrête quand `time.time() - start >= time_limit`.
  Le nombre de générations dépend donc de la vitesse de la machine et de sa charge.
- **Impact** : la graine (`--seed` / « Random Seed ») ne suffit pas à reproduire
  un résultat. Deux exécutions avec la même graine sur deux machines, ou sur la
  même machine plus ou moins chargée, donnent des solutions différentes. Toute
  optimisation de performance change aussi les résultats, puisqu'elle augmente
  le nombre de générations. Pour prouver la non-régression de la matrice de
  distances, il a fallu remplacer `time.time` par une horloge simulée dans un
  harnais externe.
- **Correction** : ajouter un paramètre optionnel `max_generations` (ou un
  nombre maximal d'évaluations) utilisé à la place du temps, ou en plus de
  lui. Avec une graine et un nombre de générations fixés, le résultat devient
  reproductible partout.

### A2. La réinjection après stagnation n'injecte que des solutions aléatoires
- **Problème** : après 10 générations sans amélioration, on appelle
  `generate_population(customers, capacity, 2)`. Pour une taille de 2, les
  proportions 30/25/25/20 donnent `int(0.6) = 0` urgence, `int(0.5) = 0`
  nearest, `int(0.5) = 0` farthest, et donc **2 solutions `init_random`**.
- **Impact** : les solutions aléatoires sont en général bien moins bonnes que
  la population en place. Comme la population est ensuite triée par coût puis
  tronquée à `population_size`, elles sont vraisemblablement éliminées
  aussitôt, et la réinjection ne diversifie presque rien.
- **Correction** : réinjecter des solutions issues des heuristiques gloutonnes
  (urgence, nearest, farthest), ou insérer les nouvelles solutions en
  remplaçant les pires individus *sans* retrier, ou encore remplacer une
  fraction plus importante de la population (par exemple 20 %).

### A3. La vérification de faisabilité après décodage est (presque) toujours vraie
- **Problème** : `chromosome_to_solution` ouvre une nouvelle route dès qu'un
  client viole la capacité ou les fenêtres de temps. Chaque route produite
  respecte donc déjà les contraintes, et tous les clients du chromosome sont
  placés. Les appels à `is_feasible` qui suivent le décodage (dans
  `ox_crossover`, `pmx_crossover`, `swap_mutation`, `inversion_mutation`,
  `insertion_mutation` et dans la boucle GA) ne peuvent échouer que si un
  client est infaisable *seul* (route `[0, c, 0]`), ce qui n'arrive pas sur
  les instances de Solomon.
- **Impact** : des calculs redondants à chaque enfant. Les branches de repli
  (« retourner un parent ») sont du code mort en pratique.
- **Correction** : garder une seule vérification, par exemple en mode debug
  (`assert`), et traiter explicitement le cas d'un client infaisable seul
  (voir A4).

### A4. Route vide possible dans le décodeur
- **Problème** : dans `chromosome_to_solution`, si le premier client du
  chromosome ne passe pas le test (capacité ou fenêtre de temps), la route
  courante `[0]` est fermée en `[0, 0]` et ajoutée à la solution.
- **Impact** : une route vide compte comme un véhicule dans `cost`
  (+ `alpha`). Le cas ne se produit pas sur des instances bien formées, mais
  le décodeur n'est pas robuste.
- **Correction** : n'ajouter la route courante que si elle contient au moins
  un client (`len(route) > 1`).

### A5. Le coût est recalculé en permanence
- **Problème** : `cost()` (donc `total_distance`) est réévalué à chaque
  comparaison : tri de `combined`, `min` du tournoi, `roulette_selection`
  (qui recalcule le coût de **toute** la population à chaque tirage, soit
  O(taille²) évaluations par génération), tri après réinjection.
- **Impact** : une part importante du temps de calcul, donc moins de
  générations dans le budget de temps.
- **Correction** : stocker le coût avec chaque individu (tuple
  `(coût, solution)` ou petit objet), calculé une seule fois à sa création ;
  pour la roulette, calculer les poids une fois par génération.

### A6. `insertion_mutation` décode le chromosome complet pour chaque position
- **Problème** : pour un client retiré, on teste les `n` positions, et chaque
  test fait un `chromosome_to_solution` complet, puis `is_feasible` et `cost`.
  Cela fait environ O(n²) vérifications de fenêtres de temps par mutation.
- **Impact** : c'est l'opérateur de loin le plus coûteux. À budget de temps
  égal, les combinaisons « insertion » font beaucoup moins de générations que
  les autres, ce qui biaise la comparaison des 12 combinaisons.
- **Correction** : évaluer l'insertion de façon incrémentale (coût de
  l'insertion entre deux clients consécutifs, et faisabilité temporelle
  calculée avec les temps d'arrivée au plus tôt et les marges des clients
  suivants), sans redécoder tout le chromosome.

### A7. Vérification de fenêtres de temps non incrémentale dans les initialisations
- **Problème** : les quatre `init_*` testent chaque candidat avec
  `check_time(route + [i, depot], customers)`, ce qui recopie la route et la
  reparcourt depuis le dépôt.
- **Impact** : coût en O(longueur de route) par candidat, et allocation d'une
  liste à chaque test. Cela pèse aussi sur chaque réinjection.
- **Correction** : mémoriser l'heure de départ du dernier client de la route.
  Le test d'un candidat ne demande alors que deux comparaisons (arrivée chez
  `i`, puis retour au dépôt).

### A8. Pression de sélection peu réglable
- **Problème** : le tournoi est figé à `k=2`. La roulette utilise les poids
  `max_cost - c + 1e-6` : le pire individu a une probabilité quasi nulle, et la
  pression dépend fortement de l'écart des coûts (un véhicule de plus = +50).
- **Impact** : il est difficile de comparer équitablement tournoi et roulette,
  car leur pression de sélection n'est pas maîtrisée.
- **Correction** : exposer `k` en paramètre ; pour la roulette, utiliser une
  sélection par rang (*rank-based*) ou une mise à l'échelle de la fitness.

### A9. Objectif pondéré plutôt que hiérarchique
- **Problème** : `cost = 50 × véhicules + distance`. Dans la littérature sur
  les instances de Solomon, on minimise habituellement d'abord le nombre de
  véhicules, puis la distance (objectif hiérarchique).
- **Impact** : une solution avec un véhicule de plus mais 51 unités de
  distance en moins est jugée meilleure. Les résultats ne sont donc pas
  directement comparables aux meilleures solutions connues publiées.
- **Correction** : comparer les solutions sur le tuple
  `(len(solution), total_distance(...))`, ou exposer `alpha` et `beta` en
  paramètres et documenter le choix.

### A10. Budget de temps : le CLI et l'interface ne comptent pas la même chose
- **Problème** : dans l'interface, la génération de la population initiale
  est déduite du budget (`ga_time = time_per_config - elapsed_gen`). Dans le
  CLI, `genetic_algorithm` reçoit `time_per_config` en entier pour la seule
  boucle évolutive, et la génération de la population s'y ajoute.
- **Impact** : le CLI dépasse le temps global demandé (par exemple
  `Temps execution : 120.42 sec` dans `results/resultat.txt`), et les deux
  modes ne sont pas strictement comparables.
- **Correction** : appliquer la même règle dans les deux, idéalement via une
  fonction unique de `core.py` qui orchestre la comparaison des combinaisons
  (voir B3).

---

## B. Code et outillage

### B1. Le CLI écrase `results/resultat.txt` sans en noter le contexte
- **Problème** : chaque exécution du CLI réécrit `results/resultat.txt`. Le
  fichier ne contient ni le nom de l'instance, ni la graine, ni la taille de
  population, ni le taux de mutation (la ligne `Dataset : ...` est affichée
  avant la redirection vers le fichier).
- **Impact** : le résultat de référence du dépôt est perdu à la prochaine
  exécution, et on ne peut pas savoir sur quelle instance ni avec quels
  paramètres il a été obtenu.
- **Correction** : ajouter une option `--output` (avec un nom par défaut
  horodaté ou dérivé de l'instance) et écrire un en-tête avec tous les
  paramètres, graine comprise.

### B2. Redirection de `sys.stdout` non restaurée
- **Problème** : `sys.stdout = Tee(sys.stdout, f)` n'est jamais annulé, et
  `f.close()` n'est appelé qu'en fin de script, sans `try/finally`.
- **Impact** : en cas d'exception (instance introuvable après la
  redirection, saisie invalide, Ctrl+C), le fichier peut rester incomplet.
- **Correction** : utiliser `with open(...) as f:` et
  `contextlib.redirect_stdout`, ou restaurer `sys.stdout` dans un `finally`.

### B3. Logique de comparaison dupliquée entre le CLI et l'interface
- **Problème** : la liste des 12 combinaisons et le partage du budget de temps
  sont codés deux fois (`core.py` et `interface.py`).
- **Impact** : toute modification doit être faite deux fois, et les deux
  versions ont déjà divergé (voir A10).
- **Correction** : une fonction `compare_combinations(...)` dans `core.py`,
  avec un callback de progression pour l'affichage en direct dans Streamlit.

### B4. Lecture d'instance dupliquée
- **Problème** : `read_vrptw_file` et `read_vrptw_content` contiennent le même
  analyseur.
- **Correction** : `read_vrptw_file` peut se limiter à
  `return read_vrptw_content(f.read())`.

### B5. Saisies du CLI non validées
- **Problème** : `int(input(...))` et `float(input(...))` lèvent une exception
  sur une saisie invalide. Un nom d'instance inexistant provoque un
  `FileNotFoundError` brut. Il faut aussi répondre 12 fois « oui » ou « non ».
- **Impact** : le CLI est peu pratique et ne peut pas être scripté.
- **Correction** : passer tous les paramètres en arguments `argparse`
  (`--instance`, `--population`, `--time`, `--mutation-rate`,
  `--combinations all|...`) en gardant le mode interactif par défaut.
  Corriger au passage la numérotation affichée (« 1. », « 3. », « 4. »).

### B6. Dossier `instances/__MACOSX`
- **Problème** : le dépôt suit 56 fichiers `instances/__MACOSX/._*.txt`,
  des métadonnées macOS issues d'une archive zip, sans rapport avec les
  instances.
- **Impact** : du bruit dans le dépôt, et un risque de confusion si on liste
  les fichiers `.txt` du dossier.
- **Correction** : `git rm -r instances/__MACOSX` et ajouter `__MACOSX/` au
  `.gitignore`. Ce dossier n'a pas été touché, conformément à la consigne de
  ne pas modifier `instances/`.

### B7. Pas de tests automatisés
- **Problème** : aucun test ne protège les fonctions de base.
- **Impact** : une régression (par exemple dans `check_time` ou le
  décodeur) passerait inaperçue.
- **Correction** : des tests `pytest` ciblés (faisabilité d'une route connue,
  décodage d'un chromosome, permutation valide après OX/PMX). Ajouter aussi un
  test de non-régression à graine fixe une fois A1 corrigé (nombre de
  générations fixé), sur le modèle de la vérification faite pour la matrice
  de distances.

### B8. Interface : divers
- `st.plotly_chart(..., key=f"chart_{time.time()}")` crée une clé unique à
  chaque rendu pour contourner un conflit de clés. Une clé stable par
  placeholder serait plus propre.
- L'interface est en anglais, le CLI et les journaux en français. Il vaudrait
  mieux harmoniser la langue.
- `render_map` est appelée à chaque rerun et retrace toutes les routes. On
  pourrait mettre la figure en cache par configuration.
