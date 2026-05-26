"""Shopping list aggregation logic."""
from typing import List, Dict
from .models import Meal

CATEGORIES = ["légumes", "protéines", "féculents", "autres"]


def aggregate_ingredients(meals: List[Meal]) -> Dict[str, List[Dict]]:
    """Aggregate ingredients from a list of meals into categories.

    Ingredients with the same name (case-insensitive) and same unit are merged
    by summing their quantities. When units differ, they are listed separately.
    """
    # key: (name_lower, unit_lower_or_none) -> {"name", "quantity", "unit", "category"}
    aggregated: Dict[tuple, dict] = {}

    for meal in meals:
        for ingredient in meal.ingredients:
            name_key = ingredient.name.strip().lower()
            unit_key = ingredient.unit.strip().lower() if ingredient.unit else None
            key = (name_key, unit_key, ingredient.category)

            if key in aggregated:
                existing = aggregated[key]
                if ingredient.quantity is not None and existing["quantity"] is not None:
                    existing["quantity"] = existing["quantity"] + ingredient.quantity
                elif ingredient.quantity is not None:
                    existing["quantity"] = ingredient.quantity
                # If existing already has a quantity and new one is None, keep existing
            else:
                aggregated[key] = {
                    "name": ingredient.name.strip(),
                    "quantity": ingredient.quantity,
                    "unit": ingredient.unit,
                    "category": ingredient.category,
                }

    result: Dict[str, List[Dict]] = {cat: [] for cat in CATEGORIES}
    for entry in aggregated.values():
        cat = entry["category"]
        result[cat].append({
            "name": entry["name"],
            "quantity": entry["quantity"],
            "unit": entry["unit"],
        })

    return result


def _format_ingredient_txt(item: dict) -> str:
    """Format a single ingredient for the text export."""
    name = item["name"].capitalize()
    qty = item["quantity"]
    unit = item["unit"]

    if qty is None:
        return f"- {name}"

    # Determine if quantity should be displayed as integer or float
    qty_str = str(int(qty)) if qty.is_integer() else str(qty)

    if unit is None:
        return f"- {name} x{qty_str}"

    unit_lower = unit.lower()
    # Units like "pièce" / "piece" are displayed as "x<qty>"
    if unit_lower in ("pièce", "piece", "pièces", "pieces"):
        return f"- {name} x{qty_str}"

    return f"- {name} {qty_str}{unit}"


def generate_txt(year: int, week: int, categories: Dict[str, List[Dict]]) -> str:
    """Generate a human-readable text shopping list."""
    lines = [f"🛒 Liste de courses — Semaine {week} ({year})", ""]

    category_labels = {
        "légumes": "Légumes",
        "protéines": "Protéines",
        "féculents": "Féculents",
        "autres": "Autres",
    }

    for cat in CATEGORIES:
        label = category_labels[cat]
        lines.append(f"## {label}")
        items = categories.get(cat, [])
        if items:
            for item in items:
                lines.append(_format_ingredient_txt(item))
        lines.append("")

    return "\n".join(lines)
