# PowerCore — Jeu Incrémental + Analyse de données Python

> Projet pédagogique complet : un jeu incrémental qui génère des logs, analysés ensuite avec Python & Matplotlib.

---

## Structure du projet

```
powercore/
├── game.html           ← Le jeu incrémental (ouvrir dans un navigateur)
├── game_logs.json      ← Généré par le jeu après export (ne pas créer manuellement)
├── analyse_logs.py     ← Script Python d'analyse & graphiques
└── README.md           ← Ce fichier
```

---

## Étape 1 — Jouer & générer des logs

### Ouvre le jeu

```bash
# Double-clic sur game.html, ou depuis le terminal :
open game.html          # macOS
start game.html         # Windows
xdg-open game.html      # Linux
```

### Mécaniques du jeu

**PowerCore** est un jeu incrémental où tu gères une centrale énergétique.

| Élément | Description |
|---|---|
| **⚡ Énergie** | Ressource principale, gagnée en cliquant ou via des générateurs |
| **💎 Cristaux** | Monnaie premium débloquée avec l'upgrade "Synthèse cristaux" |
| **⬆ XP / Niveau** | Chaque énergie produite donne de l'XP → montée de niveau |
| **🏭 Générateurs** | Produisent de l'énergie passivement (sans cliquer) |
| **Améliorations** | Multiplient la puissance de clic ou le rendement des générateurs |

### Stratégie pour générer des logs intéressants (5-10 minutes de jeu)

1. Clique frénétiquement les 30 premières secondes
2. Achète le **Micro-réacteur** dès que possible (15 ⚡)
3. Continue de cliquer + achète des générateurs progressivement
4. Achète l'upgrade **Amplificateur x2** (50 ⚡)
5. Achète l'upgrade **Synthèse cristaux** (300 ⚡) → attend 2 cristaux
6. Achète l'upgrade **Turbo Clic** (2 💎)
7. Monte jusqu'au niveau 5 minimum

### Exporter les logs

Clique sur **⬇ Exporter logs (JSON)** → le fichier `game_logs.json` se télécharge.

Place-le dans le même dossier que `analyse_logs.py`.

---

## Étape 2 — Comprendre la structure des logs

Le fichier `game_logs.json` contient **3 sections** :

### `meta` — Métadonnées de session

```json
{
  "meta": {
    "game": "PowerCore",
    "session_start": "2024-01-15T14:32:00.000Z",
    "session_duration_ms": 312000,
    "total_logs": 847,
    "export_time": "2024-01-15T14:37:12.000Z"
  }
}
```

### `final_state` — État final du jeu

```json
{
  "final_state": {
    "energy": 4520,
    "total_produced": 18340,
    "crystals": 3,
    "clicks": 127,
    "level": 6,
    "click_power": 10,
    "passive_rate": 23.5,
    "generators": {
      "reactor": { "name": "Micro-réacteur", "count": 4, "rate_per_unit": 0.5 },
      "turbine": { "name": "Turbine solaire", "count": 2, "rate_per_unit": 3 }
    }
  }
}
```

### `events` — Liste de tous les événements

Chaque événement suit ce schéma commun :

```json
{
  "id": 42,
  "timestamp": 1705328053000,
  "elapsed_ms": 32140,
  "type": "click",
  "data": {
    "energy_snapshot": 235,
    "level": 2,
    "amount": 1,
    "click_number": 42,
    "click_power": 1
  }
}
```

#### Types d'événements

| `type` | Déclencheur | Données spécifiques |
|---|---|---|
| `click` | Le joueur clique | `amount`, `click_number`, `click_power` |
| `passive` | Production automatique (toutes les ~1s) | `amount`, `generators_active`, `rate_per_second` |
| `generator` | Achat d'un générateur | `generator_name`, `new_count`, `cost_paid`, `passive_rate_after` |
| `upgrade` | Achat d'une amélioration | `upgrade_name`, `click_power_after` |
| `milestone` | Palier franchi | `milestone_id`, `description` |
| `level_up` | Passage de niveau | `new_level`, `xp_overflow` |
| `crystal` | Cristal obtenu | `amount`, `total_crystals` |

---

## Étape 3 — Lancer l'analyse Python

### Prérequis

```bash
pip install matplotlib numpy
```

### Lancement

```bash
python analyse_logs.py
# ou avec un fichier spécifique :
python analyse_logs.py mon_fichier.json
```

---

## Étape 4 — Les 3 graphiques expliqués

### Graphique 1 — Courbe d'énergie cumulée

**Ce qu'il montre :**
L'évolution de l'énergie stockée tout au long de la session.

