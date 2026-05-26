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

**Constraints :**
- La combinaison `(date, slot)` est unique. Toute tentative de POST/PUT créant un doublon renvoie `400 Bad Request` avec `"A meal already exists for this date and slot"`.
- L'`id` (UUID) est immuable : un PUT préserve l'`id` existant même si le payload en contient un autre.

---

## Project structure

```
app/
  main.py             FastAPI app factory, CORS, static files, router registration
  routes.py           Endpoints meals + shopping-list, DI via get_store()
  models.py           Pydantic v2 models (Meal, Ingredient)
  storage.py          Abstraction MealStore + JsonFileStore + CosmosTableStore + create_store_from_env
  shopping.py         Agrégation ingrédients par catégorie/unité + export texte
  dependencies.py     Helpers FastAPI Depends
data/meals.json       Persistance locale (mode JsonFileStore)
static/               UI (index.html, app.js, styles.css)
tests/                pytest (unit + integration, mocks TableClient)
infra/main.bicep      Infra Azure (Log Analytics, App Insights, ACR, Cosmos Table, Container Apps)
Dockerfile            Image runtime python:3.11-slim, uvicorn on :8000
```

---

## Storage layer

L'application utilise une abstraction `MealStore` (méthodes async) avec deux implémentations interchangeables, sélectionnées au runtime par `create_store_from_env()`.

### Sélection automatique (`create_store_from_env`)

| `COSMOS_TABLE_ENDPOINT` | `COSMOS_KEY` | Implémentation retenue                                          |
|-------------------------|--------------|------------------------------------------------------------------|
| absent                  | —            | `JsonFileStore("data/meals.json")`                               |
| présent                 | présent      | `CosmosTableStore` avec `AzureNamedKeyCredential`                |
| présent                 | absent       | `CosmosTableStore` avec `DefaultAzureCredential` (managed identity en prod, dev creds en local) |

> [!IMPORTANT]
> Beaucoup de tenants Azure appliquent la policy `CosmosDB_LocalAuth_Modify` (effet `modify`) qui force `disableLocalAuth=true` sur tout compte Cosmos nouvellement créé. Dans ce cas, `COSMOS_KEY` est rejeté à l'exécution et **seul le chemin Entra ID (managed identity + RBAC data-plane) fonctionne**. C'est aussi la pratique recommandée par Azure.

### `JsonFileStore`

- Persistance dans un fichier JSON local (par défaut `data/meals.json`).
- Convient au dev local, aux tests, et au mode "fallback" si aucune variable Cosmos n'est définie.
- Pas de gestion de concurrence : un seul process en écriture.

### `CosmosTableStore`

- Backend Cosmos DB for Table via le SDK `azure-data-tables`.
- **PartitionKey** : `f"{year}-W{week:02d}"` (ex. `2026-W23`) — chaque semaine ISO est une partition, ce qui rend `list_by_week` performant (filtre `PartitionKey eq …`).
- **RowKey** : l'UUID du meal (string).
- **Sérialisation** : champs scalaires en colonnes, `ingredients` stocké en JSON dans une seule colonne.
- **Update inter-partitions** : si la `date` change de semaine ISO, l'entité est `delete` dans l'ancienne partition puis `create` dans la nouvelle. Sinon `upsert_entity(mode="Replace")`.
- **Pas de `create_table_if_not_exists()` à l'exécution** : le rôle data-plane Cosmos Table n'inclut pas `Microsoft.DocumentDB/databaseAccounts/sqlDatabases/write`. La table `meals` est pré-créée par le Bicep.
- Constructeur injectable (`table_client=…`) pour les tests unitaires (mocks `MagicMock`).

```python
# Initialisation depuis un autre code
from app.storage import CosmosTableStore
from azure.identity import DefaultAzureCredential

store = CosmosTableStore(
    endpoint="https://<account>.table.cosmos.azure.com:443/",
    credential=DefaultAzureCredential(),
)
```

---

## Environment variables

