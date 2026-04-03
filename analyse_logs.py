"""
=============================================================
 PowerCore — Analyse des logs de jeu avec Python & Matplotlib
=============================================================
Usage :
    1. Joue à game.html pendant quelques minutes
    2. Clique sur "Exporter logs (JSON)" → game_logs.json
    3. Lance ce script : python analyse_logs.py
=============================================================
"""

import json
import sys
from pathlib import Path
from datetime import datetime

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

# ─────────────────────────────────────────────────────────────
# 0. CHARGEMENT DES DONNÉES
# ─────────────────────────────────────────────────────────────

LOG_FILE = "game_logs.json"

def load_logs(filepath: str) -> dict:
    """Charge le fichier JSON exporté par le jeu."""
    p = Path(filepath)
    if not p.exists():
        print(f"[ERREUR] Fichier introuvable : {filepath}")
        print("  → Joue à game.html et exporte les logs d'abord !")
        sys.exit(1)
    with open(p, encoding="utf-8") as f:
        data = json.load(f)
    print(f"[OK] {len(data['events'])} événements chargés")
    print(f"     Durée de session : {data['meta']['session_duration_ms'] / 1000:.1f}s")
    print(f"     Énergie produite  : {data['final_state']['total_produced']:,}")
    print()
    return data


# ─────────────────────────────────────────────────────────────
# 1. EXTRACTION & TRANSFORMATION
# ─────────────────────────────────────────────────────────────

def extract_events(data: dict) -> dict:
    """
    Sépare les événements par type.
    Retourne un dict { type: [events] }
    """
    events_by_type = {}
    for event in data["events"]:
        t = event["type"]
        events_by_type.setdefault(t, []).append(event)

    for t, evs in events_by_type.items():
        print(f"  Type '{t}': {len(evs)} événements")

    return events_by_type


def build_energy_timeline(events: list) -> tuple:
    """
    Construit la courbe d'énergie cumulée dans le temps.
    Utilise tous les événements (chaque event a un snapshot de l'énergie).
    Retourne (temps_en_secondes[], energie_cumulee[])
    """
    sorted_events = sorted(events["events"], key=lambda e: e["elapsed_ms"])
    times = [e["elapsed_ms"] / 1000 for e in sorted_events]
    energies = [e["data"].get("energy_snapshot", 0) for e in sorted_events]
    return times, energies


def build_click_histogram(click_events: list, bin_size_s: int = 10) -> tuple:
    """
    Regroupe les clics par tranches de bin_size_s secondes.
    Retourne (tranches[], counts[])
    """
    if not click_events:
        return [], []
    times_s = [e["elapsed_ms"] / 1000 for e in click_events]
    max_t = max(times_s)
    bins = np.arange(0, max_t + bin_size_s, bin_size_s)
    counts, edges = np.histogram(times_s, bins=bins)
    centers = (edges[:-1] + edges[1:]) / 2
    return centers, counts


def build_generator_progression(generator_events: list) -> dict:
    """
    Pour chaque générateur, retourne la liste des timestamps d'achat.
    Retourne { generator_name: [temps_en_secondes] }
    """
    progression = {}
    for e in generator_events:
        name = e["data"].get("generator_name", "Inconnu")
        t = e["elapsed_ms"] / 1000
        progression.setdefault(name, []).append(t)
    return progression


# ─────────────────────────────────────────────────────────────
# 2. STYLE GLOBAL
# ─────────────────────────────────────────────────────────────

COLORS = {
    "energy":    "#00d4ff",
    "clicks":    "#ff6b35",
    "generator": "#7fff6b",
    "milestone": "#ffdd57",
    "upgrade":   "#c77dff",
    "bg":        "#0a0e1a",
    "panel":     "#0f1628",
    "grid":      "#1e2d50",
    "text":      "#c8d8f0",
    "muted":     "#4a6080",
}

GENERATOR_COLORS = ["#00d4ff", "#ff6b35", "#7fff6b", "#c77dff", "#ffdd57"]

def apply_dark_style(ax, title: str, xlabel: str, ylabel: str):
    """Applique le thème sombre cohérent avec le jeu."""
    ax.set_facecolor(COLORS["panel"])
    ax.set_title(title, color=COLORS["text"], fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel(xlabel, color=COLORS["muted"], fontsize=10)
    ax.set_ylabel(ylabel, color=COLORS["muted"], fontsize=10)
    ax.tick_params(colors=COLORS["muted"], labelsize=9)
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(COLORS["grid"])
    ax.grid(True, color=COLORS["grid"], linestyle="--", linewidth=0.5, alpha=0.7)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(
        lambda x, _: f"{x/1000:.1f}K" if x >= 1000 else f"{x:.0f}"
    ))


