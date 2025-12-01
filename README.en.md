# POW_SE - Software Engineering Knowledge Graph Platform

A multimodal knowledge graph incremental construction platform for the "Software Engineering" course. It utilizes Neo4j to build a knowledge graph of course knowledge points, supporting graph visualization, knowledge querying, and intelligent Q&A.

## Contributors

1. Ye Yu
2. Hongbang Zhang
3. Jingwen Zhang
4. Jingyi Wang
5. Jiayi Li
6. Shaohua Huang
7. Tianshuo Zhang
8. Fangbo Liu
9. Xin Chen

## Technology Stack

### Frontend Stack
- **Framework**: Vue 3 + TypeScript + Vite
- **UI Library**: Naive UI
- **Visualization**: Cytoscape.js + ECharts
- **State Management**: Pinia
- **Routing**: Vue Router 4
- **Internationalization**: vue-i18n

### Backend Stack
- **Framework**: FastAPI + Python
- **Graph Database**: Neo4j 5.x
- **Cache**: Redis
- **AI Integration**: OpenAI API + Custom GraphRAG Algorithm
- **Task Queue**: RQ (Redis Queue)

### Infrastructure
- **Containerization**: Docker + Docker Compose
- **Database**: Neo4j + Redis
- **Deployment**: Supports local development and containerized deployment

## Project Structure
```lua
POW_SE/
├── app/vue/                    # Vue 3 Frontend Project
│   ├── src/
│   │   ├── views/              # Page Components
│   │   │   ├── Dashboard.vue   # Dashboard
│   │   │   ├── Upload.vue      # Document Upload
│   │   │   ├── Graph.vue       # Graph Visualization
│   │   │   ├── Query.vue       # Knowledge Query
│   │   │   └── Status.vue      # Processing Status
│   │   ├── components/         # Shared Components
│   │   ├── api/                # API Services
│   │   ├── stores/             # State Management
│   │   └── i18n/               # Internationalization
│   ├── package.json
│   └── vite.config.ts
├── server/                     # FastAPI Backend Project
│   ├── main.py                 # Application Entry Point
│   ├── routes/                 # API Routes
│   │   ├── upload.py           # Document Upload
│   │   ├── ingest.py           # Knowledge Extraction
│   │   ├── graph.py            # Graph Query
│   │   └── knowledge_card.py   # Knowledge Cards
│   ├── services/               # Business Services
│   │   ├── parser.py           # Document Parsing
│   │   ├── extractor.py        # Knowledge Extraction
│   │   ├── graph_service.py    # Graph Services
│   │   └── linker.py           # Entity Linking
│   ├── graphrag/               # GraphRAG Module
│   │   ├── stages/             # 8 Construction Stages
│   │   ├── models/             # Data Models
│   │   ├── config/             # Configuration Files
│   │   └── utils/              # Utility Functions
│   ├── infra/                  # Infrastructure
│   │   ├── neo4j_client.py     # Neo4j Client
│   │   └── ai_providers.py     # AI Service Providers
│   ├── models/                 # Data Models
│   └── tests/                  # Test Code
├── docker-compose.yml          # Docker Compose Configuration
├── uploads/                    # Upload Directory
└── data/                       # Data Files
```

## Quick Start

### Prerequisites

- Python 3.8+
- Node.js 14+
- Neo4j 5.x
- Redis 6.x

### Install Dependencies

**Backend Dependencies:**
```bash
cd server
pip install -r requirements.txt
```

**Frontend Dependencies:**
```bash
cd app/vue
npm install
```

### Start Services

**Start Backend:**
```bash
cd server
python main.py
# Or use PowerShell script
.\start-api.ps1
```

**Start Frontend:**
```bash
cd app/vue
npm run dev
# Or use PowerShell script
.\start-frontend.ps1
```

### Access the Application

- Frontend Application: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Features

- 📊 **Knowledge Graph Visualization**: Interactive graph display using Cytoscape.js
- 🔍 **Intelligent Search**: Supports keyword search and semantic queries
- 📚 **Multimodal Resources**: Links to learning resources like documents, videos, and code
- 🤖 **AI Knowledge Extraction**: Knowledge entity recognition based on GraphRAG algorithm
- 🔄 **Incremental Construction**: Supports continuous updating and expansion of the knowledge graph
- 🎯 **Smart Q&A**: Intelligent Q&A system based on knowledge graph

## Core Modules

### GraphRAG Knowledge Graph Construction
- **Stage 0**: Semantic Chunking - Intelligent document segmentation
- **Stage 1**: Coreference Resolution - Entity reference resolution
- **Stage 2**: Entity Linking - Concept identification and linking
- **Stage 3**: Claim Extraction - Knowledge triplet extraction
- **Stage 4**: Theme Building - Topic clustering and summarization
- **Stage 5**: Predicate Governance - Relationship normalization
- **Stage 6**: Idempotent Storage - Data persistence
- **Stage 7**: GraphRAG Retrieval - Intelligent retrieval system

### Knowledge Card Management
- Concept node management
- Relationship connection management
- Evidence backtracking support
- Incremental update mechanism

## Development Guide

### Backend Development

The backend uses the FastAPI framework, following RESTful API design principles:

```python
# Example API endpoint
@app.get("/api/graph/nodes")
async def get_graph_nodes(limit: int = 100):
    """Retrieve graph node data"""
    return neo4j_client.get_nodes(limit=limit)
```

### Frontend Development

The frontend uses Vue 3 Composition API and component-based development:

```vue
<template>
  <GraphVisualization :graph-data="graphData" />
</template>

<script setup>
import { ref } from 'vue'
const graphData = ref(null)
</script>
```

## Deployment

Use Docker Compose for containerized deployment:

```bash
docker-compose up -d
```

Services include:
- **Frontend**: Vue application (port 8788)
- **Backend**: FastAPI application (port 8000)
- **Database**: Neo4j graph database
- **Cache**: Redis caching service

## Testing

The project includes a complete testing framework:

```bash
# Run unit tests
cd server
pytest tests/

# Run GraphRAG module tests
pytest tests/graphrag/
```

## Contributing

Issues and Pull Requests are welcome for improving the project!

## License

MIT License