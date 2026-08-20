# RAGentic Backend — Agentic RAG Engine & Microservice

The core backend service for the **RAGentic** platform, built with **FastAPI**, **Google Gemini 2.5 Flash / Embedding-001**, and **Milvus 2.6.0**.

---

## 1. Architecture & Decision Layer

The backend is built around a deterministic **5-State Machine** (`state_machine.py`) that processes every incoming query through distinct operational stages:

```mermaid
flowchart TD
    Query([Query: POST /api/chat]) --> Router[Router: Gemini 2.5 Flash JSON Classifier]

    Router -->|"intent: direct"| DirectState[1. DIRECT State]
    Router -->|"intent: tool"| ToolState[2. TOOL_CALL State]
    Router -->|"intent: retrieve"| RetrieveState[3. RETRIEVE State]

    DirectState --> DirectLLM[Gemini General Synthesis]
    DirectLLM --> Response[ChatResponse: intent=direct, citations=[]]

    ToolState --> SafeTool[Safe AST Math Eval / UTC Date]
    SafeTool --> Response2[ChatResponse: intent=tool, citations=[]]

    RetrieveState --> MilvusHybrid[Milvus Native Hybrid Search]
    MilvusHybrid --> DenseVec[Dense ANN: embedding 3072d]
    MilvusHybrid --> SparseVec[Sparse BM25: sparse_vector Inverted Index]
    DenseVec & SparseVec --> RRF[Milvus Native RRFRanker k=60]

    RRF --> TopChunks[Top 5 Retrieved Chunks with s3_key & page_num]
    TopChunks --> StrictLLM[Grounded Evaluator: Gemini 2.5 Flash]

    StrictLLM -->|Output: DECLINE_OUT_OF_CORPUS| DeclineState[4. DECLINED State]
    StrictLLM -->|Output: Grounded Answer| CitationBuilder[5. Citation Builder]

    DeclineState --> RefusalMsg[Refusal Message: No Evidence in AWS Docs]
    RefusalMsg --> Response3[ChatResponse: intent=declined, citations=[]]

    CitationBuilder --> URLGen[Attach Presigned / Raw Streaming URLs]
    URLGen --> Response4[ChatResponse: intent=retrieve, citations=[...]]
```

---

## 2. Detailed Execution Pathways

### 1. `RETRIEVE` (AWS Cloud Documentation Hybrid RAG)
- **When Triggered**: Query relates to AWS services (EC2, S3, VPC, IAM, ECS, CloudWatch, Lambda, RDS, Route 53, etc.) or architecture blueprints.
- **Workflow**:
  1. `embedder.embed_query(query)` generates a 3072-dimensional vector (`models/gemini-embedding-001`).
  2. `store.hybrid_search_native()` sends dual `AnnSearchRequest` instances to Milvus:
     - Dense search on the `embedding` field (`IVF_FLAT`, Metric: `IP`).
     - Lexical search on the `sparse_vector` field (`SPARSE_INVERTED_INDEX`, Metric: `BM25`).
  3. Milvus fuses both candidate lists using native **Reciprocal Rank Fusion** (`RRFRanker(k=60)`).
  4. Top 5 chunks are provided to `gemini-2.5-flash` with the strict grounding instruction:
     > *"Answer using ONLY the provided AWS documentation context chunks. Cite sources as [1], [2]..."*
  5. The API maps each cited chunk to its `doc_name`, `page_num`, `chunk_text`, and presigned `/api/documents/raw?key=...` URL for inline in-browser PDF viewing.

### 2. `TOOL_CALL` (Autonomous Arithmetic & Time Utility)
- **When Triggered**: Query requests arithmetic computations (e.g. EC2 memory/vCPU calculations, pricing estimates) or current UTC date/time.
- **Workflow**:
  1. Router extracts tool name (`calculator` or `date`).
  2. Math queries are processed using Python's `ast.literal_eval` with strict node whitelisting (`Add`, `Sub`, `Mult`, `Div`, `Pow`, `BinOp`, `UnaryOp`). Arbitrary code execution or system calls are mathematically impossible.
  3. Returns immediate formatted result without unnecessary LLM hallucination risk or token cost.