# ─────────────────────────────────────────────────────────────
# 3. GRAPHIQUE 1 — Courbe d'énergie cumulée dans le temps
# ─────────────────────────────────────────────────────────────

def plot_energy_curve(ax, data: dict, events_by_type: dict):
    """
    Graphique 1 : Évolution de l'énergie au fil du temps.

    Ce graphique montre la croissance de l'énergie stockée.
    On y superpose les milestones (points d'étape) et les achats
    de générateurs pour voir leur impact sur la courbe.
    """
    times, energies = build_energy_timeline(data)

    # Courbe principale
    ax.plot(times, energies, color=COLORS["energy"], linewidth=2, zorder=3, label="Énergie")
    ax.fill_between(times, energies, alpha=0.12, color=COLORS["energy"])

    # Superposer les milestones
    milestones = events_by_type.get("milestone", [])
    if milestones:
        mt = [e["elapsed_ms"] / 1000 for e in milestones]
        me = [e["data"].get("energy_snapshot", 0) for e in milestones]
        ax.scatter(mt, me, color=COLORS["milestone"], s=60, zorder=5, label="Milestone", marker="*")

    # Superposer les achats de générateurs
    generators = events_by_type.get("generator", [])
    if generators:
        gt = [e["elapsed_ms"] / 1000 for e in generators]
        ge = [e["data"].get("energy_snapshot", 0) for e in generators]
        ax.scatter(gt, ge, color=COLORS["generator"], s=35, zorder=4, label="Achat générateur", marker="^")

    apply_dark_style(ax,
        title="Énergie accumulée dans le temps",
        xlabel="Temps de session (secondes)",
        ylabel="Énergie ⚡"
    )
    ax.legend(facecolor=COLORS["bg"], edgecolor=COLORS["grid"],
              labelcolor=COLORS["text"], fontsize=9)


# ─────────────────────────────────────────────────────────────
# 4. GRAPHIQUE 2 — Rythme de clics par fenêtre de temps
# ─────────────────────────────────────────────────────────────

def plot_click_rhythm(ax, events_by_type: dict):
    """
    Graphique 2 : Histogramme du rythme de clics.

    Montre l'intensité d'engagement du joueur dans le temps.
    Des barres hautes = le joueur clique beaucoup dans cette fenêtre.
    Utile pour détecter les phases actives vs passives.
    """
    click_events = events_by_type.get("click", [])
    if not click_events:
        ax.text(0.5, 0.5, "Aucun clic enregistré", transform=ax.transAxes,
                ha="center", va="center", color=COLORS["muted"])
        return

    centers, counts = build_click_histogram(click_events, bin_size_s=10)

    # Colorer les barres selon l'intensité
    max_c = max(counts) if len(counts) > 0 else 1
    norm_counts = counts / max_c
    bar_colors = [plt.cm.cool(v * 0.8 + 0.1) for v in norm_counts]

    bars = ax.bar(centers, counts, width=9, color=bar_colors, edgecolor="none", zorder=3)

    # Ligne de moyenne mobile
    if len(counts) >= 3:
        window = min(3, len(counts))
        moving_avg = np.convolve(counts, np.ones(window)/window, mode="same")
        ax.plot(centers, moving_avg, color=COLORS["clicks"],
                linewidth=2, linestyle="--", label=f"Moy. mobile ({window} fenêtres)", zorder=4)
        ax.legend(facecolor=COLORS["bg"], edgecolor=COLORS["grid"],
                  labelcolor=COLORS["text"], fontsize=9)

    # Annotation pic maximum
    if len(counts) > 0:
        peak_idx = np.argmax(counts)
        ax.annotate(f"Pic: {counts[peak_idx]} clics",
                    xy=(centers[peak_idx], counts[peak_idx]),
                    xytext=(centers[peak_idx], counts[peak_idx] + 0.5),
                    color=COLORS["milestone"], fontsize=8,
                    ha="center",
                    arrowprops=dict(arrowstyle="->", color=COLORS["milestone"], lw=1))

    apply_dark_style(ax,
        title="Rythme de clics du joueur (fenêtres de 10s)",
        xlabel="Temps de session (secondes)",
        ylabel="Nombre de clics"
    )
    # Override le formatter pour les entiers
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x)}"))


