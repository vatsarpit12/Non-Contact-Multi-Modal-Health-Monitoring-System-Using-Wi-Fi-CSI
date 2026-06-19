#!/bin/bash

# Health Monitoring System - Complete Startup Script
echo "Health Monitoring System - Complete Startup"
echo "============================================="

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed or not in PATH"
    exit 1
fi

# Function to check if port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Check if backend is already running
if check_port 5001; then
    echo "✅ Backend server is already running on port 5001"
else
    echo "🚀 Starting backend server..."
    cd "$(dirname "$0")"
    python3 -m backend.app &
    BACKEND_PID=$!
    echo "Backend PID: $BACKEND_PID"
    
    # Wait for backend to start
    echo "⏳ Waiting for backend to start..."
    for i in {1..30}; do
        if curl -s http://localhost:5001/api/v1/health >/dev/null 2>&1; then
            echo "✅ Backend server started successfully"
            break
        fi
        sleep 1
    done
fi

# Check if frontend port is available
if check_port 5002; then
    echo "⚠️  Port 5002 is already in use. Please stop the existing service or use a different port."
    echo "You can access the frontend at: http://localhost:5002"
else
    echo "🚀 Starting frontend server..."
    cd "$(dirname "$0")/frontend"
    python3 app.py &
    FRONTEND_PID=$!
    echo "Frontend PID: $FRONTEND_PID"
    
    # Wait for frontend to start
    echo "⏳ Waiting for frontend to start..."
    for i in {1..30}; do
        if curl -s http://localhost:5002 >/dev/null 2>&1; then
            echo "✅ Frontend server started successfully"
            break
        fi
        sleep 1
    done
fi

echo ""
echo "🎉 System is now running!"
echo "========================="
echo "🌐 Frontend: http://localhost:5002"
echo "🔧 Backend API: http://localhost:5001"
echo "📊 Health Check: http://localhost:5001/api/v1/health"
echo ""
echo "Press Ctrl+C to stop all services"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping services..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
        echo "✅ Backend stopped"
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
        echo "✅ Frontend stopped"
    fi
    echo "👋 All services stopped"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Keep script running
wait
