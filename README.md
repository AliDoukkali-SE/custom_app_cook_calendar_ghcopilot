# Meal Calendar API

FastAPI API to plan meals by week.

## Prerequisites

- Python 3.11+
- Existing virtual environment: `meal_calendar`
- Dependencies installed from `requirements.txt`

## Run Locally (Windows PowerShell)

### 1. Activate the existing venv

```pwsh
.\meal_calendar\Scripts\Activate.ps1
```

### 2. Verify venv pip

```pwsh
python -m pip --version
```

### 3. Install dependencies (if needed)

```pwsh
pip install -r requirements.txt
```

### 4. Start the API

```pwsh
uvicorn app.main:app --reload
```

### 5. Open the app

- UI: http://localhost:8000
- Health: http://localhost:8000/health
- OpenAPI: http://localhost:8000/docs

## Run Tests

### From the existing venv

```pwsh
.\meal_calendar\Scripts\python -m pytest -v
```

## Project Structure

- `app/`: FastAPI application (routers, services, repositories, schemas)
- `tests/`: unit and integration tests
- `static/`: static frontend
- `data/`: local JSON storage
