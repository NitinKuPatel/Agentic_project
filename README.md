# Agentic AI Knowledge-Base Bot

## Overview
This is an Enterprise-Grade Agentic AI Knowledge-Base Assistant, built with FastAPI, MongoDB, FAISS, and Redis. It focuses on correctness, auditability, and permission-aware retrieval.

## Prerequisites
- Python 3.10+
- MongoDB (running locally or addressable)
- Redis (running locally or addressable)

## Setup

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configuration**
   Copy `.env.example` to `.env` (already done if using provided files) and update values if needed.
   
   Ensure:
   - `MONGODB_URI` points to your Mongo instance.
   - `REDIS_URL` points to your Redis instance.
   - `STORAGE_TYPE` is set to "local" for now.

3. **Running the Application**
   ```bash
   uvicorn app.main:app --reload
   ```

4. **API Documentation**
   Visit `http://localhost:8000/docs` to see the Swagger UI.

## Architecture Highlights
- **FastAPI**: Main gateway and orchestrator.
- **MongoDB**: Stores document metadata, versions, and audit logs.
- **FAISS**: Local vector index for embeddings.
- **Redis**: Caching and rate limiting.
- **Local Storage**: Mimics object storage for document files.

## Next Steps
- Implement the actual `AgentOrchestrator` in `app/orchestrator/agent.py`.
- Connect the `query` endpoint to the orchestrator.
- Implement the ingestion pipeline for documents.
