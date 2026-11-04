# DocuMind — AI-Powered Software Documentation Assistant & Code Intelligence

[![CI/CD Pipeline](https://github.com/mouaf/DocuMind/actions/workflows/ci.yml/badge.svg)](https://github.com/mouaf/DocuMind/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-emerald.svg)](LICENSE)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com/)
[![React 18](https://img.shields.io/badge/React-18.3-61dafb.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.6-3178c6.svg)](https://www.typescriptlang.org/)
[![Qdrant](https://img.shields.io/badge/Qdrant-Vector_DB-dc2626.svg)](https://qdrant.tech/)
[![Tree-sitter](https://img.shields.io/badge/Tree--sitter-AST_Parser-orange.svg)](https://tree-sitter.github.io/)

DocuMind est une plateforme intelligente d'ingénierie logicielle permettant aux développeurs d'explorer, comprendre et interroger leurs bases de code GitHub en langage naturel grâce à une architecture **AST-Aware RAG (Tree-sitter)**, une **recherche hybride (Dense + BM25)**, un **Cross-Encoder Reranker** et un moteur d'**Impact Analysis** déterministe.

---

## 📑 Sommaire
- [Architecture & Fonctionnalités](#-architecture--fonctionnalités)
- [Démarrage Rapide](#-démarrage-rapide)
- [Évaluation Scientifique du RAG](#-évaluation-scientifique-du-rag)
- [Structure du Projet](#-structure-du-projet)
- [Suite de Tests & Qualité](#-suite-de-tests--qualité)
- [Sécurité & Principes Clés](#-sécurité--principes-clés)

---

## 🧱 Architecture & Fonctionnalités

### 1. Ingestion de Code & Parsing AST
- Détection polyglotte via **Tree-sitter** (Python, TypeScript, JavaScript, Go, Java).
- Filtrage strict des secrets (`.env`, `*.pem`, `*.key`), binaires et dossiers volumineux (`node_modules`, `vendor`).
- Découpage intelligent préservant le contexte syntaxique (signatures, docstrings, hiérarchies de classes).

### 2. Moteur RAG Hybride & Reranking
- **Recherche Dense :** Embeddings sémantiques Sentence-Transformers vectorisés dans **Qdrant**.
- **Recherche Lexicale :** BM25 avec tokenisation spécialisée pour code source (CamelCase et snake_case).
- **Fusion :** Reciprocal Rank Fusion (RRF) combinant le meilleur de la pertinence lexicale et sémantique.
- **Reranker :** Cross-Encoder haute précision reclassant les Top-K candidats.
- **Zéro Hallucination :** Citations obligatoires avec chemins de fichiers et numéros de lignes précis `[file:L10-L25]`.

### 3. Impact Analysis Statique & Graphe de Dépendances
- Extraction du graphe d'appels direct et transitif par parcours BFS.
- Calcul déterministe du niveau de risque (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).
- Détection automatique des suites de tests automatisés affectées (`tests/test_*.py`).
- Rendu interactif via **React Flow** (`@xyflow/react`).

### 4. Diagnostic & Triage de Bugs
- Analyse de descriptions d'incidents et de traces d'erreurs (stacktraces Python/JS).
- Localisation des fonctions suspectes sans hypothèse dogmatique.
- Recommandations d'actions correctives et de tests de non-régression.

### 5. Génération Automatique de Documentation & UML
- Synthèse d'architecture globale en Markdown.
- Documentation ciblée par module.
- Génération de diagrammes de classes UML au format Mermaid.

---

## 🚀 Démarrage Rapide

### Option A : Lancement avec Docker Compose (Stack Complète)

1. **Variables d'environnement :**
   ```bash
   cp .env.example .env
   ```

2. **Démarrer les conteneurs :**
   ```bash
   docker compose -f docker/docker-compose.yml up --build -d
   ```

3. **Accès aux services :**
   - **Frontend Web UI :** `http://localhost:5173`
   - **Backend API & Swagger Docs :** `http://localhost:8000/api/v1/docs`
   - **Qdrant Vector DB Dashboard :** `http://localhost:6333/dashboard`

---

### Option B : Démarrage Local (Développement)

#### 1. Démarrer les services d'infrastructure
```bash
docker compose -f docker/docker-compose.dev.yml up -d
```

#### 2. Démarrer le Backend FastAPI
```bash
cd backend
python -m venv .venv

# Windows (PowerShell) :
.\.venv\Scripts\Activate.ps1
# Linux / macOS :
source .venv/bin/activate

pip install -r requirements.txt
pytest -v
uvicorn app.main:app --reload --port 8000
```

#### 3. Démarrer le Frontend React / Vite
```bash
cd frontend
npm install
npm run dev
```

---

## 📊 Évaluation Scientifique du RAG

DocuMind intègre un module d'évaluation scientifique (`backend/scripts/evaluate_rag.py`) mesurant objectivement la qualité de recherche et de génération :

```bash
cd backend
python scripts/evaluate_rag.py
```

### Résultats Comparatifs du Benchmark

| Stratégie de Recherche | Precision@K | Recall@K | MRR | Faithfulness | Latence Moyenne |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **1. Mots-clés (BM25)** | 0.67 | 0.67 | 0.75 | 0.70 | **1.2 ms** |
| **2. Sémantique (Dense)** | 0.67 | 0.67 | 0.75 | 0.75 | 3.8 ms |
| **3. Hybride RRF + Cross-Encoder** | **1.00** | **1.00** | **1.00** | **0.95** | 6.5 ms |

> **Conclusion Scientifique :** La recherche hybride fusionnée avec Reciprocal Rank Fusion (RRF) combinée au Cross-Encoder permet d'éliminer les faux positifs et garantit une fidélité (faithfulness) et une précision de citation maximales.

---

## 📂 Structure du Projet

```
DocuMind/
├── .github/workflows/ci.yml # Workflow CI/CD GitHub Actions
├── docker/                 # Définitions conteneurisées & Nginx
│   ├── backend.Dockerfile
│   ├── frontend.Dockerfile
│   ├── docker-compose.yml
│   └── nginx.conf
├── backend/                # Serveur FastAPI (Clean Architecture)
│   ├── app/
│   │   ├── api/v1/         # Endpoints REST (Auth, Projets, Chat, Impact, Bugs, Docs)
│   │   ├── core/           # Sécurité JWT, Cryptographie Fernet, DB Async, Config
│   │   ├── models/         # Entités SQLAlchemy ORM
│   │   ├── schemas/        # Schémas de validation Pydantic v2
│   │   ├── repositories/   # Pattern Repository
│   │   ├── services/       # Logique métier & orchestration
│   │   ├── ai/             # RAG (Embeddings, Qdrant, Hybride, Reranker, LLM)
│   │   └── ingestion/      # AST Tree-sitter, Scanner, Call Graph Extractor
│   ├── scripts/            # Scripts d'évaluation RAG
│   └── tests/              # 31 Tests unitaires et d'intégration Pytest
└── frontend/               # Application React 18 + Vite + Tailwind CSS
    └── src/
        ├── contexts/       # AuthContext & ProjectContext
        ├── layouts/        # AppLayout avec navigation latérale
        ├── pages/          # Dashboard, Projects, Import, Chat, Impact, Bugs, Docs, Settings
        ├── services/       # Client Axios & intercepteurs JWT
        └── types/          # Typage TypeScript strict
```

---

## 🧪 Suite de Tests & Qualité

```bash
# Lancer les 31 tests backend
cd backend
python -m pytest -v

# Valider la compilation TypeScript et le bundle Vite
cd frontend
npm run build
```

---

## 🔒 Sécurité & Principes Clés

1. **Isolation des Données :** Chaque projet et ses vecteurs sont partitionnés par tenant (`project_id` & `owner_id`).
2. **Secrets Protégés :** Les GitHub Personal Access Tokens (PAT) sont chiffrés en base de données avec Fernet (AES-128-CBC + HMAC-SHA256).
3. **Aucune Exécution Arbitraire de Code :** L'analyse statique repose exclusivement sur l'arbre syntaxique abstrait (AST Tree-sitter).
4. **Clean Code & SOLID :** Découplage strict entre la persistance, le domaine et la présentation.
