let currentYear;
let currentWeek;
const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
const SLOTS = [
    { key: "breakfast", label: "Breakfast" },
    { key: "lunch", label: "Lunch" },
    { key: "dinner", label: "Dinner" },
];

document.addEventListener('DOMContentLoaded', async () => {
    const currentDate = new Date();
    currentYear = currentDate.getFullYear();
    currentWeek = getISOWeek(currentDate);

    document.getElementById('prev-week')?.addEventListener('click', async () => {
        const monday = dateFromIsoWeek(currentYear, currentWeek);
        monday.setDate(monday.getDate() - 7);
        currentYear = monday.getFullYear();
        currentWeek = getISOWeek(monday);
        await refreshWeek();
    });

    document.getElementById('next-week')?.addEventListener('click', async () => {
        const monday = dateFromIsoWeek(currentYear, currentWeek);
        monday.setDate(monday.getDate() + 7);
        currentYear = monday.getFullYear();
        currentWeek = getISOWeek(monday);
        await refreshWeek();
    });

    document.getElementById('duplicate-week')?.addEventListener('click', async () => {
        const source = prompt(
            `Source week (format YYYY-WW). Default: ${currentYear}-${String(currentWeek).padStart(2, '0')}`,
            `${currentYear}-${String(currentWeek).padStart(2, '0')}`,
        );
        if (!source) {
            return;
        }

        const target = prompt('Target week (format YYYY-WW):');
        if (!target) {
            return;
        }

        const sourceWeek = parseWeekInput(source);
        const targetWeek = parseWeekInput(target);
        if (!sourceWeek || !targetWeek) {
            alert('Invalid week format. Use YYYY-WW.');
            return;
        }

        const duplicatedMeals = await duplicateWeek(sourceWeek, targetWeek);
        if (duplicatedMeals === null) {
            return;
        }

        currentYear = targetWeek.year;
        currentWeek = targetWeek.week;
        await refreshWeek();
        alert(`Duplicated ${duplicatedMeals.length} meal(s).`);
    });

    document.getElementById('generate-shopping-list')?.addEventListener('click', async () => {
        await generateShoppingList();
    });

    await refreshWeek();
});

function parseWeekInput(value) {
    const match = String(value).trim().match(/^(\d{4})-(\d{1,2})$/);
    if (!match) {
        return null;
    }
    return {
        year: Number.parseInt(match[1], 10),
        week: Number.parseInt(match[2], 10),
    };
}

async function refreshWeek() {
    const weekLabel = document.getElementById('week-label');
    const calendar = document.getElementById('calendar');

    if (weekLabel) {
        weekLabel.textContent = `Week ${currentWeek}, ${currentYear}`;
    }

    const meals = await fetchMeals(currentYear, currentWeek);
    if (calendar) {
        renderCalendarGrid(calendar, meals);
    }
}

function renderCalendarGrid(container, meals) {
    container.innerHTML = '';

    container.appendChild(buildCell('header', 'Slot / Day'));
    DAYS.forEach((day) => container.appendChild(buildCell('header', day)));

    SLOTS.forEach((slot) => {
        container.appendChild(buildCell('slot-label', slot.label));

        DAYS.forEach((_, dayIndex) => {
            const mealDate = dateForIsoDay(currentYear, currentWeek, dayIndex + 1);
            const dateIso = toISODate(mealDate);
            const meal = meals.find((m) => m.date === dateIso && m.slot === slot.key);

            const cell = document.createElement('div');
            cell.className = 'calendar-cell';

            const mealName = document.createElement('div');
            mealName.className = 'meal-name';
            mealName.textContent = meal ? meal.name : 'No meal';
            cell.appendChild(mealName);

            if (meal && Array.isArray(meal.ingredients) && meal.ingredients.length > 0) {
                const ingredients = document.createElement('div');
                ingredients.className = 'meal-ingredients';
                ingredients.textContent = meal.ingredients.map((item) => item.name).join(', ');
                cell.appendChild(ingredients);
            }

            const actionButton = document.createElement('button');
            actionButton.type = 'button';
            actionButton.className = 'meal-action';
            actionButton.textContent = meal ? 'Edit meal' : 'Add meal';
            actionButton.setAttribute('aria-label', `${actionButton.textContent} ${DAYS[dayIndex]}/${slot.label}`);
            actionButton.addEventListener('click', async () => {
                await promptAndSaveMeal(dateIso, slot.key, meal || null);
            });
            cell.appendChild(actionButton);

            container.appendChild(cell);
        });
    });
}

