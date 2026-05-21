# API Documentation

## Meals

### GET /meals/

Returns all meals planned for a given week.

**Query parameters:**
- `year` (int, required): ISO year
- `week` (int, required): ISO week number

**Response:** `200 OK` — array of `Meal` objects.

---

### POST /meals/

Create a new meal.

**Body:** `Meal` object (JSON). `id` is auto-generated if omitted.

**Response:** `201 Created` — created `Meal` object.

---

### PUT /meals/{meal_id}

Update an existing meal.

**Path parameter:** `meal_id` (UUID)

**Body:** `Meal` object (JSON).

**Response:** `200 OK` — updated `Meal` object.

---

### DELETE /meals/{meal_id}

Delete a meal.

**Path parameter:** `meal_id` (UUID)

**Response:** `204 No Content`

---

## Shopping List

### GET /shopping-list/

Generate a shopping list for a given week from all planned meals.

**Query parameters:**
- `year` (int, required): ISO year
- `week` (int, required): ISO week number
- `format` (str, optional): set to `txt` to get a downloadable text file

#### JSON response (default)

```
GET /shopping-list/?year=2026&week=21
```

```json
{
  "year": 2026,
  "week": 21,
  "categories": {
    "légumes": [
      {"name": "tomates", "quantity": 6, "unit": "pièce"}
    ],
    "protéines": [
      {"name": "poulet", "quantity": 500, "unit": "g"}
    ],
    "féculents": [],
    "autres": []
  }
}
```

**Aggregation rules:**
- Ingredients are grouped by name (case-insensitive) and unit within each category.
- When two ingredients share the same name and unit, their quantities are summed.
- When units differ for the same ingredient name, they are listed as separate entries.
- Meals without ingredients do not cause errors (their contribution is an empty list).

#### Text export

```
GET /shopping-list/?year=2026&week=21&format=txt
```

Returns a `text/plain` file with `Content-Disposition: attachment` header.

**Example output:**

```
🛒 Liste de courses — Semaine 21 (2026)

## Légumes
- Tomates x6
- Courgettes 500g

## Protéines
- Poulet 500g
- Oeufs x12

## Féculents
- Riz 1kg

## Autres
- Huile d'olive 1L
```

---

## Models

### Ingredient

| Field      | Type                                              | Required | Default  | Description                     |
|------------|---------------------------------------------------|----------|----------|---------------------------------|
| `name`     | `str` (1–100 chars)                               | yes      | —        | Ingredient name                 |
| `quantity` | `float \| null`                                   | no       | `null`   | Quantity (null = unspecified)   |
| `unit`     | `str \| null`                                     | no       | `null`   | Unit (g, kg, L, pièce, …)       |
| `category` | `"légumes" \| "protéines" \| "féculents" \| "autres"` | no | `"autres"` | Ingredient category         |

### Meal

| Field         | Type                                        | Required | Default       | Description              |
|---------------|---------------------------------------------|----------|---------------|--------------------------|
| `id`          | `UUID`                                      | no       | auto-generated | Unique identifier        |
| `date`        | `date` (ISO 8601)                           | yes      | —             | Meal date                |
| `slot`        | `"breakfast" \| "lunch" \| "dinner"`        | yes      | —             | Time slot                |
| `name`        | `str` (1–120 chars)                         | yes      | —             | Meal name                |
| `notes`       | `str \| null`                               | no       | `null`        | Optional notes           |
| `calories`    | `int \| null`                               | no       | `null`        | Calorie count            |
| `ingredients` | `list[Ingredient]`                          | no       | `[]`          | List of ingredients      |
