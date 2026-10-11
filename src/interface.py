"""
Interface Streamlit du solveur VRPTW par algorithme génétique.

Lancement depuis la racine du projet :
    streamlit run src/interface.py
"""

import random
import time

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from core import (
    Customer,
    read_vrptw_content,
    is_feasible,
    total_distance,
    cost,
    generate_population,
    run_ga_from_population,
)
# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="VRPTW Genetic Algorithm",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────────────────────
# LIGHT THEME CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}

.stApp { background: #f4f6fa; color: #1a1d27; }

.app-header {
    background: #ffffff; border-bottom: 1px solid #e2e6ef;
    padding: 14px 28px; margin: -1rem -1rem 0 -1rem;
    display: flex; align-items: center; gap: 12px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.app-header h1 { font-size: 1.35rem; font-weight: 700; color: #111827; margin: 0; }
.app-header .badge {
    background: #2563eb; color: #fff; font-size: 0.65rem; font-weight: 700;
    padding: 3px 9px; border-radius: 4px; letter-spacing: 1.5px; text-transform: uppercase;
}

.panel {
    background: #ffffff; border: 1px solid #e2e6ef; border-radius: 12px;
    padding: 22px; box-shadow: 0 1px 6px rgba(0,0,0,0.05);
}

.section-label {
    font-size: 0.68rem; font-weight: 700; color: #6b7280;
    text-transform: uppercase; letter-spacing: 2px; margin: 18px 0 8px 0;
}
.divider { border: none; border-top: 1px solid #e8ecf4; margin: 16px 0; }

.info-chip-row { display: flex; gap: 8px; margin-top: 8px; }
.info-chip {
    flex: 1; background: #f0f4ff; border: 1px solid #c7d7fd;
    border-radius: 8px; padding: 9px 12px; text-align: center;
}
.info-chip .val { font-size: 1.1rem; font-weight: 700; color: #2563eb; font-family: 'JetBrains Mono', monospace; }
.info-chip .lbl { font-size: 0.6rem; color: #6b7280; text-transform: uppercase; letter-spacing: 1.2px; margin-top: 2px; }

.stButton > button {
    background: linear-gradient(135deg, #2563eb, #1d4ed8) !important;
    color: #fff !important; border: none !important; border-radius: 8px !important;
    font-family: 'Inter', sans-serif !important; font-weight: 700 !important;
    font-size: 0.9rem !important; padding: 12px 0 !important; width: 100% !important;
    margin-top: 6px !important; transition: all 0.2s !important;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #1d4ed8, #1e40af) !important;
    box-shadow: 0 6px 20px rgba(37,99,235,0.3) !important; transform: translateY(-1px) !important;
}

.stNumberInput label, .stTextInput label, .stFileUploader label, .stSelectbox label {
    color: #6b7280 !important; font-size: 0.68rem !important;
    font-weight: 700 !important; text-transform: uppercase !important; letter-spacing: 1.8px !important;
}
.stNumberInput > div > div > input, .stTextInput > div > div > input {
    background: #f9fafb !important; border: 1px solid #d1d5db !important;
    border-radius: 7px !important; color: #111827 !important;
    font-family: 'JetBrains Mono', monospace !important; font-size: 0.85rem !important;
}
.stSelectbox > div > div {
    background: #f9fafb !important; border: 1px solid #d1d5db !important;
    border-radius: 7px !important; color: #111827 !important;
}
.stCheckbox > label { font-family: 'JetBrains Mono', monospace !important; font-size: 0.78rem !important; color: #374151 !important; }

.stTabs [data-baseweb="tab-list"] {
    background: #f4f6fa !important; border-bottom: 2px solid #e2e6ef !important; gap: 2px !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important; border: none !important; color: #9ca3af !important;
    font-family: 'Inter', sans-serif !important; font-size: 0.75rem !important;
    font-weight: 600 !important; text-transform: uppercase !important;
    letter-spacing: 1.5px !important; padding: 10px 18px !important;
}
.stTabs [aria-selected="true"] { color: #2563eb !important; border-bottom: 2px solid #2563eb !important; }

.run-log-box {
    background: #f8fafc; border: 1px solid #e2e6ef; border-radius: 10px;
    padding: 18px 20px; font-family: 'JetBrains Mono', monospace;
    font-size: 0.76rem; line-height: 1.8; color: #1f2937;
    height: 66vh; overflow-y: auto; white-space: pre-wrap; word-break: break-all;
}

.champion-badge {
    background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px;
    padding: 10px 16px; font-weight: 700; color: #1d4ed8; font-size: 0.82rem;
    margin-bottom: 14px; display: inline-block;
}

.stFileUploader > div {
    background: #f9fafb !important; border: 1.5px dashed #d1d5db !important; border-radius: 8px !important;
}
.stProgress > div > div > div { background: #2563eb !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="app-header">
  <span style="font-size:1.5rem">🚚</span>
  <h1>VRPTW Genetic Algorithm</h1>
  <span class="badge">GA Solver</span>
</div>
<div style="height:16px"></div>
""", unsafe_allow_html=True)



# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────────────────────
for key,default in [
    ("customers",None),("capacity",None),("nb_vehicles",None),
    ("run_log",""),("results_table",[]),("best_solutions",{}),
    ("populations",{}),("ran",False),
]:
    if key not in st.session_state: st.session_state[key]=default


# ─────────────────────────────────────────────────────────────────────────────
# LAYOUT
# ─────────────────────────────────────────────────────────────────────────────
left_col, right_col = st.columns([1, 1.65], gap="medium")

with left_col:
    #st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">📁 Instance File</div>', unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Upload Solomon .txt file", type=["txt"])
    if uploaded_file:
        content = uploaded_file.read().decode("utf-8")
        customers, nb_vehicles, capacity = read_vrptw_content(content)
        st.session_state.customers   = customers
        st.session_state.capacity    = capacity
        st.session_state.nb_vehicles = nb_vehicles
        nc = len(customers)-1
        st.markdown(f"""
        <div class="info-chip-row">
          <div class="info-chip"><div class="val">{nc}</div><div class="lbl">Clients</div></div>
          <div class="info-chip"><div class="val">{capacity}</div><div class="lbl">Capacity</div></div>
          <div class="info-chip"><div class="val">{nb_vehicles}</div><div class="lbl">Max Vehicles</div></div>
        </div>""", unsafe_allow_html=True)

    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">⚙ Parameters</div>', unsafe_allow_html=True)
    c1,c2 = st.columns(2)
    with c1:
        population_size = st.number_input("Population Size", min_value=5, max_value=500, value=20, step=5)
        time_limit      = st.number_input("Time Limit (seconds)", min_value=1.0, max_value=3600.0, value=30.0, step=1.0, format="%.1f")
    with c2:
        mutation_rate = st.number_input("Mutation Rate", min_value=0.0, max_value=1.0, value=0.3, step=0.05, format="%.2f")
        seed_val      = st.number_input("Random Seed", min_value=0, max_value=9999, value=42)

    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">🔀 Combinations to Test</div>', unsafe_allow_html=True)

    COMBINATIONS = [
        ('tournament','ox','swap'),('tournament','ox','insertion'),('tournament','ox','inversion'),
        ('tournament','pmx','swap'),('tournament','pmx','insertion'),('tournament','pmx','inversion'),
        ('roulette','ox','swap'),('roulette','ox','insertion'),('roulette','ox','inversion'),
        ('roulette','pmx','swap'),('roulette','pmx','insertion'),('roulette','pmx','inversion'),
    ]
    sel_combos=[]
    ca,cb=st.columns(2)
    for idx,(sel,cross,mut) in enumerate(COMBINATIONS):
        label=f"{sel[:5]} · {cross} · {mut[:3]}"
        with (ca if idx%2==0 else cb):
            if st.checkbox(label, key=f"combo_{idx}", value=(idx<2)):
                sel_combos.append((sel,cross,mut))
    st.markdown(
        f'<div style="font-size:0.7rem;color:#9ca3af;text-align:right;margin-top:4px;">'
        f'{len(sel_combos)} combination{"s" if len(sel_combos)!=1 else ""} selected</div>',
        unsafe_allow_html=True)

    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    run_clicked = st.button("▶  RUN GENETIC ALGORITHM", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with right_col:
    #st.markdown('<div class="panel">', unsafe_allow_html=True)
    tab_log, tab_table, tab_map = st.tabs(["🖥  Run Log", "📋  Comparison Table", "🗺  Route Map"])
    with tab_log:    log_ph   = st.empty()
    with tab_table:  table_ph = st.empty()
    with tab_map:
        map_sel_ph   = st.empty()
        map_chart_ph = st.empty()
    st.markdown('</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# RENDER HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def render_log(text: str) -> None:
    """Afficher le journal d'exécution (texte échappé) dans l'onglet Run Log."""
    esc = text.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
    log_ph.markdown(f'<div class="run-log-box">{esc}</div>', unsafe_allow_html=True)


def render_table(results_list: list[dict]) -> None:
    """
    Afficher le tableau comparatif des combinaisons (trié par coût), le
    badge du champion et l'histogramme des coûts.
    """
    if not results_list:
        table_ph.info("No results yet — run the algorithm first.")
        return
    df = pd.DataFrame(results_list)
    best_val = df["Cost"].min()
    champ = results_list[0]
    with table_ph.container():
        st.markdown(
            f'<div class="champion-badge">🏆 Champion: {champ["Configuration"]} — '
            f'Vehicles: {champ["Vehicles"]}  ·  Distance: {champ["Distance"]}  ·  Cost: {champ["Cost"]}</div>',
            unsafe_allow_html=True)
        def hl(row):
            """Surligner la ligne de meilleur coût."""
            if row["Cost"]==best_val:
                return ['background-color:#eff6ff;color:#1d4ed8;font-weight:700']*len(row)
            return ['']*len(row)
        st.dataframe(df.style.apply(hl,axis=1), use_container_width=True,
                     height=min(420, 60+len(df)*38))
        colors=['#2563eb' if r["Cost"]==best_val else '#cbd5e1' for r in results_list]
        fig=go.Figure()
        fig.add_trace(go.Bar(
            x=[r["Configuration"] for r in results_list],
            y=[r["Cost"] for r in results_list],
            marker_color=colors,
            text=[r["Cost"] for r in results_list],
            textposition='outside',
            textfont=dict(size=10,color='#374151',family='JetBrains Mono'),
        ))
        fig.update_layout(
            paper_bgcolor='#ffffff', plot_bgcolor='#f9fafb',
            font=dict(color='#374151',family='Inter'),
            xaxis=dict(tickangle=-30,gridcolor='#e5e7eb',color='#6b7280',tickfont=dict(size=9)),
            yaxis=dict(gridcolor='#e5e7eb',color='#6b7280',title='Cost'),
            height=260, margin=dict(l=0,r=0,t=20,b=90), showlegend=False,
        )
        #st.plotly_chart(fig, use_container_width=True)
        #st.plotly_chart(fig, use_container_width=True, key=f"chart_{len(results_list)}")
        st.plotly_chart(fig, use_container_width=True, key=f"chart_{time.time()}")

def render_map(best_solutions: dict[str, list[list[int]]], customers: list[Customer]) -> None:
    """
    Tracer les routes de la meilleure solution de la configuration choisie
    dans la liste déroulante (dépôt, clients, une couleur par route).
    """
    if not best_solutions:
        with map_chart_ph.container(): st.info("No solutions yet — run the algorithm first.")
        return
    configs=list(best_solutions.keys())
    with map_sel_ph.container():
        selected=st.selectbox("Select configuration to visualize",options=configs,index=0,key="map_sel")
    solution=best_solutions[selected]
    COLORS=['#2563eb','#10b981','#f59e0b','#ef4444','#8b5cf6','#06b6d4',
            '#f97316','#ec4899','#84cc16','#14b8a6','#a78bfa','#fb923c',
            '#34d399','#60a5fa','#fbbf24','#f472b6','#4ade80','#38bdf8',
            '#e879f9','#fb7185','#a3e635','#2dd4bf','#c084fc','#fdba74']
    fig=go.Figure()
    for ri,route in enumerate(solution):
        col=COLORS[ri%len(COLORS)]
        xs=[customers[n].x for n in route]; ys=[customers[n].y for n in route]
        fig.add_trace(go.Scatter(x=xs,y=ys,mode='lines+markers',
            line=dict(color=col,width=2),marker=dict(size=6,color=col),
            name=f'Route {ri+1}',
            hovertemplate='Client %{text}<br>(%{x:.1f}, %{y:.1f})<extra></extra>',
            text=[str(n) for n in route]))
        if len(route)>=2:
            x0,y0=customers[route[-2]].x,customers[route[-2]].y
            x1,y1=customers[route[-1]].x,customers[route[-1]].y
            fig.add_annotation(x=x1,y=y1,ax=x0,ay=y0,xref='x',yref='y',axref='x',ayref='y',
                               showarrow=True,arrowhead=2,arrowsize=1.2,arrowwidth=1.5,
                               arrowcolor=col,opacity=0.65)
    fig.add_trace(go.Scatter(
        x=[c.x for c in customers[1:]], y=[c.y for c in customers[1:]],
        mode='markers+text',
        marker=dict(size=7,color='#64748b',symbol='circle',line=dict(color='#cbd5e1',width=1)),
        text=[str(c.id) for c in customers[1:]],
        textposition='top center',textfont=dict(size=7,color='#9ca3af',family='JetBrains Mono'),
        name='Clients',showlegend=False,
        hovertemplate='Client %{text}<br>(%{x:.1f}, %{y:.1f})<extra></extra>'))
    depot=customers[0]
    fig.add_trace(go.Scatter(x=[depot.x],y=[depot.y],mode='markers+text',
        marker=dict(size=14,color='#f59e0b',symbol='star',line=dict(color='#fff',width=1.5)),
        text=['DEPOT'],textposition='top right',
        textfont=dict(size=9,color='#d97706',family='Inter'),
        name='Depot',hovertemplate='Depot<br>(%{x:.1f}, %{y:.1f})<extra></extra>'))
    nb_v=len(solution); dist=round(total_distance(solution,customers),2); cv=round(cost(solution,customers),2)
    fig.update_layout(
        paper_bgcolor='#ffffff', plot_bgcolor='#f9fafb',
        font=dict(color='#374151',family='Inter',size=11),
        xaxis=dict(gridcolor='#e5e7eb',zerolinecolor='#e5e7eb',color='#6b7280',showgrid=True),
        yaxis=dict(gridcolor='#e5e7eb',zerolinecolor='#e5e7eb',color='#6b7280',showgrid=True,
                   scaleanchor='x',scaleratio=1),
        legend=dict(bgcolor='#f9fafb',bordercolor='#e2e6ef',borderwidth=1,
                    font=dict(size=8,family='JetBrains Mono'),x=1.01,y=1),
        height=540, margin=dict(l=10,r=10,t=42,b=10),
        title=dict(text=f"<b>{selected}</b>   |   {nb_v} routes  ·  dist={dist}  ·  cost={cv}",
                   font=dict(size=11,color='#6b7280',family='JetBrains Mono'),x=0.01))
    with map_chart_ph.container(): st.plotly_chart(fig, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# INITIAL RENDER
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.ran:
    render_log(st.session_state.run_log)
    render_table(st.session_state.results_table)
    if st.session_state.customers:
        render_map(st.session_state.best_solutions, st.session_state.customers)
else:
    render_log("En attente d'execution...\n\nConfigurez les parametres a gauche et cliquez sur RUN.")


# ─────────────────────────────────────────────────────────────────────────────
# RUN — with live streaming log
# ─────────────────────────────────────────────────────────────────────────────
if run_clicked:
    if st.session_state.customers is None:
        st.error("Please upload a VRPTW instance file first.")
    elif not sel_combos:
        st.warning("Select at least one combination.")
    else:
        random.seed(seed_val)
        customers = st.session_state.customers
        capacity  = st.session_state.capacity

        log_lines    = []
        results_list = []
        best_solutions  = {}
        start_global = time.time()
        total = len(sel_combos)

        for combo_idx, (sel, cross, mut) in enumerate(sel_combos):
            config    = f"{sel} + {cross} + {mut}"
            remaining = time_limit - (time.time() - start_global)
            n_remaining = total - combo_idx

            if remaining  <= 0 or n_remaining <= 0:
                log_lines.append(f"\n⚠ Temps global atteint — combinaison ignoree: {config}\n")
                render_log("\n".join(log_lines))
                break
            time_per_config = remaining / n_remaining
            # ── Header ────────────────────────────────────────────────────
            log_lines.append(f"\n\n-- {config} ...\n")
            render_log("\n".join(log_lines))

            # ── Generate initial population ───────────────────────────────
            t0         = time.time()
            population = generate_population(customers, capacity, population_size)
            sorted_pop = sorted(population, key=lambda s: cost(s, customers))

            log_lines.append(f"\nPopulation generee : {len(sorted_pop)}\n")
            render_log("\n".join(log_lines))

            # ── Log each solution exactly like the original format ─────────
            for si, sol in enumerate(sorted_pop):
                nb_v = len(sol)
                dist = round(total_distance(sol, customers), 2)
                cv   = round(cost(sol, customers), 2)
                log_lines.append(f"\n===== Solution {si+1} =====")
                log_lines.append(f"Routes: {sol}")
                log_lines.append(f"Nb vehicules utilises : {nb_v}")
                log_lines.append(f"Distance totale : {dist}")
                log_lines.append(f"Cost : {cv}\n")
                render_log("\n".join(log_lines))

            # ── Run GA evolution ──────────────────────────────────────────
            elapsed_gen = time.time() - t0
            ga_time = max(0, time_per_config - elapsed_gen)
            pop, best_sol = run_ga_from_population(
                population, customers, capacity,
                sel, cross, mut, mutation_rate, ga_time
            )

            elapsed = round(time.time() - t0, 2)
            nb_v    = len(best_sol)
            dist    = round(total_distance(best_sol, customers), 2)
            cv      = round(cost(best_sol, customers), 2)
            valid   = is_feasible(best_sol, customers, capacity)

            # ── Summary line ──────────────────────────────────────────────
            log_lines.append(
                f"\nVehicules : {nb_v} | Distance : {dist} | "
                f"Cout : {cv} | Faisable : {'ok' if valid else 'no'}\n"
            )
            render_log("\n".join(log_lines))

            results_list.append({
                "Configuration": config,
                "Vehicles":      nb_v,
                "Distance":      dist,
                "Cost":          cv,
                "Feasible":      "✓" if valid else "✗",
                "Time (s)":      elapsed,
            })
            best_solutions[config] = best_sol

            # Live table update after each combination
            sorted_results = sorted(results_list, key=lambda x: x["Cost"])
            render_table(sorted_results)

        # ── Persist ──────────────────────────────────────────────────────
        sorted_results = sorted(results_list, key=lambda x: x["Cost"])
        st.session_state.run_log        = "\n".join(log_lines)
        st.session_state.results_table  = sorted_results
        st.session_state.best_solutions = best_solutions
        st.session_state.customers      = customers
        st.session_state.ran            = True

        render_log("\n".join(log_lines))
        render_table(sorted_results)
        render_map(best_solutions, customers)
        st.success("✅ Exécution terminée")