function buildCell(className, text) {
    const el = document.createElement('div');
    el.className = className;
    el.textContent = text;
    return el;
}

function dateForIsoDay(year, week, isoDay) {
    return dateFromIsoWeek(year, week, isoDay);
}

function toISODate(value) {
    const year = value.getFullYear();
    const month = String(value.getMonth() + 1).padStart(2, '0');
    const day = String(value.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

function parseIngredientsInput(raw) {
    if (!raw || !raw.trim()) {
        return [];
    }
    return raw
        .split(',')
        .map((entry) => entry.trim())
        .filter(Boolean)
        .map((name) => ({ name, category: 'autres' }));
}

async function promptAndSaveMeal(dateIso, slot, existingMeal) {
    const defaultName = existingMeal?.name || '';
    const mealName = prompt('Meal name:', defaultName);
    if (!mealName || !mealName.trim()) {
        return;
    }

    const defaultIngredients = existingMeal?.ingredients?.map((item) => item.name).join(', ') || '';
    const ingredientsInput = prompt('Ingredients (comma-separated):', defaultIngredients);
    if (ingredientsInput === null) {
        return;
    }

    const payload = {
        date: dateIso,
        slot,
        name: mealName.trim(),
        notes: existingMeal?.notes ?? null,
        calories: existingMeal?.calories ?? null,
        ingredients: parseIngredientsInput(ingredientsInput),
    };

    const response = await fetch('/meals/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        alert(error.detail || 'Failed to save meal.');
        return;
    }

    await refreshWeek();
}

async function generateShoppingList() {
    const response = await fetch(`/shopping-list/?year=${currentYear}&week=${currentWeek}`);
    if (!response.ok) {
        alert('Failed to generate shopping list.');
        return;
    }

    const payload = await response.json();
    const listRoot = document.getElementById('shopping-list-items');
    const emptyBlock = document.getElementById('shopping-list-empty');
    if (!listRoot || !emptyBlock) {
        return;
    }

    const categories = payload.categories || {};
    const entries = [];
    Object.keys(categories).forEach((category) => {
        (categories[category] || []).forEach((item) => {
            entries.push(item.name);
        });
    });

    listRoot.innerHTML = '';
    if (entries.length === 0) {
        emptyBlock.textContent = 'No ingredients found for this week.';
        return;
    }

    emptyBlock.textContent = '';
    entries.forEach((name) => {
        const li = document.createElement('li');
        li.textContent = name;
        listRoot.appendChild(li);
    });
}

function dateFromIsoWeek(year, week, isoDay = 1) {
    const simple = new Date(Date.UTC(year, 0, 1 + (week - 1) * 7));
    const dayOfWeek = simple.getUTCDay() || 7;
    if (dayOfWeek <= 4) {
        simple.setUTCDate(simple.getUTCDate() - dayOfWeek + 1);
    } else {
        simple.setUTCDate(simple.getUTCDate() + 8 - dayOfWeek);
    }
    simple.setUTCDate(simple.getUTCDate() + (isoDay - 1));
    return new Date(simple.getUTCFullYear(), simple.getUTCMonth(), simple.getUTCDate());
}

function getISOWeek(date) {
    const tmp = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
    const dayNum = tmp.getUTCDay() || 7;
    tmp.setUTCDate(tmp.getUTCDate() + 4 - dayNum);
    const yearStart = new Date(Date.UTC(tmp.getUTCFullYear(), 0, 1));
    return Math.ceil((((tmp - yearStart) / 86400000) + 1) / 7);
}

async function fetchMeals(year, week) {
    try {
        const response = await fetch(`/meals/?year=${year}&week=${week}`);
        if (!response.ok) {
            console.error('Failed to fetch meals:', response.statusText);
            return [];
        }
        return await response.json();
    } catch (err) {
        console.error('Failed to fetch meals:', err);
        return [];
    }
}

async function duplicateWeek(source, target) {
    const response = await fetch('/meals/duplicate-week', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ source, target }),
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        alert(error.detail || 'Failed to duplicate week.');
        return null;
    }

    return await response.json();
}
