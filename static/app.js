// Fetch meals for current ISO week from /meals?year=&week=
// Render in the grid, click a cell to add/edit a meal (prompt-based modal for the POC)
let currentYear;
let currentWeek;

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
        calendar.innerHTML = `<pre>${JSON.stringify(meals, null, 2)}</pre>`;
    }
}

function dateFromIsoWeek(year, week) {
    const simple = new Date(Date.UTC(year, 0, 1 + (week - 1) * 7));
    const dayOfWeek = simple.getUTCDay() || 7;
    if (dayOfWeek <= 4) {
        simple.setUTCDate(simple.getUTCDate() - dayOfWeek + 1);
    } else {
        simple.setUTCDate(simple.getUTCDate() + 8 - dayOfWeek);
    }
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
    const response = await fetch(`/meals?year=${year}&week=${week}`);
    if (!response.ok) {
        console.error('Failed to fetch meals:', response.statusText);
        return [];
    }
    return await response.json();
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
