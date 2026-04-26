#!/bin/bash

# Go to the folder where this script lives, regardless of where it's placed
cd "$(dirname "$0")"

# Create venv if it doesn't exist yet
if [ ! -d "venv" ]; then
    echo "Setting up virtual environment for the first time..."
    python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

# Install dependencies quietly (skips if already installed)
pip install -r requirements.txt --quiet

# Launch the app
python app.py
