#!/bin/bash

echo "Starting UCLA Tennis Dashboard..."

# Start backend
echo "Starting FastAPI backend..."
cd backend
python3 -m uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!

# Start frontend
echo "Starting React frontend..."
cd ../frontend
npm start &
FRONTEND_PID=$!

echo "Backend running on http://localhost:8000"
echo "Frontend running on http://localhost:3000"
echo "Press Ctrl+C to stop both servers"

# Wait for user interrupt
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait