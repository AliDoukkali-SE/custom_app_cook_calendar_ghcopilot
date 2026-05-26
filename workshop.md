---
published: false
type: workshop
title: GitHub Copilot Hands-on Lab — Meal Calendar (Python + Azure)
short_title: Copilot HoL — Meal Calendar
description: Monter en compétence sur GitHub Copilot end-to-end en construisant une app Python "Meal Calendar" déployée sur Azure Container Apps, avec CI/CD GitHub Actions, IaC Bicep, Coding Agent et Azure SRE Agent.
level: beginner
language: fr
duration_minutes: 360
tags: python, fastapi, azure, copilot, github-actions, bicep, container-apps, cosmos-db, sre
navigation_levels: 3
navigation_numbering: false
---

# GitHub Copilot Hands-on Lab — Meal Calendar (Python + Azure)

> **Objectif** : ce workshop n'a pas pour but de livrer une vraie app de production, mais de faire **monter en compétence un développeur junior sur GitHub Copilot**, de la complétion in-IDE jusqu'au Coding Agent et à l'Azure SRE Agent, en passant par la CI/CD GitHub Actions et le déploiement Azure.
>
> **App fil rouge** : *Meal Calendar* — une mini-app Python (FastAPI) qui permet de planifier les repas (petit-déj / déj / dîner) sur un calendrier hebdo. Simple, épurée, déployable sur Azure.
>
> **Format** : 2 sessions de ~3 h (ou 1 journée complète).

> [!WARNING]
> GitHub Copilot évolue très vite. Certaines captures d'écran, raccourcis ou intitulés de menu peuvent changer. Sois adaptable, l'esprit de l'exercice reste le même.

---

## Pré-requis

Deux options pour suivre le workshop :

- **GitHub Codespaces** : le plus rapide, environnement prêt à l'emploi dans le navigateur.
- **Local** : meilleur moyen d'apprendre à configurer ses outils Copilot une fois pour toutes.

