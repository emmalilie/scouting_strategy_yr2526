# UCLA Tennis Full-Stack Dashboard

React frontend + FastAPI backend dashboard 

## Structure
```
dashboard/
├── backend/           # FastAPI server
├── frontend/          # React app
├── start.py          # Data scraping functions
└── start_dashboard.sh # Startup script
```

## Quick Start
```bash
./start_dashboard.sh
```

## Manual Setup

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
python -m uvicorn main:app --reload --port 8000

```

### Frontend
```bash
cd frontend
npm install
npm start
```

## Features
- **Live data**: Scrapes UCLA tennis data in real-time
- **REST API**: FastAPI backend with CORS enabled
- **Interactive UI**: React frontend with data tables and performance charts
- **Performance tracking**: Cumulative win/loss visualization

## Endpoints
- `GET /roster` - Team roster with stats
- `GET /schedule` - Current season schedule
- `GET /seasons` - Available seasons
- `GET /seasons/{season}` - Specific season data with performance metrics