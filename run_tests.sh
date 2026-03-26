#!/bin/bash
# Script to run tests in a virtual environment
# Usage: ./run_tests.sh

set -e  # Exit on error

VENV_DIR="venv"

# Check if venv exists, create if not
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

# Activate venv
echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Install dependencies if needed
echo "Installing dependencies..."
pip install -q -r requirements-dev.txt
pip install -q -e .

# Run tests
echo ""
echo "Running tests..."
python -m pytest tests/ -v

# Deactivate venv
deactivate