### 3. `DIRECT` (Conversational & General Knowledge)
- **When Triggered**: General conversational greetings ("hello", "who are you?") or standard non-cloud programming questions.
- **Workflow**:
  1. Synthesized directly using `gemini-2.5-flash`.
  2. Avoids vector database lookups and zero citations are returned.

### 4. `DECLINED` (Strict Evidence Evaluation & Poison Pill Refusal)
- **When Triggered**: Out-of-domain questions (Mars science, crypto trading), non-AWS poison pills (chocolate chip cookie recipes), or unverified hallucination probes (non-existent AWS services).
- **Workflow**:
  1. The LLM evaluator detects the retrieved documentation contains insufficient evidence.
  2. Adhering to the strict prompt, the LLM emits the token `DECLINE_OUT_OF_CORPUS`.
  3. State machine transitions to `DECLINED` and outputs:
     > *"I don't have reliable information about this in the indexed AWS documentation and knowledge base. Please ask questions related to the supported AWS services."*
  4. Clears all citations to prevent misleading references.

---

## 3. Milvus Collection Schema (`ragentic_chunks`)

The collection manages both dense embeddings and native BM25 sparse vectors in a single unified schema:

| Field Name | Data Type | Description | Index |
|---|---|---|---|
| `id` | `VARCHAR(256)` | Primary Key (`{doc_id}_chunk_{index}`) | — |
| `doc_id` | `VARCHAR(64)` | UUID assigned to the source PDF document | — |
| `doc_name` | `VARCHAR(512)` | Original filename (e.g. `AWS_VPC_Virtual_Private_Cloud.pdf`) | — |
| `s3_key` | `VARCHAR(1024)` | Storage object path (`docs/{doc_id}/{filename}`) | — |
| `chunk_index` | `INT64` | Sequential chunk index within the document | — |
| `page_num` | `INT64` | 1-indexed page number where chunk text appears | — |
| `chunk_text` | `VARCHAR(65535)` | Raw chunk text (Analyzer & Match enabled) | — |
| `sparse_vector` | `SPARSE_FLOAT_VECTOR` | Auto-generated BM25 sparse vector | `SPARSE_INVERTED_INDEX` (BM25) |
| `embedding` | `FLOAT_VECTOR(3072)` | Dense vector from `gemini-embedding-001` | `IVF_FLAT` (Metric: `IP`) |

> **Native BM25 Function**: Milvus attaches a built-in `Function(FunctionType.BM25)` mapping `chunk_text` $\rightarrow$ `sparse_vector`. Upserting text automatically generates sparse term weights natively inside Milvus.

---

## 4. API Endpoints

### Chat & State Machine
- **`POST /api/chat`**: Main agent invocation endpoint.
  - **Request**: `{"message": "string", "thread_id": "string | null"}`
  - **Response**: `{"thread_id": "...", "message_id": "...", "answer": "...", "intent": "retrieve|direct|tool|declined", "citations": [...], "latency_ms": 1200.5, "token_count": 1840}`
- **`GET /api/threads`**: Lists all active conversation threads and metadata.
- **`GET /api/threads/{thread_id}`**: Retrieves message history and citations for a specific thread.

### Document Storage & Ingestion
- **`POST /api/documents/ingest`**: Multipart file upload (`.pdf`) to chunk, embed, and index into Milvus + S3.
- **`GET /api/documents/raw?key={s3_key}`**: Streams PDF with `Content-Disposition: inline` and CORS headers for in-browser modal viewing.
- **`GET /api/documents`**: Lists all indexed documents.

### Observability & Health
- **`GET /health`**: Verifies connectivity to Milvus and S3/MinIO.
- **`GET /metrics`**: Exposes average retrieval latency, query counts by intent, total token spend, and document count.

---

## 5. Testing & Verification

Run the full PyTest suite:
```bash
cd backend
source .venv/bin/activate
pytest -v
```

### Test Suite Structure:
- `tests/test_retriever.py`: Validates RRF monotonicity, multi-list score fusion, and hybrid retrieval pipeline.
- `tests/test_agent.py`: Validates AST safe calculator evaluation, date tool, intent router, and state transitions.
- `tests/test_adversarial.py`: Tests 4 out-of-domain and poison pill queries to verify explicit `declined` intent and absence of hallucinations.
