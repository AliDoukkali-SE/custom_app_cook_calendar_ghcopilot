# Meal Calendar API — Documentation

## Overview

Application FastAPI pour gérer un calendrier de repas. Les données sont stockées dans un fichier JSON (`data/meals.json`).

## Installation

```bash
# Créer et activer le virtual environment
python -m venv meal_calendar
.\meal_calendar\Scripts\Activate.ps1  # Windows

# Installer les dépendances
pip install -r requirements.txt
```

## Lancer l'application

```bash
uvicorn app.main:app --reload --port 8000
```

L'app est accessible sur http://127.0.0.1:8000

- Documentation interactive (Swagger) : http://127.0.0.1:8000/docs
- Health check : http://127.0.0.1:8000/health

---

## Modèle `Meal`

| Champ      | Type                                      | Requis | Description                     |
|------------|-------------------------------------------|--------|---------------------------------|
| `id`       | UUID                                      | Non    | Généré automatiquement          |
| `date`     | date (ISO: YYYY-MM-DD)                    | Oui    | Date du repas                   |
| `slot`     | `"breakfast"` \| `"lunch"` \| `"dinner"`  | Oui    | Créneau du repas                |
| `name`     | string (1-120 caractères)                 | Oui    | Nom du plat                     |
| `notes`    | string \| null                            | Non    | Notes optionnelles              |
| `calories` | int \| null                               | Non    | Nombre de calories (optionnel)  |

### Exemple JSON

```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "date": "2026-05-21",
  "slot": "lunch",
  "name": "Salade César",
  "notes": "Sans croûtons",
  "calories": 350
}
```

---

## Endpoints

### `GET /`

Sert la page statique `static/index.html`.

### `GET /health`

Retourne le statut de l'application.

**Réponse :** `{"status": "ok"}`

---

### `GET /meals/?year={year}&week={week}`

Liste les repas d'une semaine ISO donnée.

**Paramètres query :**
- `year` (int) — Année ISO
- `week` (int) — Numéro de semaine ISO

**Réponse :** `200 OK` — `list[Meal]`

**Exemple :**
```
GET /meals/?year=2026&week=21
```

---

### `POST /meals/`

Crée un nouveau repas.

**Body :** objet `Meal` (sans `id`, il sera généré)

**Réponse :** `201 Created` — `Meal`

**Exemple :**
```json
{
  "date": "2026-05-21",
  "slot": "dinner",
  "name": "Pâtes carbonara",
  "calories": 600
}
```

---

### `PUT /meals/{meal_id}`

Met à jour un repas existant.

**Paramètres path :**
- `meal_id` (UUID) — ID du repas

**Body :** objet `Meal`

**Réponse :** `200 OK` — `Meal`

**Erreur :** `404 Not Found` si le repas n'existe pas.

---

### `DELETE /meals/{meal_id}`

Supprime un repas.

**Paramètres path :**
- `meal_id` (UUID) — ID du repas

**Réponse :** `204 No Content`

**Erreur :** `404 Not Found` si le repas n'existe pas.

---

## Structure du projet

```
├── app/
│   ├── __init__.py
│   ├── main.py        # Point d'entrée FastAPI
│   ├── models.py      # Modèle Pydantic Meal
│   ├── routes.py      # Endpoints API /meals
│   └── storage.py     # Abstraction stockage + JsonFileStore
├── data/
│   └── meals.json     # Données persistées
├── static/
│   └── index.html     # Page d'accueil
├── requirements.txt
└── docs.md            # Cette documentation
```

## Tests

```bash
pytest
```