# RAGentic — Quick Kick-Start Guide

A step-by-step walkthrough to set up, ingest data, build, test, and run the **Agentic RAG Microservice** on your local machine.

---

## 1. Prerequisites

Before getting started, make sure you have the following installed on your system:

| Dependency | Minimum Version | Notes |
|---|---|---|
| **Python** | `3.12+` | Backend FastAPI application & ingestion scripts |
| **Node.js** | `v20+` (or `v24+`) | Frontend Next.js 15 application |
| **npm** | `v10+` | Node package manager |
| **Milvus** | `v2.4+` / `v2.6.0` | Running as a system service or container on `localhost:19530` |
| **Gemini API Key** | — | Google AI Studio key for embeddings & LLM generation |

---

## 2. Environment Configuration

1. Navigate to the `backend/` directory:
   ```bash
   cd backend
   ```
2. Copy the sample environment file:
   ```bash
   cp .env.example .env
   ```
3. Open `.env` and configure your settings:
   ```env
   # Google Gemini API
   GEMINI_API_KEY=your_actual_gemini_api_key_here
   EMBEDDING_MODEL=models/gemini-embedding-001
   LLM_MODEL=gemini-2.5-flash

   # Milvus Vector Store
   MILVUS_HOST=localhost
   MILVUS_PORT=19530
   MILVUS_COLLECTION=ragentic_chunks

   # S3 / MinIO Storage (Optional for local dev)
   S3_BUCKET=ragentic-docs
   S3_ENDPOINT_URL=http://localhost:9000
   AWS_REGION=us-east-1
   AWS_ACCESS_KEY_ID=minioadmin
   AWS_SECRET_ACCESS_KEY=minioadmin

   # RAG Parameters
   BM25_TOP_K=20
   DENSE_TOP_K=20
   RRF_K=60

   # Application
   ENV=local
   LOG_LEVEL=INFO
   CORPUS_DIR=./corpus
   ```

---

## 3. Backend Setup & Corpus Ingestion

### Step 3.1: Create & Activate Virtual Environment
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3.2: Install Python Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 3.3: Verify Milvus Status
Ensure your Milvus service is active and healthy:
```bash
curl -s http://localhost:9091/healthz
# Expected output: OK
```

### Step 3.4: Ingest Document Corpus into Milvus
Place your PDF files in `backend/corpus/` (e.g. the 15 AWS service guides), then run:
```bash
python scripts/ingest_corpus.py
```
> **What this does automatically:**
> - Connects to your Milvus instance on `localhost:19530`.
> - Creates the collection schema with dense vectors (`3072-dim`) + native BM25 sparse vectors (`DataType.SPARSE_FLOAT_VECTOR` + `FunctionType.BM25`).
> - Chunks each PDF (800 chars, 150 overlap) with page numbers and document IDs.
> - Computes Gemini embeddings and indexes all chunks in Milvus.

### Step 3.5: Run Automated Tests
Verify all 15 unit, retriever, and adversarial prompt tests pass:
```bash
pytest -v
```

### Step 3.6: Start the FastAPI Backend Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
- **Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)
- **Metrics Endpoint**: [http://localhost:8000/metrics](http://localhost:8000/metrics)

---

## 4. Frontend Setup & Build

Open a **new terminal window** and navigate to `frontend/`:

### Step 4.1: Install Node Dependencies
```bash
cd frontend
npm install
```

### Step 4.2: Build the Production Next.js Bundle
```bash
npm run build
```
*(Confirms TypeScript types, static pages, and standalone bundle compile without error.)*

### Step 4.3: Start the Frontend Application
For development (with hot-reloading):
```bash
npm run dev
```
Or to run the compiled production server:
```bash
npm start
```
Open **[http://localhost:3000](http://localhost:3000)** in your web browser.

---

## 5. Testing the Application

Once both frontend and backend are running, try the following test queries in the web UI at `http://localhost:3000`:

### 1. Grounded AWS Document QA (Hybrid Retrieval + Citations)
- **Query**: *"How does Amazon VPC route traffic through an Internet Gateway and NAT Gateway?"*
- **Expected Behavior**:
  - Intent pill: `retrieved`
  - Returns structured answer referencing `[1] AWS_VPC_Virtual_Private_Cloud.pdf`.
  - Clicking the citation chip opens the **Citation Modal** showing the retrieved chunk snippet and the embedded PDF viewer navigated to the source page.

### 2. Autonomous Tool Execution (Math Calculator)
- **Query**: *"Calculate (128 * 1024) / 16"*
- **Expected Behavior**:
  - Intent pill: `tool used`
  - Returns `Tool result: 8192.0`.

### 3. Adversarial / Out-of-Domain Refusal
- **Query**: *"What is the baking time for chocolate chip cookies?"*
- **Expected Behavior**:
  - Intent pill: `declined`
  - Returns explicit refusal: *"I don't have reliable information about this in the indexed AWS documentation and knowledge base. Please ask questions related to the supported AWS services."*

---

## 6. Alternative: Running with Docker Compose (Full Stack)

If you prefer running all services (Frontend, Backend, Milvus, MinIO, Etcd) in isolated containers with a single command:

```bash
export GEMINI_API_KEY="your-gemini-api-key"
docker compose -f infra/docker-compose.yml up --build
```

---

## 7. Project Directory Cheatsheet

```text
RAGentic/
├── backend/
│   ├── app/
│   │   ├── agent/         # State machine, router, tools, and Gemini LLM client
│   │   ├── api/           # FastAPI routes (/api/chat, /api/documents, /health, /metrics)
│   │   ├── rag/           # Hybrid retriever, embedder, ingestor, Milvus store
│   │   └── storage/       # S3 / MinIO client integration
│   ├── corpus/            # PDF documents to be indexed
│   ├── scripts/           # Ingestion script (ingest_corpus.py)
│   ├── tests/             # PyTest test suite (unit + adversarial)
│   ├── Dockerfile         # Multi-stage non-root container
│   └── requirements.txt   # Python dependencies
├── frontend/
│   ├── src/               # Next.js 15 App router, components, styles, hooks
│   ├── Dockerfile         # Standalone multi-stage Next.js container
│   └── package.json
├── infra/
│   ├── docker-compose.yml # 1-command local cluster
│   └── terraform/         # AWS ECS Fargate, ALB, VPC, and IAM IaC modules
├── .github/workflows/     # CI/CD pipeline (lint/test -> build -> push)
├── KICK_START.md          # This setup guide
└── README.md              # Complete architecture & design documentation
```