|                                              |                                                                                                  |
| -------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| Un compte GitHub                             | [Créer un compte gratuit](https://github.com/join)                                               |
| Accès GitHub Copilot                         | Voir section ci-dessous                                                                          |
| Un navigateur web                            | [Microsoft Edge](https://www.microsoft.com/edge) ou autre                                        |
| Un abonnement Azure                          | Pass formation, sandbox MS Learn, ou abo perso. Droits **Contributor + User Access Admin** sur un RG dédié. |
| Python 3.11+                                 | [python.org/downloads](https://www.python.org/downloads/)                                        |
| Docker Desktop                               | [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop)             |
| Azure CLI 2.60+                              | [docs.microsoft.com/cli/azure/install-azure-cli](https://learn.microsoft.com/cli/azure/install-azure-cli) |
| Bicep CLI                                    | `az bicep install`                                                                               |
| GitHub CLI (`gh`) 2.50+                      | [cli.github.com](https://cli.github.com/) — `winget install GitHub.cli` ou `brew install gh`     |
| GitHub Copilot CLI extension                 | `gh extension install github/gh-copilot` (installée après `gh auth login`)                       |

> [!IMPORTANT]
> **Toujours activer le venv Python avant tout `pip install`.**
> Sur Windows : `python -m venv .venv` puis `.\.venv\Scripts\Activate.ps1`. Vérifier avec `python -m pip --version` que pip pointe bien sur `.venv`.

### Accéder à GitHub Copilot

Plusieurs façons :

- **Copilot Free** : gratuit, limite mensuelle de complétions / chat. Pas de Coding Agent ni Code Review.
- **Copilot Pro / Pro+** : abonnement individuel, essai 30 jours.
- **Copilot Business / Enterprise** : via l'organisation. Demande l'accès sur [github.com/settings/copilot](https://github.com/settings/copilot).

> [!NOTE]
> 90 % du workshop tourne avec Copilot Free. Pour les **Niveaux 7 (Coding Agent) et 8 (Code Review automatique de PR)**, une licence payante est nécessaire.

### Forker / cloner le repo de base

Crée un repo GitHub vide nommé `meal-calendar` (ou fork un repo starter fourni par le formateur). On part de zéro pour bien voir Copilot construire.

```bash
git clone https://github.com/<ton-user>/meal-calendar
cd meal-calendar
code .
```

### Option Codespaces

Si la conf locale est compliquée, lance un **Codespace** depuis le bouton vert `Code > Codespaces`. Tu peux ensuite l'ouvrir dans ton VS Code local via `Open in VS Code`.

### Option locale — installer les extensions

1. [Visual Studio Code](https://code.visualstudio.com/)
2. [GitHub Copilot](https://marketplace.visualstudio.com/items?itemName=GitHub.copilot)
3. [GitHub Copilot Chat](https://marketplace.visualstudio.com/items?itemName=GitHub.copilot-chat)
4. [Python extension](https://marketplace.visualstudio.com/items?itemName=ms-python.python)

Connecte-toi à ton compte GitHub dans VS Code (icône user en bas à gauche) pour activer Copilot.

### Configurer GitHub CLI + Copilot CLI

GitHub CLI (`gh`) sera utilisé tout au long du workshop pour scripter le travail sur GitHub (issues, PRs, secrets, workflow runs…), et son extension `gh copilot` apporte Copilot **dans le terminal**.

```pwsh
# Auth GitHub (ouvre un navigateur)
gh auth login

# Vérifier
gh auth status

# Installer l'extension Copilot CLI
gh extension install github/gh-copilot

# Smoke test
gh copilot suggest "list all containers including stopped ones"
gh copilot explain "git rebase -i HEAD~3"
```

> [!TIP]
> `gh copilot alias` ajoute deux alias pratiques dans ton shell : `ghcs` (suggest) et `ghce` (explain). Sur PowerShell :
>
> ```pwsh
> gh copilot alias -- pwsh | Out-String | Invoke-Expression
> # Ajoute la ligne ci-dessus à $PROFILE pour que ce soit permanent
> ```

---

# Niveau 1 — Code Completion : bootstrap de l'app

Premier contact avec Copilot : la **complétion en ligne**. On va générer la structure initiale de l'app Meal Calendar pas à pas.

> [!TIP]
> Raccourcis Copilot Completion (VS Code) :
> - `Tab` : accepter la suggestion entière
> - `Ctrl + →` : accepter mot par mot
> - `Alt + ]` / `Alt + [` : suggestion suivante / précédente
> - `Ctrl + Enter` : ouvrir le panneau Copilot avec plusieurs propositions

## Changer de modèle de complétion

Dans la barre de titre VS Code, ouvre le menu Copilot → `Configure Inline Suggestions...` → `Change Completions Model...`. Selon ton plan, tu peux essayer plusieurs modèles et te faire ton avis.

## Étape 1 — Structure & dépendances

Crée un fichier `requirements.txt` à la racine et tape juste :

```text
# FastAPI app with Pydantic, uvicorn, pytest and httpx for testing
```

Laisse Copilot proposer les versions. Accepte avec `Tab` ligne par ligne.

Active le venv et installe :

```pwsh
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Étape 2 — Écrire du code à partir d'un prompt

**Qu'est-ce qu'un prompt ?** Une description en langage naturel utilisée pour générer des suggestions. Ça peut être une seule ligne ou plusieurs.

Crée `app/__init__.py` (vide) puis `app/main.py` et tape :

```python
# FastAPI app exposing GET / (serves static index.html) and GET /health returning {"status": "ok"}
# Mount /static for static files and include the meals router
```

Regarde Copilot construire l'app. Accepte / corrige.

## Étape 3 — Modèle Pydantic

Crée `app/models.py` :

```python
# Pydantic v2 model `Meal` with:
# - id: UUID generated by default
# - date: date (ISO format)
# - slot: Literal["breakfast", "lunch", "dinner"]
# - name: str (1-120 chars)
# - notes: str | None
```

Essaie aussi les expressions régulières — Copilot est très bon dessus :

```python
# function `validate_iso_date(s: str) -> bool` that returns True if s matches YYYY-MM-DD
```

```python
# function `validate_email(s: str) -> bool` (we'll need it later for sharing)
```

## Étape 4 — Couche de stockage

Crée `app/storage.py` avec une **abstraction** + une impl JSON locale :

```python
# Abstract base `MealStore` with async methods: list_by_week(year, week), create(meal), update(id, meal), delete(id)
# Concrete `JsonFileStore(MealStore)` reading/writing data/meals.json (create file if missing)
```

## Étape 5 — Routes CRUD

Crée `app/routes.py` :

```python
# APIRouter prefix="/meals" tags=["meals"]
# GET /?year=&week= -> list[Meal]
# POST / -> Meal (201)
# PUT /{meal_id} -> Meal
# DELETE /{meal_id} -> 204
# Inject the store via FastAPI dependency `get_store`
```

## Étape 6 — Frontend statique

Crée `static/index.html` :

```html
<!-- Simple weekly calendar: grid 7 columns (Mon-Sun) x 3 rows (breakfast/lunch/dinner)
     Header with prev/next week buttons. Loads /static/app.js -->
```

Puis `static/app.js` :

```js
// Fetch meals for current ISO week from /meals?year=&week=
// Render in the grid, click a cell to add/edit a meal (prompt-based modal for the POC)
```

## Étape 7 — Lancer l'app

```pwsh
uvicorn app.main:app --reload
```

Ouvre [http://localhost:8000](http://localhost:8000) → tu devrais voir le calendrier vide.

## Étape 8 — Next Edit Suggestion

C'est l'évolution de la complétion : quand tu modifies du code, Copilot anticipe la prochaine modif **ailleurs** dans le code.

Dans `app/models.py`, ajoute un champ `calories: int | None = None` au modèle `Meal`. Regarde Copilot proposer de propager le champ dans `routes.py`, `static/app.js`, voire les tests.

![Next Edit Suggestion](https://learn.microsoft.com/en-us/visualstudio/version-16.0/media/vs-2019/edit-suggestion.png)

## Side Quest #1 — Message de commit généré

Édite n'importe quel fichier. Dans le panneau Source Control, clique sur le **petit bouton magique** à droite du champ message → Copilot génère un commit message basé sur le diff. Pratique, et un dev paresseux n'a plus d'excuse pour `wip`.

## Side Quest #2 — Documentation

### Docstrings

Place ton curseur juste au-dessus d'une fonction (ex. `validate_iso_date`) et tape `"""` puis attends. Copilot rédige la docstring.

### README

Active la complétion sur Markdown (icône Copilot en bas à droite → `Enable for Markdown`). Crée `DOCS.md` :

```md
# Meal Calendar — Documentation

This documentation is generated with GitHub Copilot to showcase what the tool can do.

##
```

Tape un titre de section vide → Copilot remplit. Itère.

## Side Quest #3 — Copilot dans le terminal (`gh copilot`)

Copilot ne vit pas que dans VS Code. Avec l'extension `gh copilot` (installée dans les pré-requis), tu as Copilot **directement dans ton shell**.

### `suggest` — générer une commande

```pwsh
gh copilot suggest "create a python venv, activate it and install requirements.txt"
gh copilot suggest -t git "undo my last commit but keep the changes staged"
gh copilot suggest -t gh "list my open pull requests across all my repos"
```

`-t` filtre le type : `shell`, `gh`, `git`. À la fin, tu peux :

- **Copier** la commande dans le presse-papier
- **Exécuter** directement
- **Réviser** en demandant une variante

### `explain` — décrypter une ligne de commande

Idéal quand tu copies une commande d'un tuto sans la comprendre.

```pwsh
gh copilot explain "docker run --rm -it -v `${PWD}:/app -w /app python:3.11-slim bash"
gh copilot explain "az containerapp update -g rg-meal-calendar-dev -n meal-calendar --image acrxxxx.azurecr.io/meal-calendar:latest"
```

### Alias `ghcs` / `ghce`

Si tu as configuré les alias (cf. pré-requis), tu peux taper directement :

```pwsh
ghcs "kill the process using port 8000"
ghce "git reflog"
```

> [!TIP]
> Copilot CLI brille pour : `git` velu, `docker`, `kubectl`, `az`, `gh`, `ffmpeg`, `awk`/`sed`, `jq`, `Get-*` PowerShell. Il **ne lance jamais** une commande sans ta confirmation explicite.

## Big tasks vs small tasks

Copilot complétion est plus efficace sur des **petits prompts précis** que sur un gros prompt unique de 30 lignes.

> [!TIP]
> La meilleure stratégie pour générer un gros bout de code : démarrer par la structure de base avec un prompt simple, puis ajouter les morceaux un par un. Le mode **Agent** (Niveau 3) est plus adapté aux gros chantiers.

---

# Niveau 2 — Copilot Chat : qualité & tests

Copilot Chat est ton **coach de code**. Il garde l'historique de la conversation, peut expliquer, refactor, générer tests, sécuriser…

## Démarrer avec Copilot Chat

- **Chat View** : icône Copilot en haut à côté de la barre de recherche, ou `Ctrl + Shift + I`
- **Inline Chat** : `Ctrl + I` directement dans le code

## Built-in Agents : Ask, Plan & Agent

Trois modes intégrés :

- **Ask** : question / réponse, génération de code à coller
- **Plan** : crée un plan d'implémentation structuré pour une grosse tâche (couvert au Niveau 4)
- **Agent** : exécute des commandes, lit/écrit des fichiers de façon autonome (Niveau 3)

Ce niveau se concentre sur **Ask**.

## Sélection du modèle

Tu peux changer de modèle dans le sélecteur du Chat (GPT-5, Claude Sonnet 4.5, etc.). Selon ton admin Copilot et l'IDE, certains modèles seront dispo ou non.

## Slash Commands

- `/explain` — explique le code sélectionné
- `/fix` — propose un fix pour les bugs du code sélectionné
- `/tests` — génère des tests unitaires
- `/help`, `/clear`, `/vscode`

## Chat Participants

- `@workspace` — connaissance de tout le code du workspace
- `@vscode` — commandes et features de VS Code
- `@terminal` — contexte du terminal

## Manipulation de contexte

Le **prompt** compte, mais le **contexte** que tu attaches aussi. Clique sur l'icône trombone (📎) dans le Chat pour voir les options : `#codebase`, `#file`, `#selection`, `#changes`, `#problems`, `#fetch`…

### Exemple — référencer un fichier

```text
@workspace /explain #file:routes.py
```

### Exemple — questions sur les changements Git

```text
Peux-tu me proposer une entrée de CHANGELOG correspondant à mes #changes ?

Quels risques runtime introduisent mes #changes ?
```

### Exemple — sélection + dossier en contexte

Sélectionne quelques fonctions de `routes.py`, **drag-and-drop le dossier `app/`** dans la zone de chat, puis :

```text
@workspace /explain le code dans #selection
```

## Générer des tests

Crée `tests/test_routes.py`. Avec **Inline Chat (Ctrl+I)** :

```text
Génère une classe de tests pytest avec httpx.AsyncClient pour mes routes /meals (CRUD complet).
Utilise un JsonFileStore avec un tmp_path en fixture.
```

Essaie ensuite via la **Chat View** sur le même fichier. Compare la qualité.

Pour les mocks :

```text
Génère un mock du MealStore et utilise-le dans un test qui vérifie que POST /meals appelle store.create une seule fois.
```

Lance les tests :

```pwsh
pytest -v
```

> [!TIP]
> Copilot Chat garde l'historique. Tu peux référencer une réponse précédente : *"Adapte le mock précédent pour simuler une exception"*.

## Expliquer & documenter

Ouvre `app/storage.py` et :

```text
/explain Génère des docstrings Google-style pour cette classe
```

Pour le README :

```text
Complète mon #file:README.md avec une section "Run locally" et une section "Deploy to Azure"
```

## Refactor

Dans `app/routes.py` :

```text
Extrais une dépendance `get_week_filter(year: int, week: int)` qui valide les paramètres et retourne un objet WeekFilter.
Crée des versions async cohérentes partout où ça a du sens.
```

## Traduction de code

Ouvre `app/models.py`, sélectionne tout, et demande :

```text
Traduis ce code en TypeScript avec Zod pour la validation
```

Utile pour partager des modèles entre back Python et front TS.

## Sécuriser ton code

Introduis volontairement une faille dans `app/routes.py` (ex. concaténation d'un input dans un nom de fichier). Puis :

```text
Peux-tu vérifier ce code pour des problèmes de sécurité ?
Vois-tu des améliorations qualité à apporter ?
```

Puis :

```text
Peux-tu proposer un fix ?
```

Survole le bloc de code dans le chat → bouton pour **injecter directement** dans le fichier.

## Demander à Copilot de reviewer ton code

- **Sur tous tes git changes** : icône Copilot dans la vue Source Control
- **Sur un fichier** : clic droit dans l'éditeur → `Copilot` → `Review and Comment`

Copilot ajoute des commentaires inline avec boutons Accepter / Rejeter, et liste tout dans la vue **Comments** de VS Code.

---

# Niveau 3 — Copilot Agent : feature complète

Le mode **Agent** marque le passage d'un mode `AI-Infused` à `AI-Native` : Copilot ne se contente plus de répondre, il **agit** (lit/écrit des fichiers, lance des commandes, corrige ses erreurs en boucle).

Sélectionne le mode **Agent** dans le chat (`Ctrl + Shift + I`) et un modèle premium (Claude Sonnet 4.5, GPT-5).

## Étape 1 — Génération de code

Drag-and-drop `app/routes.py` et `app/models.py` dans la zone de chat. Tape :

```text
Ajoute une feature "duplicate week" :
- nouvelle route POST /meals/duplicate-week avec body {source: {year, week}, target: {year, week}}
- copie tous les repas de la semaine source vers la semaine cible (nouveaux UUID)
- bouton dans le frontend (static/app.js) qui ouvre un prompt et appelle la route
- tests pytest pour la nouvelle route
```

L'agent va :
1. Élaborer un plan
2. Modifier `routes.py`, `app.js`, ajouter des tests
3. Lancer `pytest` pour valider
4. Itérer si erreur

À la fin tu peux **Keep**, **Undo**, ou continuer à itérer.

## Étape 2 — Refactor

Nouvelle session Agent. Ajoute `models.py` au contexte :

```text
Ajoute un modèle `User` (id, email, display_name).
Ajoute un champ `owner_id: UUID` sur Meal qui référence un User.
Adapte le store et les routes pour filtrer par owner_id (header X-User-Id pour le POC).
Mets à jour les tests.
```

## Étape 3 — Génération de tests

```text
Ajoute des tests d'intégration end-to-end qui couvrent :
- créer 3 repas sur la même semaine
- les lister
- mettre à jour le déjeuner
- supprimer le dîner
Lance les tests et corrige jusqu'à ce qu'ils passent.
```

> [!NOTE]
> L'Agent peut exécuter des commandes terminal (avec ton accord). Tu peux activer `auto-approve` pour cette session si tu fais confiance au scope.

## Étape 4 — Édition multi-fichiers avancée

```text
Ajoute le support multi-langue (FR/EN/DE) au frontend.
Utilise un fichier static/i18n.json par langue.
Ajoute un sélecteur dans le header. Langue par défaut FR.
Persiste le choix dans localStorage.
```

Quand tu es content, **Keep** + commit.

---

# Niveau 4 — Copilot Plan & Implement + MCP Servers

Le **Plan agent** est dédié aux gros chantiers : il analyse, planifie, te pose des questions, puis passe la main à l'Agent pour implémenter.

## Étape 1 — Plan : ré-écrire l'app en mode "v2"

> [!IMPORTANT]
> **Commit ton code actuel** avant. On va faire une grosse manip qu'on pourra rollback.

Ouvre une nouvelle session Chat en mode **Plan** avec un modèle premium :

```text
Crée une v2 de l'API meal-calendar dans un dossier `app_v2/`.
- Garde FastAPI mais structure le code en couches : routers / services / repositories / schemas.
- Ajoute un service `MealService` qui orchestre la logique métier (ex. interdire deux repas sur le même slot/jour).
- Garde la compatibilité d'API avec la v1 (mêmes routes, mêmes payloads).
- Ajoute des tests unitaires (services) et d'intégration (routes).
- Lance les tests à la fin.
```

Le Plan agent va analyser le code existant, te poser des questions (framework de tests, choix d'archi), puis générer un plan structuré.

Pour voir le plan complet :

```text
Écris le plan complet en markdown.
```

## Étape 2 — Implémenter le plan

Clique sur **Start Implementation**. Le plan est passé à l'Agent qui va exécuter étape par étape, te demander confirmation pour les commandes, et mettre à jour la todo list.

À la fin tu peux **Keep** ou **Undo**. Si OK, supprime `app/` et renomme `app_v2/` en `app/` (ou demande à l'Agent de le faire).

```text
Ajoute les instructions de run dans le README.md
```

Commit.

## Étape 3 — Édition avancée multi-langue (déjà fait au Niveau 3, skip si déjà OK)

## Étape 4 — Configurer des MCP Servers

> **MCP — Model Context Protocol** (modelcontextprotocol.io) : un standard ouvert pour connecter les LLM à des outils et sources de données externes. *"USB-C des apps IA."*

Dans VS Code, depuis la vue Extensions, cherche et installe :

- **GitHub MCP Server**
- **Playwright MCP Server**

> [!NOTE]
> Si tu es sur **Codespaces dans le navigateur** : le MCP GitHub local en Docker peut ne pas marcher. Utilise la version **remote** : crée `.vscode/mcp.json` :
>
> ```json
> {
>   "servers": {
>     "github": { "type": "http", "url": "https://api.githubcopilot.com/mcp/" }
>   }
> }
> ```

Démarre les serveurs MCP. Pour GitHub MCP : authentification via PAT (sur Docker) ou SSO Codespaces.

## Étape 5 — Créer une issue via MCP

Dans les paramètres GitHub du repo, **active les Issues**.

Ouvre Copilot Chat en mode **Agent** :

```text
Aide-moi à rédiger une issue GitHub pour ajouter une feature "shopping list" à l'app meal-calendar.

En tant qu'utilisateur, je veux pouvoir générer automatiquement une liste de courses pour la semaine sélectionnée à partir des repas planifiés. La liste doit :
- agréger les ingrédients (champ ingredients à ajouter sur Meal)
- regrouper par catégorie (légumes, protéines, féculents, autres)
- être exportable en .txt

Aide-moi à créer l'issue avec description détaillée, détails d'implémentation et critères d'acceptation.
```

Itère jusqu'à satisfaction, puis :

```text
Crée l'issue sur mon projet GitHub.
```

Copilot mappe l'opération sur l'outil MCP et te demande l'autorisation. Accepte.

> [!TIP]
> **Alternative `gh` CLI** : tu peux aussi créer l'issue depuis le terminal sans MCP. Demande à Copilot CLI de te générer la commande :
>
> ```pwsh
> gh copilot suggest "create a github issue titled 'Shopping list feature' with a body loaded from issue.md and labels 'feature' and 'good-first-issue'"
> ```
>
> Puis exécute le résultat, par exemple :
>
> ```pwsh
> gh issue create --title "Shopping list feature" --body-file issue.md --label feature --label good-first-issue
> gh issue list --state open
> ```

## Étape 6 — Implémenter la feature avec l'Agent

Crée une branche `feat/shopping-list` :

```pwsh
git checkout -b feat/shopping-list
```

Mode **Agent** + modèle premium / Auto :

```text
Implémente l'issue #<numéro> pour la feature shopping list. Ajoute aussi des tests.
```

Quand c'est OK, **Keep** + commit.

## Étape 7 — Tester avec Playwright MCP

```text
Utilise les outils Playwright pour générer un test e2e pour ce scénario :

1. Ouvrir http://localhost:8000
2. Cliquer sur "Add meal" dans la cellule lundi/déjeuner
3. Saisir "Pâtes carbonara" avec les ingrédients "pâtes, lardons, œufs, parmesan"
4. Cliquer sur "Generate shopping list"
5. Vérifier que les 4 ingrédients apparaissent dans la liste
6. Prendre une capture d'écran de la liste

Vérifie chaque étape et ne passe à la suivante que si elle réussit.
```

Copilot exécute le test pas à pas, prend des captures, corrige tout seul si besoin.

## Étape 8 — Code Review Copilot sur la PR

Push la branche **et crée la PR depuis le terminal** avec `gh` :

```pwsh
git push -u origin feat/shopping-list

# Créer la PR en une commande, sans quitter le terminal
gh pr create --base main --head feat/shopping-list --fill --reviewer @copilot

# (Optionnel) Ouvrir la PR dans le navigateur
gh pr view --web
```

Quelques minutes plus tard, Copilot poste des commentaires de review : best practices, bugs potentiels, vulnérabilités, **scan CodeQL et secret scanning** inclus.

Pour suivre depuis le terminal :

```pwsh
gh pr status
gh pr checks
gh pr view --comments
```

## Étape 9 — Copilot Autofix sur les alertes CodeQL

> [!NOTE]
> **Copilot Autofix** (GitHub Advanced Security) génère automatiquement un **patch IA** pour chaque alerte détectée par CodeQL ou d'autres scanners de code, directement dans la PR. Dispo gratuitement sur les repos publics, et via GHAS sur les repos privés.

### Activer Code Scanning + Autofix

Dans `Settings > Code security and analysis` du repo :

- **Code scanning** : activer "Default setup" (CodeQL géré par GitHub) ou "Advanced" si tu veux un workflow custom.
- **Copilot Autofix** : activer la case `Copilot Autofix for code scanning alerts`.

Ou via `gh` :

```pwsh
gh api -X PATCH /repos/:owner/:repo/code-scanning/default-setup `
  -F state=configured -F query_suite=default
```

### Déclencher une alerte volontaire

Dans une nouvelle branche `chore/trigger-codeql`, ajoute dans `app/routes.py` un code intentionnellement vulnérable (ex. ouverture d'un fichier dont le chemin vient du body sans validation → *path traversal*). Push + PR.

### Observer Autofix au travail

Le workflow CodeQL tourne sur la PR. Dès qu'une alerte est levée, GitHub poste **un commentaire avec un patch suggéré** : explication en langage naturel + diff.

Depuis le terminal :

```pwsh
gh pr checks
gh code-scanning alerts list   # via extension `gh-code-scanning` si installée
```

Deux options :

1. **Commit suggestion** — bouton sur la PR pour appliquer le patch en un clic
2. **Edit in Codespaces** — ouvrir, tester, puis push manuellement

> [!TIP]
> Autofix est complémentaire au Code Review : Code Review attrape les problèmes de design/qualité, Autofix se concentre sur les vulnérabilités détectées par CodeQL. Combine les deux dans tes guard rails de PR.

> [!IMPORTANT]
> **NE MERGE PAS la PR de la shopping list.** On la garde pour les niveaux suivants (Coding Agent au Niveau 7). En revanche, tu peux fermer la PR de test Autofix.

---

# Niveau 5 — Conteneuriser & déployer sur Azure (Bicep)

On passe au cloud. Cible : **Azure Container Apps** + **Cosmos DB Table API** + **Application Insights**.

## Étape 1 — Dockerfile généré par Copilot


Crée `Dockerfile` à la racine et tape :

```dockerfile
# Multi-stage Dockerfile for the FastAPI meal-calendar app
# - Stage 1: install deps in a venv (python:3.11-slim)
# - Stage 2: copy venv, app/, static/, requirements.txt
# - Run as non-root user
# - HEALTHCHECK on /health
# - CMD uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Build et run local :

```pwsh
docker build -t meal-calendar:dev .
docker run --rm -p 8000:8000 meal-calendar:dev
```

Vérifie [http://localhost:8000/health](http://localhost:8000/health).

## Étape 2 — Bicep généré par Copilot

Crée `infra/main.bicep`. En mode **Agent** :

```text
#fetch https://learn.microsoft.com/azure/templates/microsoft.app/containerapps?pivots=deployment-language-bicep

Crée un Bicep main.bicep qui déploie :
- Log Analytics Workspace
- Application Insights connecté au Log Analytics
- Azure Container Registry (Basic, admin enabled pour un workshop simple)
- Cosmos DB account avec Table API (serverless, free tier désactivé par défaut)
- Container Apps Environment connecté au Log Analytics
- Container App "meal-calendar" :
  - image paramétrée
  - port 8000
  - auth registry via `username/passwordSecretRef` (ACR)
  - variables d'env : APPLICATIONINSIGHTS_CONNECTION_STRING, COSMOS_TABLE_ENDPOINT
  - identité managée System-Assigned (pour l'auth AAD vers Cosmos)
  - secret `acr-password` tiré de `acr.listCredentials()`
  - min replicas 0, max 3, scale rule HTTP
- Table `meals` pré-créée sous le compte Cosmos (`Microsoft.DocumentDB/databaseAccounts/tables@2024-05-15`) — indispensable car le rôle data-plane n'a pas le droit `sqlDatabases/write`.
- Role assignment data-plane Cosmos Table (`tableRoleAssignments@2024-12-01-preview`) : `Cosmos DB Built-in Data Contributor` (`00000000-0000-0000-0000-000000000002`) octroyé à l'identité managée du Container App, scope = compte Cosmos.

> [!IMPORTANT]
> Beaucoup de tenants Azure appliquent une policy `CosmosDB_LocalAuth_Modify` qui force `disableLocalAuth=true` sur tout nouveau compte Cosmos. Dans ce cas, l'auth par clé (`COSMOS_KEY`) est rejetée et **seule l'auth Entra ID (managed identity + RBAC data-plane)** fonctionne. C'est aussi la pratique recommandée.

Paramètres : location (default resourceGroup().location), appName, imageTag.
Outputs : containerAppFqdn, acrLoginServer.
```

Vérifie le `what-if` :

```pwsh
az login
az group create -n rg-meal-calendar-dev -l northeurope
az deployment group what-if -g rg-meal-calendar-dev -f infra/main.bicep -p appName=mealcalendar imageTag=dev
```

## Étape 3 — Premier déploiement manuel

Flow recommandé : build/push dans ACR d'abord, puis déploiement Bicep.

```pwsh
# 1. Récupérer l'ACR et build+push l'image depuis le code source
$acr = az acr list -g rg-meal-calendar-dev --query "[0].name" -o tsv
az acr build -r $acr -t meal-calendar:dev .

# 2. Déployer l'infra complète
az deployment group create -g rg-meal-calendar-dev -f infra/main.bicep -p appName=mealcalendar imageTag=dev
```

> [!TIP]
> Si `westeurope` est en saturation (`AKSCapacityHeavyUsage`) ou qu'un service est déjà provisionné dans une autre région, supprime puis recrée le resource group dans une région stable (ex: `northeurope`) avant de redéployer.

> [!WARNING]
> Si le déploiement reste bloqué avec `ContainerAppOperationError: Operation expired` ou `ContainerAppOperationInProgress` :
>
> ```pwsh
> az containerapp delete -g rg-meal-calendar-dev -n meal-calendar -y
> az deployment group create -g rg-meal-calendar-dev -f infra/main.bicep -p appName=mealcalendar imageTag=dev
> ```

Récupère l'URL :

```pwsh
az containerapp show -g rg-meal-calendar-dev -n meal-calendar --query "properties.configuration.ingress.fqdn" -o tsv
```

Ouvre `https://<fqdn>/health` → `{"status": "ok"}` 🎉

## Étape 4 — Brancher l'app sur Cosmos DB

Mode **Agent** :

```text
Ajoute une nouvelle implémentation `CosmosTableStore(MealStore)` dans app/storage.py
qui utilise azure-data-tables.
- Configurable via env vars COSMOS_TABLE_ENDPOINT et COSMOS_KEY (clé en option : si elle est absente, utiliser `DefaultAzureCredential()` d'azure-identity pour l'auth Entra ID via managed identity)
- Si COSMOS_TABLE_ENDPOINT est absent, fallback sur JsonFileStore
- PartitionKey = f"{year}-W{week:02d}", RowKey = meal id
- Ne PAS appeler `create_table_if_not_exists` à l'exécution : la table `meals` est pré-créée par le Bicep (le rôle data-plane n'a pas `sqlDatabases/write`)
- Mets à jour requirements.txt (azure-data-tables, azure-identity)
- Ajoute des tests unitaires avec un mock du TableClient
```

Re-build, re-push, re-deploy et vérifie que la persistance survit à un redémarrage du container :

```pwsh
$base = "https://<fqdn>"
$payload = @{ date="2026-06-03"; slot="lunch"; name="Probe"; notes=""; calories=420; ingredients=@() } | ConvertTo-Json -Compress
$created = Invoke-RestMethod -Uri "$base/meals/" -Method Post -ContentType "application/json" -Body $payload
$rev = az containerapp revision list -g rg-meal-calendar-dev -n meal-calendar --query "[?properties.active].name | [0]" -o tsv
az containerapp revision restart -g rg-meal-calendar-dev -n meal-calendar --revision $rev
Start-Sleep -Seconds 25
$after = Invoke-RestMethod -Uri "$base/meals/?year=2026&week=23"
($after | Where-Object { $_.id -eq $created.id }) -ne $null   # doit retourner True
```

---

# Niveau 6 — CI/CD GitHub Actions générée par Copilot

Copilot est très bon pour générer des workflows. On va construire la pipeline pas à pas.

## Étape 1 — Workflow CI from scratch

Crée `.github/workflows/ci.yml` :

```yaml
# GitHub Actions workflow `CI` that runs on pull_request and push to main
# - Setup Python 3.11 with pip cache
# - Install requirements.txt
# - Run ruff check
# - Run pytest with coverage, fail under 70%
```

Copilot va générer bloc par bloc. Comme tout YAML généré, **vérifie l'indentation et les quotes** — c'est l'erreur la plus fréquente.

## Étape 2 — Ajouter des tâches via prompts

À la fin du job tests, ajoute :

```yaml
# upload coverage report as artifact
```

```yaml
# add a job `docker-build` that builds the Dockerfile (no push) only on PR
```

## Étape 3 — Workflow CD avec OIDC

Crée `.github/workflows/cd.yml` :

```yaml
# GitHub Actions workflow `CD` triggered on push to main and workflow_dispatch
# Permissions: id-token: write, contents: read (for OIDC federation)
# Jobs:
# 1. build-and-push:
#    - azure/login@v2 with OIDC (client-id, tenant-id, subscription-id from secrets)
#    - az acr login
#    - docker build & push image tagged with github.run_id and "latest"
# 2. deploy:
#    needs: build-and-push
#    - azure/login@v2 OIDC
#    - az containerapp update with the new image tag
```

## Étape 4 — Configurer OIDC Azure ↔ GitHub

Demande à Copilot Chat :

```text
Génère les commandes az CLI pour créer une App Registration Entra ID,
ajouter une federated credential pour le repo `<user>/meal-calendar` sur la branche main et sur les pull_request,
et lui assigner le rôle Contributor sur le resource group rg-meal-calendar-dev.
Affiche les valeurs à mettre dans les secrets GitHub : AZURE_CLIENT_ID, AZURE_TENANT_ID, AZURE_SUBSCRIPTION_ID.
```

Exécute. Au lieu de configurer les secrets à la souris dans `Settings > Secrets and variables > Actions`, fais-le **en une commande** avec `gh` :

```pwsh
gh secret set AZURE_CLIENT_ID --body "<client-id>"
gh secret set AZURE_TENANT_ID --body "<tenant-id>"
gh secret set AZURE_SUBSCRIPTION_ID --body "<subscription-id>"

# Les valeurs non secrètes vont dans des variables (visibles dans les logs, plus simples à maintenir)
gh variable set ACR_NAME --body "acrmealcalendarxxxx"
gh variable set ACA_NAME --body "meal-calendar"
gh variable set RG_NAME --body "rg-meal-calendar-dev"

# Vérifier
gh secret list
gh variable list
```

Dans tes workflows, référence-les via `${{ secrets.AZURE_CLIENT_ID }}` et `${{ vars.RG_NAME }}`.

> [!IMPORTANT]
> **OIDC = pas de secret long-lived**. Aucun mot de passe / clé de service principal n'est stocké dans GitHub. C'est la façon recommandée d'authentifier des workflows à Azure depuis 2023.

## Étape 5 — Premier run

Push sur une branche → la PR déclenche CI (ruff + pytest + docker build).
Merge sur `main` → CD build+push+deploy.

Suivi en temps réel depuis le terminal :

```pwsh
gh run list --limit 5
gh run watch              # suit le dernier run en live
gh run view --log         # logs complets du dernier run
gh run view <run-id> --log-failed   # uniquement les steps en échec
```

Vérifie que `https://<fqdn>` sert ta dernière version.

## Étape 6 — Debug avec Copilot

Si un job échoue, récupère directement les logs via `gh` et passe-les à Copilot CLI :

```pwsh
gh run view --log-failed | gh copilot explain --stdin
```

Ou colle-les dans Copilot Chat :

```text
Voici les logs de l'étape "deploy" :
<paste>
Que se passe-t-il et comment fixer ?
```

Tu peux aussi attacher `#problems` pour les erreurs détectées par VS Code dans tes YAML.

## Étape 7 — Bonus : workflow d'infra

Crée `.github/workflows/infra.yml` (déclenchement `workflow_dispatch`) qui run `az deployment group create` sur `infra/main.bicep`. Demande à Copilot.

---

# Niveau 7 — GitHub Copilot Coding Agent

> [!NOTE]
> Le **Coding Agent** est un assistant IA qui travaille **directement sur GitHub.com**. Il prend une issue, crée une branche, code, ouvre une PR, lit tes review comments, itère. Nécessite Copilot Pro / Business / Enterprise.

## Étape 1 — Assigner une issue au Coding Agent

Retrouve l'issue "shopping list" créée au Niveau 4 (ou crée une nouvelle issue, par exemple "Add Microsoft Entra ID authentication").

Deux façons d'assigner :

**Via l'UI GitHub** : section **Assignees** de l'issue → sélectionne **Copilot**.

**Via `gh` CLI** :

```pwsh
gh issue list
gh issue edit <numero> --add-assignee @copilot
# ou plus court
gh issue develop <numero> --assignee @copilot --base main
```

Tu peux ajouter un prompt complémentaire en commentaire d'issue :

```pwsh
gh issue comment <numero> --body "Une fois la feature implémentée, génère un test Playwright e2e qui valide le parcours complet et inclus une capture d'écran dans la description de la PR."
```

## Étape 2 — Suivre la progression

Le Coding Agent crée une PR. Le **premier commit = le plan**. Tu peux commenter pour donner des précisions.

Clique sur **View Session** depuis la PR pour voir Mission Control : actions, fichiers modifiés, commandes lancées, erreurs corrigées.

Depuis le terminal :

```pwsh
gh pr list --author "app/copilot-swe-agent"
gh pr view <numero> --comments
gh pr checks <numero>
```

> [!TIP]
> Le Coding Agent peut prendre de quelques minutes à 30+ minutes selon la tâche. **Continue avec le Niveau 8** pendant qu'il bosse.

## Étape 3 — Reviewer la PR

Une fois la PR prête : review classique. Pour demander une modif, ajoute un commentaire de review **en mentionnant @copilot** :

```pwsh
gh pr comment <numero> --body "@copilot Peux-tu retirer le dossier de screenshots qui a été commit par erreur ?"
```

L'agent reprend, fait les modifs, push.

Quand tu es OK :

```pwsh
gh pr merge <numero> --squash --delete-branch
```

---

# Niveau 8 — Azure SRE Agent

> [!NOTE]
> **Azure SRE Agent** (preview) est un agent Microsoft qui surveille tes ressources Azure, détecte les incidents, propose des diagnostics et des fixes. Il s'intègre avec Application Insights, Log Analytics, et peut interagir avec GitHub pour ouvrir des PR de fix.

## Étape 1 — Activer Azure SRE Agent

Dans le portail Azure → cherche **Azure SRE Agent** → Create.

- Subscription / RG : `rg-meal-calendar-dev`
- Donne-lui accès au RG (rôle **Reader** au minimum, **Contributor** pour les actions de remédiation)
- Connecte la **Container App** et l'**Application Insights** créés au Niveau 5

> [!WARNING]
> Vérifie la disponibilité régionale avant le jour J. Si non dispo : repli sur App Insights Workbooks générés par Copilot Chat (`#fetch` de la doc Workbooks + prompt agent).

## Étape 2 — Questions naturelles

Dans la console SRE Agent :

```text
Quelle est la latence p95 de /meals sur la dernière heure ?
```

```text
Y a-t-il eu des erreurs 5xx dans les 30 dernières minutes ? Lesquelles ?
```

```text
Quelle est la cause probable du dernier spike de CPU ?
```

## Étape 3 — Incident simulé

On va casser volontairement la prod. Crée une branche `bug/break-post-meals` :

Mode Agent dans VS Code :

```text
Modifie app/routes.py : dans la route POST /meals, ajoute une ligne `raise RuntimeError("boom")` avant le store.create.
Ajoute aussi un log error.
Ne touche à rien d'autre.
```

Push, crée une PR, merge sur `main`. La CD pousse la version cassée.

Sur le frontend, essaie d'ajouter un repas → 500. Laisse tourner 5-10 minutes pour générer du signal.

## Étape 4 — Détection & diagnostic

Sur SRE Agent :

```text
J'ai un problème en prod, peux-tu investiguer ?
```

L'agent doit :
- Détecter le pic de 500 sur POST /meals
- Identifier la stack trace `RuntimeError: boom`
- Pointer le commit suspect (intégration GitHub)
- Proposer un rollback ou un fix

Demande-lui :

```text
Génère un rapport d'incident au format markdown pour ce problème.
```

## Étape 5 — Rollback

Deux options :

1. **Via SRE Agent** s'il a les droits Contributor : il peut révertir vers le tag précédent.
2. **Via GitHub Actions** : `workflow_dispatch` du workflow CD avec un `imageTag` pointant sur un build précédent, ou `git revert <sha>` + push.

```pwsh
git revert <sha-du-commit-cassé>
git push
```

La CD redéploie une version saine. Vérifie sur SRE Agent que les 5xx s'éteignent.

---

# Niveau 9 — Customisation Copilot pour le projet

On revient sur l'IDE pour rendre Copilot **vraiment** au courant des conventions du projet.

> [!NOTE]
> Disponible sur VS Code, Visual Studio et github.com.

## Étape 1 — `copilot-instructions.md`

Crée `.github/copilot-instructions.md` :

```md
# Conventions du projet meal-calendar

- Réponds en français, mais le code et les identifiants restent en anglais.
- Stack : Python 3.11, FastAPI, Pydantic v2, pytest, httpx.
- Toujours utiliser des type hints stricts. `from __future__ import annotations` en tête des modules.
- Tests : pytest, pattern AAA (Arrange / Act / Assert), fixtures dans `tests/conftest.py`.
- Couche storage abstraite : ne jamais appeler Cosmos directement depuis les routes.
- Front : HTML/JS vanilla, pas de framework.
- Infra : Bicep, déploiement via `az deployment group`.
- CI/CD : GitHub Actions avec OIDC (jamais de service principal long-lived).
- Quand pertinent, fournir des liens vers la doc officielle (FastAPI, Azure, OWASP).
```

Refais quelques requêtes Copilot Chat sur le projet → tu dois sentir la différence (réponses en FR, tests pytest avec AAA, etc.).

## Étape 2 — Instructions par scope

Crée `.github/instructions/python-tests.instructions.md` :

```md
---
description: Conventions pour les tests Python du projet
applyTo: "tests/**/*.py"
---

- Framework : pytest + httpx.AsyncClient pour les routes.
- Une classe par module testé, méthodes `test_<comportement>`.
- Fixtures réutilisables dans `tests/conftest.py`.
- Au moins 1 cas négatif (input invalide / 4xx) par endpoint.
- Pas de I/O réel : utiliser tmp_path pour JsonFileStore, mocks pour CosmosTableStore.
```

Et `.github/instructions/bicep.instructions.md` :

```md
---
description: Conventions Bicep du projet
applyTo: "infra/**/*.bicep"
---

- Toujours utiliser des modules Bicep AVM (Azure Verified Modules) quand ils existent.
- Paramètres avec descriptions et @minLength/@allowed quand pertinent.
- Outputs : noms en camelCase, jamais de secret en output.
- Tags par défaut : { project: 'meal-calendar', environment: <param> }.
```

## Étape 3 — Reusable prompts

Crée `.github/prompts/add-endpoint.prompt.md` :

```md
---
agent: 'agent'
tools: ['codebase', 'editFiles', 'runCommands', 'runTests']
description: 'Ajouter un endpoint REST au router meals avec tests'
---

Ajoute un nouvel endpoint à `app/routes.py` selon les conventions du projet.

Demande à l'utilisateur si pas fourni :
- méthode HTTP (GET/POST/PUT/DELETE/PATCH)
- chemin relatif (sous /meals)
- payload d'entrée et de sortie

Tâches :
1. Mettre à jour le schema Pydantic dans `app/models.py` si besoin.
2. Ajouter la méthode correspondante au `MealStore` (interface + impls).
3. Implémenter la route avec dependency injection.
4. Écrire au moins 2 tests pytest (cas nominal + cas d'erreur).
5. Lancer pytest et corriger.
6. Mettre à jour le README si l'API publique change.
```

Appelle-le dans le chat :

```text
/add-endpoint
```

> [!TIP]
> [github.com/github/awesome-copilot](https://github.com/github/awesome-copilot) regorge d'exemples d'`instructions`, `prompts` et `agents` à recopier.

## Étape 4 — Custom agent

Crée `.github/agents/api-reviewer.agent.md` :

```md
---
description: "Reviewer d'API FastAPI orienté qualité, sécurité OWASP et perf"
name: "ApiReviewer"
tools: ["codebase", "search", "problems", "fetch", "githubRepo"]
model: Claude Sonnet 4.5
---

## Rôle

Tu es un reviewer senior d'API REST FastAPI. Tu lis le code et identifies :

1. **Sécurité** : OWASP API Top 10 (injection, auth cassée, exposition de données, mass assignment, rate limiting…).
2. **Validation** : robustesse des modèles Pydantic, gestion des erreurs.
3. **Performance** : calls DB inutiles, N+1, manque d'async.
4. **Conventions** : respect de `.github/copilot-instructions.md`.

## Méthode

- Commence par lister les routes du projet (cherche `@router.` dans `app/`).
- Pour chaque route, donne un score /10 et liste les findings classés par sévérité (P0 / P1 / P2).
- Termine par un plan de remédiation priorisé.
```

Sélectionne le custom agent `ApiReviewer` dans la liste des modes du chat → demande-lui une review.

## Étape 5 — Prompt engineering avancé

### Role prompt

```text
Je travaille sur une app FastAPI Python 3.11 nommée meal-calendar, déployée sur Azure Container Apps.
Stack : Pydantic v2, pytest, Cosmos DB Table API, Bicep, GitHub Actions OIDC.
Mon code doit respecter OWASP API Top 10 et passer un coverage de 70%.
Agis comme mon code coach senior. Quand tu réponds :
- pose-moi une question si l'intention n'est pas claire
- donne du code complet, pas de "..." cachant l'implémentation
- ajoute un lien vers la doc officielle pertinente
- fournis des tests
Tu as compris ces instructions ?
```

### One-shot / Few-shot

Pour générer des tests qui collent au style maison, fournis 1 ou 2 exemples dans le prompt.

### Fetch web

```text
Je veux ajouter un rate-limiter à mon API. Quelle est la dernière façon recommandée pour FastAPI ?
#fetch https://www.starlette.io/middleware/
```

### Vision (debug visuel)

Drag & drop une capture d'écran d'un bug d'UI dans le chat avec un modèle vision-capable :

```text
Quand je clique sur une cellule du calendrier, le modal s'ouvre mais déborde sur mobile. Voici la capture. Comment fixer en CSS ?
```

---

# Récap & garde-fous

## Les modes Copilot vus

| Mode                       | Où                          | Quand l'utiliser                                                  |
| -------------------------- | --------------------------- | ----------------------------------------------------------------- |
| **Completion**             | IDE                         | Écriture courante de code, propagation locale, doc inline         |
| **Chat — Ask**             | IDE / github.com            | Comprendre, refactor, générer un bout précis                      |
| **Chat — Plan**            | IDE                         | Cadrer un gros chantier (rewrite, nouvelle feature transverse)    |
| **Chat — Agent**           | IDE                         | Exécuter un chantier multi-fichiers, lancer commandes, itérer     |
| **Copilot CLI** (`gh copilot`) | Terminal                | Générer/expliquer des commandes shell, git, `gh`, `az`, `docker`  |
| **Code Review**            | PR github.com               | Review automatique d'une PR (best practices, sécu, CodeQL)        |
| **Copilot Autofix**        | Alertes CodeQL sur PR       | Patch IA automatique pour les vulnérabilités détectées            |
| **Coding Agent**           | github.com                  | Déléguer une issue end-to-end                                     |
| **Azure SRE Agent**        | Azure portal                | Observer la prod, diagnostiquer, remédier                         |

## Patterns de prompts efficaces

1. **Rôle + contexte** au début de la session.
2. **Découper** un gros besoin en petits prompts incrémentaux.
3. Joindre **le bon contexte** : `#file`, `#selection`, `#changes`, `#problems`, `#fetch`.
4. **One-shot / few-shot** pour imposer un style.
5. Toujours **vérifier les tests** et les diffs avant `Keep`.
6. Dans le terminal : `gh copilot suggest` pour générer, `gh copilot explain` pour comprendre avant d'exécuter.

## Garde-fous

- **Revue humaine obligatoire** sur tout code généré, surtout sur les routes publiques et l'IaC.
- **Jamais de secret** (clé, token, mot de passe) dans un prompt ou un commit. Utilise OIDC + Key Vault.
- **Tests** en premier rempart : un test généré qui passe ne prouve pas que la feature est correcte, mais l'absence de test garantit qu'on régresse.
- **Autofix ≠ free pass** : toujours relire le patch proposé, surtout pour les vulnérabilités d'authz/business logic où le contexte métier compte.
- **Coût Azure** : pense à `az group delete -n rg-meal-calendar-dev --yes --no-wait` à la fin du workshop.

---

# Aller plus loin

- [github/awesome-copilot](https://github.com/github/awesome-copilot) — prompts, instructions et agents communautaires
- [Copilot Adventures](https://github.com/microsoft/CopilotAdventures) — petites quêtes ludiques
- [GitHub CLI manual](https://cli.github.com/manual/) — toutes les commandes `gh`
- [Using GitHub Copilot in the CLI](https://docs.github.com/copilot/github-copilot-in-the-cli/using-github-copilot-in-the-cli) — doc officielle `gh copilot`
- [About Copilot Autofix](https://docs.github.com/code-security/code-scanning/managing-code-scanning-alerts/about-autofix-for-codeql-code-scanning) — fonctionnement et limites
- [Mastering GitHub Copilot for Paired Programming](https://github.com/microsoft/Mastering-GitHub-Copilot-for-Paired-Programming)
- [Zero2Hero](https://github.com/Azure-Samples/zero2hero)
- [Writing great agents.md](https://github.blog/ai-and-ml/github-copilot/how-to-write-a-great-agents-md-lessons-from-over-2500-repositories/)
- [Doc Azure Container Apps](https://learn.microsoft.com/azure/container-apps/)
- [Doc OIDC GitHub ↔ Azure](https://learn.microsoft.com/azure/developer/github/connect-from-azure)

> Bravo, tu as terminé 🎉
>
> Tu maîtrises maintenant Copilot du clavier à la prod. À toi de jouer sur tes vrais projets — et n'oublie pas : **Copilot accélère les bons devs, il ne remplace pas le cerveau**.