| Variable                              | Requis | Description                                                                 |
|---------------------------------------|--------|-----------------------------------------------------------------------------|
| `COSMOS_TABLE_ENDPOINT`               | non    | Endpoint Table de Cosmos (`https://<account>.table.cosmos.azure.com:443/`). Active `CosmosTableStore`. |
| `COSMOS_KEY`                          | non    | Clé primaire Cosmos. Si présente, auth par clé. Si absente et endpoint présent → auth AAD. |
| `COSMOS_TABLE_NAME`                   | non    | Nom de la table (défaut `meals`).                                            |
| `APPLICATIONINSIGHTS_CONNECTION_STRING`| non   | Chaîne de connexion App Insights pour la télémétrie.                         |

---

## Infrastructure (Bicep)

`infra/main.bicep` provisionne un environnement complet dans un seul resource group.

**Ressources créées :**

| Ressource                                                | Rôle                                                       |
|----------------------------------------------------------|------------------------------------------------------------|
| `Microsoft.OperationalInsights/workspaces`               | Log Analytics (rétention 30j)                              |
| `Microsoft.Insights/components`                          | Application Insights connecté au workspace                 |
| `Microsoft.ContainerRegistry/registries` (Basic)         | ACR avec admin enabled                                     |
| `Microsoft.DocumentDB/databaseAccounts`                  | Cosmos DB serverless + capability `EnableTable`            |
| `Microsoft.DocumentDB/databaseAccounts/tables`           | Table `meals` pré-créée                                    |
| `Microsoft.DocumentDB/databaseAccounts/tableRoleAssignments@2024-12-01-preview` | RBAC data-plane : `Cosmos DB Built-in Data Contributor` (`00000000-0000-0000-0000-000000000002`) au principal du Container App |
| `Microsoft.App/managedEnvironments`                      | Container Apps Environment lié à Log Analytics             |
| `Microsoft.App/containerApps`                            | App `meal-calendar` (port 8000, MI System-Assigned, scale 0–3) |

**Paramètres :**
- `appName` (string, min 3)
- `imageTag` (string, min 1)
- `location` (default `resourceGroup().location`)
- `cosmosEnableFreeTier` (bool, default `false`)

**Outputs :** `containerAppFqdn`, `acrLoginServer`.

**Points de vigilance :**
- `tableRoleAssignments` doit utiliser l'API `2024-12-01-preview` minimum (les versions antérieures retournent `"too old to be used for RBAC support"`).
- La table `meals` doit être créée par le Bicep, sinon le premier appel échoue avec 403 (manque `sqlDatabases/write`).
- L'identité du Container App est `SystemAssigned` ; son `principalId` est consommé directement dans le role assignment.

---

## Deployment

### Prérequis

```pwsh
az login
az account set --subscription <SUBSCRIPTION_ID>
az group create -n rg-meal-calendar-dev -l northeurope
```

### Build + push image vers ACR

```pwsh
$acr = az acr list -g rg-meal-calendar-dev --query "[0].name" -o tsv
$tag = "dev$(Get-Date -Format yyyyMMddHHmmss)"
az acr build --registry $acr --image meal-calendar:$tag --file Dockerfile . --no-logs
```

> [!NOTE]
> Le flag `--no-logs` évite un crash Windows (`'charmap' codec can't encode...`) lors du streaming des logs ACR sous PowerShell.

### Déploiement Bicep

```pwsh
az deployment group create `
  -g rg-meal-calendar-dev `
  -f infra/main.bicep `
  -p appName=mealcalendar imageTag=$tag
```

Le FQDN est exposé via l'output `containerAppFqdn` :

```pwsh
az containerapp show -g rg-meal-calendar-dev -n meal-calendar `
  --query "properties.configuration.ingress.fqdn" -o tsv
```

### Logs runtime

```pwsh
az containerapp logs show -g rg-meal-calendar-dev -n meal-calendar --tail 200 --follow
```

---

## Local development

```pwsh
# 1. Activer le venv
.\meal_calendar\Scripts\Activate.ps1

# 2. Installer les dépendances
python -m pip install -r requirements.txt

# 3. Lancer l'API (mode JsonFileStore — aucune variable Cosmos)
uvicorn app.main:app --reload --port 8000
```

UI disponible sur `http://localhost:8000/`, OpenAPI sur `http://localhost:8000/docs`.

Pour tester `CosmosTableStore` localement avec ses credentials développeur (AAD) :

```pwsh
$env:COSMOS_TABLE_ENDPOINT = "https://cosmos-mealcalendar-<suffix>.table.cosmos.azure.com:443/"
# Pas de COSMOS_KEY → DefaultAzureCredential
az login   # fournit les jetons à DefaultAzureCredential
uvicorn app.main:app --reload --port 8000
```

---

## Tests

```pwsh
.\meal_calendar\Scripts\Activate.ps1
python -m pytest -v
```

| Suite                                      | Couverture                                              |
|--------------------------------------------|---------------------------------------------------------|
| `tests/test_routes.py`                     | Endpoints CRUD `meals` (JsonFileStore via tmp_path)     |
| `tests/test_shopping.py`                   | Agrégation liste de courses, export texte               |
| `tests/integration/test_routes_v2.py`      | Tests d'intégration FastAPI                             |
| `tests/unit/test_meal_service_v2.py`       | MealService isolé                                       |
| `tests/unit/test_cosmos_table_store.py`    | CosmosTableStore avec `TableClient` mocké (MagicMock)   |

Les tests Cosmos n'effectuent **aucun appel réseau** : le `TableClient` est injecté via l'argument `table_client=…` du constructeur.

---

## Persistence verification

Procédure pour valider que les données survivent au redémarrage du conteneur (test de bout en bout post-déploiement) :

```pwsh
$base = "https://<containerAppFqdn>"
$payload = @{
  date="2026-06-03"; slot="lunch"; name="Probe"; notes=""; calories=420; ingredients=@()
} | ConvertTo-Json -Compress

# 1. Création
$created = Invoke-RestMethod -Uri "$base/meals/" -Method Post `
  -ContentType "application/json" -Body $payload

# 2. Vérification avant restart
$before = Invoke-RestMethod -Uri "$base/meals/?year=2026&week=23"

# 3. Restart de la revision active
$rev = az containerapp revision list -g rg-meal-calendar-dev -n meal-calendar `
  --query "[?properties.active].name | [0]" -o tsv
az containerapp revision restart -g rg-meal-calendar-dev -n meal-calendar --revision $rev
Start-Sleep -Seconds 25

# 4. Vérification après restart
$after = Invoke-RestMethod -Uri "$base/meals/?year=2026&week=23"
($after | Where-Object { $_.id -eq $created.id }) -ne $null   # → True attendu
```

---

## Troubleshooting

| Symptôme                                                                                | Cause                                                                            | Résolution                                                                     |
|-----------------------------------------------------------------------------------------|----------------------------------------------------------------------------------|--------------------------------------------------------------------------------|
| `403 Forbidden` sur `create_table_if_not_exists`                                        | Le rôle Cosmos Data Contributor n'inclut pas `sqlDatabases/write`                 | Pré-créer la table dans Bicep et supprimer l'appel applicatif                  |
| `Unauthorized` / `KeyBasedAuthenticationDisabled` malgré la présence de `COSMOS_KEY`    | Policy tenant `CosmosDB_LocalAuth_Modify` force `disableLocalAuth=true`          | Ne pas fournir `COSMOS_KEY` ; laisser `DefaultAzureCredential` faire l'AAD     |
| `Api version 2024-05-15 is too old to be used for RBAC support`                         | Mauvaise version d'API pour `tableRoleAssignments`                               | Utiliser `2024-12-01-preview`                                                  |
| `'charmap' codec can't encode...` pendant `az acr build`                                | PowerShell Windows + streaming logs ACR                                          | Ajouter `--no-logs`                                                            |
| `ContainerAppOperationError: Operation expired`                                         | Précédente opération encore en cours                                             | `az containerapp delete -g … -n meal-calendar -y` puis redéployer              |
| `pip install` installe dans le mauvais environnement                                    | Venv non activé                                                                  | `\.\meal_calendar\Scripts\Activate.ps1` puis `python -m pip --version` pour vérifier |

---

## Dependencies

`requirements.txt` :

```
fastapi
pydantic
uvicorn
pytest
httpx
azure-data-tables
azure-identity
```

Runtime Python : 3.11 (image de base `python:3.11-slim`).
