#!/bin/bash

# NeuroWell-CA Setup Script
# This script automates the setup process

echo "==================================="
echo "NeuroWell-CA Setup Script"
echo "==================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker Desktop first."
    exit 1
fi

echo "✅ Docker is installed"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.10 or higher."
    exit 1
fi

echo "✅ Python is installed"

# Create .env file from example
echo ""
echo "Step 1: Setting up environment variables..."
if [ ! -f "backend/.env" ]; then
    cp backend/.env.example backend/.env
    echo "✅ Created backend/.env file"
    echo "⚠️  Please edit backend/.env and add your credentials (Twilio, JWT secret, etc.)"
else
    echo "ℹ️  backend/.env already exists"
fi

# Start Docker containers
echo ""
echo "Step 2: Starting Docker containers..."
docker-compose up -d

echo "⏳ Waiting for containers to start (30 seconds)..."
sleep 30

# Check if containers are running
if docker ps | grep -q neurowellca-postgres; then
    echo "✅ PostgreSQL container is running"
else
    echo "❌ PostgreSQL container failed to start"
    exit 1
fi

if docker ps | grep -q neurowellca-ollama; then
    echo "✅ Ollama container is running"
else
    echo "❌ Ollama container failed to start"
    exit 1
fi

# Pull Ollama model
echo ""
echo "Step 3: Pulling Ollama model (Llama 3.2 3B - 2GB download)..."
docker exec neurowellca-ollama ollama pull llama3.2:latest

# Set up Python virtual environment
echo ""
echo "Step 4: Setting up Python virtual environment..."
cd backend

if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Created virtual environment"
else
    echo "ℹ️  Virtual environment already exists"
fi

# Activate virtual environment and install dependencies
echo ""
echo "Step 5: Installing Python dependencies..."
source venv/bin/activate
pip install -r requirements.txt

# Initialize database
echo ""
echo "Step 6: Initializing database..."
export FLASK_APP=run.py
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

echo ""
echo "==================================="
echo "✅ Setup Complete!"
echo "==================================="
echo ""
echo "Next steps:"
echo "1. Edit backend/.env and add your Twilio credentials"
echo "2. Start the backend:"
echo "   cd backend"
echo "   source venv/bin/activate"
echo "   python run.py"
echo "3. Open frontend/index.html in your browser"
echo ""
echo "Docker services:"
echo "- PostgreSQL: http://localhost:5432"
echo "- Ollama: http://localhost:11434"
echo ""
echo "Backend API: http://localhost:5000"
echo ""
