# Tennis Dashboard

Universal tennis team dashboard with React frontend and FastAPI backend.

## Quick Start

```bash
npm start
```

This starts both backend (port 8000) and frontend (port 3000) automatically.

## Structure

```
dashboard/
├── backend/           # FastAPI server
│   ├── main.py       # API endpoints
│   ├── start.py      # Web scraping
│   └── requirements.txt
├── frontend/         # React app
├── config/           # School configuration
├── data/            # CSV/Excel data files
├── templates/       # Templates for new schools
└── package.json     # Root npm scripts
```

## Features

- Team roster with player statistics
- Current season schedule
- Historical results with performance charts
- Multi-school support via configuration

## Setup for Other Schools

See [SETUP_GUIDE.md](SETUP_GUIDE.md) for instructions.