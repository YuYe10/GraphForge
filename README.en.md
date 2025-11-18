**Software Engineering Knowledge Graph Platform**

A multimodal knowledge graph incremental construction platform for the "Software Engineering" course. It utilizes Neo4j to build a knowledge graph of course knowledge points, supporting graph visualization and querying knowledge points to access related learning content and digital resources.

## Contributors

1. Ye Yu
2. Hongbang Zhang
3. Jingwen Zhang
4. Jingyi Wang
5. Jiayi Li

## Technology Stack

- **Frontend**: Vue 3 + Vite + D3.js
- **Backend**: FastAPI + Python
- **Database**: Neo4j (Graph Database) + MariaDB (Relational Database)
- **AI Framework**: PyTorch + Transformers

## Project Structure
```lua
software_engineering_kg_platform/
├── backend/                    # FastAPI Backend Project
│   └── main.py                # Application Entry Point
├── frontend/                   # Vue.js Frontend Project
├── kg_builder/                 # Knowledge Graph Builder Module (Can be independent)
├── database/                  # Database Related
├── docs/                      # Project Documentation
└── docker-compose.yml         # Docker Compose for services like Neo4j, MariaDB
```

## Quick Start

### Prerequisites

- Python 3.8+
- Node.js 14+
- Neo4j 5.x
- MariaDB 10.x

### Install Dependencies

**Backend Dependencies:**
```bash
cd backend
pip install -r requirements.txt
```

**Frontend Dependencies:**
```bash
cd frontend
npm install
```

### Start Services

**Start Backend:**
```bash
cd backend
python main.py
# Or use the batch file
start_backend.bat
```

**Start Frontend:**
```bash
cd frontend
npm run dev
# Or use the batch file
start_frontend.bat
```

### Access the Application

- Frontend Application: http://localhost:8080
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Features

- 📊 **Knowledge Graph Visualization**: Interactive graph display using D3.js 
- 🔍 **Intelligent Search**: Supports keyword search and semantic queries 
- 📚 **Multimodal Resources**: Links to learning resources like documents, videos, and code 
- 🤖 **AI Knowledge Extraction**: Knowledge entity recognition based on BERT models 
- 🔄 **Incremental Construction**: Supports continuous updating and expansion of the knowledge graph 

## Development Guide

### Backend Development

The backend uses the FastAPI framework, following RESTful API design principles:

```python
# Example API endpoint
@app.get("/api/knowledge-graph/initial")
async def get_initial_graph():
    """Retrieve initial knowledge graph data"""
    return neo4j_service.get_initial_graph()
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

## Contributing

Issues and Pull Requests are welcome for improving the project!

## License

MIT License