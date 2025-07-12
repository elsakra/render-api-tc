#!/bin/bash
set -e

echo "Installing build dependencies..."
pip install --upgrade pip
pip install --upgrade setuptools wheel

echo "Installing project dependencies..."
pip install -r requirements.txt

echo "Build complete!" 