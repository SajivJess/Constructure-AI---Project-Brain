---
title: Constructure AI
emoji: 🏗️
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
license: mit
---

# Constructure AI - Project Brain

RAG-based construction document Q&A system with hybrid search, caching, and conflict detection.

## Features
- 🔍 Hybrid Search (BM25 + FAISS)
- 📊 Analytics Dashboard
- ⚡ Response Caching
- 🔄 Conflict Detection
- 📄 Document Export

## Tech Stack
- FastAPI + Uvicorn
- Google Gemini AI
- FAISS Vector Database
- Sentence Transformers
- BM25 Search

## API Endpoints
- POST /chat - Ask questions about documents
- POST /upload - Upload construction documents
- GET /documents/list - List all documents
- POST /extract - Extract structured data
- POST /evaluate - Evaluate responses
- GET /analytics - Get system analytics
- POST /detect-conflicts - Detect document conflicts
- GET /health - Health check

## Environment
- Python 3.11
- Port 7860