# ─────────────────────────────────────────────────────────────
# 5. GRAPHIQUE 3 — Progression des générateurs achetés
# ─────────────────────────────────────────────────────────────

def plot_generator_progression(ax, events_by_type: dict):
    """
    Graphique 3 : Chronologie des achats de générateurs.

    Chaque ligne représente un type de générateur.
    L'axe Y = nombre possédé, l'axe X = temps.
    Montre la stratégie d'investissement du joueur.
    """
    generator_events = events_by_type.get("generator", [])
    if not generator_events:
        ax.text(0.5, 0.5, "Aucun générateur acheté", transform=ax.transAxes,
                ha="center", va="center", color=COLORS["muted"])
        return

    progression = build_generator_progression(generator_events)

    for i, (name, times) in enumerate(progression.items()):
        color = GENERATOR_COLORS[i % len(GENERATOR_COLORS)]
        # Construire la courbe en escalier
        step_times = [0] + sorted(times)
        step_counts = list(range(len(step_times)))

        ax.step(step_times, step_counts, where="post",
                color=color, linewidth=2.5, label=name, zorder=3)
        ax.fill_between(step_times, step_counts, step="post",
                        alpha=0.08, color=color)

        # Marquer chaque achat
        ax.scatter(sorted(times), list(range(1, len(times) + 1)),
                   color=color, s=40, zorder=5)

    apply_dark_style(ax,
        title="Progression des achats de générateurs",
        xlabel="Temps de session (secondes)",
        ylabel="Nombre de générateurs possédés"
    )
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x)}"))
    ax.legend(facecolor=COLORS["bg"], edgecolor=COLORS["grid"],
              labelcolor=COLORS["text"], fontsize=9)


# ─────────────────────────────────────────────────────────────
# 6. ASSEMBLAGE FINAL
# ─────────────────────────────────────────────────────────────

def build_dashboard(data: dict, events_by_type: dict):
    """
    Assemble les 3 graphiques dans une figure unique façon dashboard.
    """
    fig = plt.figure(figsize=(16, 9), facecolor=COLORS["bg"])

    # Titre principal
    session_s = data["meta"]["session_duration_ms"] / 1000
    total_e   = data["final_state"]["total_produced"]
    n_clicks  = data["final_state"]["clicks"]
    level     = data["final_state"]["level"]

    fig.suptitle(
        f"PowerCore — Analyse de session  |  "
        f"Durée: {session_s:.0f}s  ·  "
        f"Énergie: {total_e:,} ⚡  ·  "
        f"Clics: {n_clicks}  ·  "
        f"Niveau: {level}",
        color=COLORS["energy"], fontsize=14, fontweight="bold",
        y=0.98
    )

    # Layout : ligne du haut = graphique 1 (large) + graphique 3
    #          ligne du bas  = graphique 2 (pleine largeur)
    gs = fig.add_gridspec(2, 2, hspace=0.38, wspace=0.28,
                          left=0.07, right=0.96, top=0.92, bottom=0.08)

    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[1, :])   # pleine largeur en bas
    ax3 = fig.add_subplot(gs[0, 1])

    ax1.set_facecolor(COLORS["panel"])
    ax2.set_facecolor(COLORS["panel"])
    ax3.set_facecolor(COLORS["panel"])

    plot_energy_curve(ax1, data, events_by_type)
    plot_click_rhythm(ax2, events_by_type)
    plot_generator_progression(ax3, events_by_type)

    # Pied de page
    fig.text(0.5, 0.01,
             f"Exporté le {data['meta']['export_time'][:19].replace('T', ' ')} · "
             f"{data['meta']['total_logs']} événements enregistrés",
             ha="center", color=COLORS["muted"], fontsize=8)

    plt.savefig("powercore_stats.png", dpi=150, bbox_inches="tight",
                facecolor=COLORS["bg"])
    print("[OK] Dashboard sauvegardé → powercore_stats.png")

    plt.show()


# ─────────────────────────────────────────────────────────────
# 7. POINT D'ENTRÉE
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    filepath = sys.argv[1] if len(sys.argv) > 1 else LOG_FILE

    print("=" * 55)
    print("  PowerCore — Analyse de logs")
    print("=" * 55)

    # Ici on charge les données du JSON et on les retranscrit dans un format "Python" en transformant le JSON en dictionnaire Python
    data = load_logs(filepath) # ici data = dictionnaire Python contenant les données du JSON
    events_by_type = extract_events(data)

    #print(events_by_type)
    print()
    print("[INFO] Génération du dashboard...")
    build_dashboard(data, events_by_type)