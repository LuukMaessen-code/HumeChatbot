#!/bin/bash

echo "Starting shell script..."

# Navigate to the correct directory
cd /mnt/c/code/git/evipython || { echo "Directory not found!"; exit 1; }

echo "Activated directory, now activating the virtual environment..."

# Activate the Python virtual environment
source evi-env/Scripts/activate || { echo "Failed to activate virtual environment!"; exit 1; }

echo "Virtual environment activated. Running the script..."

# Run the Python script
python3 quickstart.py || { echo "Python script failed!"; exit 1; }

echo "Script completed."