**Comment le lire :**
- Une courbe **linéaire** = le joueur clique à rythme constant
- Une courbe **exponentielle** = les générateurs s'accumulent et accélèrent la production
- Les **étoiles jaunes** ★ = milestones franchis (paliers importants)
- Les **triangles verts** ▲ = achats de générateurs (souvent suivis d'une accélération visible)

**Concept Python utilisé :**
```python
# On trie tous les events par elapsed_ms
sorted_events = sorted(data["events"], key=lambda e: e["elapsed_ms"])
times    = [e["elapsed_ms"] / 1000 for e in sorted_events]
energies = [e["data"]["energy_snapshot"] for e in sorted_events]

plt.plot(times, energies)
plt.scatter(milestone_times, milestone_energies, marker="*")
```

---

### Graphique 2 — Rythme de clics (histogramme)

**Ce qu'il montre :**
L'intensité d'engagement du joueur par tranches de 10 secondes.

**Comment le lire :**
- Des **barres hautes** en début de session → le joueur clique beaucoup au départ
- Des **barres plates** en fin de session → il se repose sur les générateurs
- La **ligne pointillée** = moyenne mobile sur 3 fenêtres (lisse les pics)
- Le **pic annoté** = moment d'engagement maximum

**Concept Python utilisé :**
```python
# np.histogram regroupe les timestamps en intervalles
times_s = [e["elapsed_ms"] / 1000 for e in click_events]
counts, edges = np.histogram(times_s, bins=np.arange(0, max_t, 10))

# Moyenne mobile avec convolution
moving_avg = np.convolve(counts, np.ones(3)/3, mode="same")
```

**À observer :** Si les clics s'arrêtent brutalement mais l'énergie continue d'augmenter (graphique 1), c'est que les générateurs prennent le relais → moment clé du jeu incrémental !

---

### Graphique 3 — Progression des générateurs

**Ce qu'il montre :**
L'historique d'achat de chaque type de générateur, en escaliers.

**Comment le lire :**
- Chaque **couleur** = un type de générateur
- Chaque **marche** = un achat (le joueur avait assez d'énergie)
- Plus les achats s'accélèrent → plus le joueur a de revenus passifs
- L'ordre d'achat révèle la **stratégie** : commence-t-il par les bon marché ou les puissants ?

**Concept Python utilisé :**
```python
# Courbe en escalier avec plt.step
step_times  = [0] + sorted(purchase_times)
step_counts = list(range(len(step_times)))   # 0, 1, 2, 3...

plt.step(step_times, step_counts, where="post")  # "post" = la marche monte après l'achat
```

---

## Concepts Python abordés

| Concept | Où dans le code |
|---|---|
| `json.load()` | Chargement du fichier de logs |
| Compréhensions de liste | `[e["elapsed_ms"] / 1000 for e in events]` |
| Tri avec `sorted()` + `key=` | Tri des événements par timestamp |
| `dict.get()` avec valeur par défaut | Accès sécurisé aux données d'événement |
| Filtrage de liste | `[e for e in events if e["type"] == "click"]` |
| `numpy.histogram()` | Regroupement des clics en intervalles |
| `numpy.convolve()` | Calcul de moyenne mobile |
| `matplotlib.pyplot` | Tracé des graphiques |
| `plt.figure()` + `GridSpec` | Mise en page multi-graphiques |
| `ax.step()` | Graphique en escalier |
| `ax.annotate()` | Annotation avec flèche |
| `ax.fill_between()` | Zone colorée sous une courbe |

---

## Extensions possibles (pour aller plus loin)

### Niveau intermédiaire

```python
# Calcul du taux de clics moyen par minute
total_clicks = data["final_state"]["clicks"]
duration_min = data["meta"]["session_duration_ms"] / 60000
cpm = total_clicks / duration_min
print(f"Clics par minute : {cpm:.1f}")

# Part de l'énergie produite par clic vs générateurs
click_events = [e for e in data["events"] if e["type"] == "click"]
total_from_clicks = sum(e["data"]["amount"] for e in click_events)
total_from_passive = data["final_state"]["total_produced"] - total_from_clicks
print(f"Énergie clics : {total_from_clicks:.0f}")
print(f"Énergie auto  : {total_from_passive:.0f}")
```

### Niveau avancé

```python
import pandas as pd

# Charger les events dans un DataFrame
df = pd.DataFrame(data["events"])
df["elapsed_s"] = df["elapsed_ms"] / 1000

# Filtrer les clics uniquement
clicks_df = df[df["type"] == "click"].copy()

# Grouper par tranche de 30 secondes
clicks_df["bin_30s"] = (clicks_df["elapsed_s"] // 30) * 30
clics_par_tranche = clicks_df.groupby("bin_30s").size()
print(clics_par_tranche)

# Graphique Pandas direct
clics_par_tranche.plot(kind="bar", title="Clics par tranche de 30s")
plt.show()
```