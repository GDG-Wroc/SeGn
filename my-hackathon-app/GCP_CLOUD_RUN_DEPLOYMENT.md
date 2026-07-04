# Deployment na Google Cloud Run

Ten projekt zawiera 5 kontenerow deployowanych jako osobne uslugi Cloud Run:

- `my-hackathon-app-frontend` - Angular serwowany przez nginx
- `my-hackathon-app-backend` - FastAPI
- `mcp-triz` - TRIZ MCP server
- `mcp-analogy` - Design by Analogy MCP server
- `triz-embeddings` - Ollama z modelem `embeddinggemma:300m` dla TRIZ

## Pliki env w repo

Przyklady konfiguracji sa w:

- `apps/my-hackathon-app/.env.example`
- `apps/src/backend/.env.example`
- `apps/mcp_triz/.env.example`
- `apps/mcp_triz/embeddings/.env.example`
- `apps/mcp_analogy/.env.example`

Lokalne `.env` nie powinny trafic do repo. W Cloud Run wartosci ustawiane sa przez `cloudbuild.yaml` jako zmienne runtime albo, dla sekretow, przez Secret Manager.

## 1. Wymagania w GCP

Wybierz projekt i region:

```bash
export PROJECT_ID="twoj-projekt"
export REGION="europe-west1"
export REPOSITORY="hackathon"
gcloud config set project "$PROJECT_ID"
```

Wlacz wymagane API:

```bash
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com
```

Utworz repozytorium Docker w Artifact Registry:

```bash
gcloud artifacts repositories create "$REPOSITORY" \
  --repository-format=docker \
  --location="$REGION"
```

Nadaj Cloud Build uprawnienia do deployowania Cloud Run:

```bash
PROJECT_NUMBER="$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')"

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"
```

## 2. Pierwszy deploy

Pierwszy deploy buduje obrazy i tworzy uslugi. Na tym etapie mozna jeszcze nie znac URL-i innych uslug, wiec po deployu trzeba je pobrac i ustawic w drugim przebiegu.

```bash
gcloud builds submit \
  --config=cloudbuild.yaml \
  --substitutions=_REGION="$REGION",_REPOSITORY="$REPOSITORY"
```

## 3. Pobierz URL-e uslug

```bash
export FRONTEND_URL="$(gcloud run services describe my-hackathon-app-frontend --region "$REGION" --format='value(status.url)')"
export BACKEND_URL="$(gcloud run services describe my-hackathon-app-backend --region "$REGION" --format='value(status.url)')"
export TRIZ_MCP_URL="$(gcloud run services describe mcp-triz --region "$REGION" --format='value(status.url)')/mcp"
export ANALOGY_MCP_URL="$(gcloud run services describe mcp-analogy --region "$REGION" --format='value(status.url)')/mcp"
export EMBEDDING_SERVICE_URL="$(gcloud run services describe triz-embeddings --region "$REGION" --format='value(status.url)')/v1"
```

## 4. Drugi deploy z konfiguracja runtime

Podstaw URL-e tak, aby frontend znal backend, backend znal oba MCP, a TRIZ MCP znal embeddings:

```bash
gcloud builds submit \
  --config=cloudbuild.yaml \
  --substitutions=_REGION="$REGION",_REPOSITORY="$REPOSITORY",_API_BASE_URL="$BACKEND_URL",_TRIZ_MCP_URL="$TRIZ_MCP_URL",_ANALOGY_MCP_URL="$ANALOGY_MCP_URL",_EMBEDDING_SERVICE_URL="$EMBEDDING_SERVICE_URL"
```

Jezeli korzystasz z zewnetrznego lub lokalnie hostowanego API LLM zgodnego z OpenAI, dodaj tez odpowiednie podstawienia:

```bash
,_LOCAL_LLM_BASE_URL="https://...",_LOCAL_LLM_MODEL="model-name",_TRIZ_LLM_BASE_URL="https://...",_TRIZ_LLM_MODEL="model-name",_ANALOGY_RESPONSE_LLM_BASE_URL="https://...",_ANALOGY_RESPONSE_LLM_MODEL="model-name",_ANALOGY_LLM_BASE_URL="https://...",_ANALOGY_LLM_MODEL="model-name"
```

Sekrety, takie jak klucze API, ustawiaj przez Secret Manager i `--set-secrets`, a nie wprost w `cloudbuild.yaml`.

Minimalne wartosci, ktore trzeba podmienic po pierwszym deployu:

- `_API_BASE_URL` - URL uslugi `my-hackathon-app-backend`
- `_TRIZ_MCP_URL` - URL uslugi `mcp-triz` zakonczony `/mcp`
- `_ANALOGY_MCP_URL` - URL uslugi `mcp-analogy` zakonczony `/mcp`
- `_EMBEDDING_SERVICE_URL` - URL uslugi `triz-embeddings` zakonczony `/v1`

Opcjonalne wartosci dla LLM:

- `_LOCAL_LLM_BASE_URL` i `_LOCAL_LLM_MODEL` - wspolny fallback backendu
- `_TRIZ_LLM_BASE_URL` i `_TRIZ_LLM_MODEL` - override dla odpowiedzi TRIZ
- `_ANALOGY_RESPONSE_LLM_BASE_URL` i `_ANALOGY_RESPONSE_LLM_MODEL` - override dla odpowiedzi analogii w backendzie
- `_ANALOGY_LLM_BASE_URL` i `_ANALOGY_LLM_MODEL` - LLM uzywany wewnatrz `mcp-analogy`
- `ANALOGY_LLM_API_KEY` - ustaw przez Secret Manager, jezeli endpoint LLM wymaga klucza

## 5. Weryfikacja

Sprawdz health backendu:

```bash
curl "$BACKEND_URL/"
```

Sprawdz endpoint MCP:

```bash
curl "$TRIZ_MCP_URL"
curl "$ANALOGY_MCP_URL"
```

Otworz frontend:

```bash
echo "$FRONTEND_URL"
```

## 6. Uwagi produkcyjne

- Obecnie uslugi sa deployowane z `--allow-unauthenticated`, co jest wygodne na hackathon. Produkcyjnie warto ograniczyc dostep do backendu i MCP przez IAM albo API Gateway.
- `triz-embeddings` buduje obraz z modelem w srodku, wiec pierwszy build moze trwac dlugo i obraz bedzie duzy.
- Cloud Run domyslnie skaluje do zera. Dla szybszych odpowiedzi ustaw `--min-instances=1` na backendzie, MCP i embeddings.
- Dla `triz-embeddings` moze byc potrzebna wyzsza pamiec/CPU albo GPU, zależnie od limitow projektu i regionu.
- Po zmianie URL-i uslug uruchom ponownie drugi deploy, aby nadpisac zmienne runtime.
