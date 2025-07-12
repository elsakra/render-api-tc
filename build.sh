#!/bin/bash
set -e

echo "Python version:"
python --version

echo "Installing build dependencies..."
python -m pip install --upgrade pip==22.3.1
python -m pip install --upgrade setuptools==65.5.0 wheel==0.38.4

echo "Installing project dependencies..."
python -m pip install --no-cache-dir -r requirements.txt

echo "Build complete!" 