#!/bin/bash

echo "============================================================"
echo "EPUB/MOBI to PDF Converter"
echo "============================================================"
echo ""

# Check if virtual environment exists
if [ -f "venv/bin/python" ]; then
    echo "[OK] Virtual environment found."
    echo ""
    echo "[INFO] Starting application..."
    echo ""
    
    # Run application in desktop mode
    venv/bin/python app.py --mode desktop
    
    exit 0
fi

echo "[INFO] Virtual environment not found."
echo "[INFO] First-time setup required..."
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 not found!"
    echo ""
    echo "Please install Python 3.8+ from:"
    echo "  - macOS: brew install python3"
    echo "  - Ubuntu/Debian: sudo apt install python3 python3-venv"
    echo "  - Fedora/RHEL: sudo dnf install python3 python3-pip"
    echo ""
    exit 1
fi

echo "[OK] Python3 found"
python3 --version
echo ""

# Create virtual environment
echo "[INFO] Creating virtual environment..."
python3 -m venv venv

echo "[INFO] Installing dependencies..."
echo "This may take 2-3 minutes..."
echo ""
venv/bin/pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo ""
    echo "[ERROR] Failed to install dependencies!"
    echo "Please check your network connection and try again."
    exit 1
fi

echo ""
echo "[OK] Dependencies installed successfully!"
echo ""
echo "============================================================"
echo "[INFO] First-time setup complete!"
echo "============================================================"
echo ""
echo "Next time, the application will start directly."
echo ""
echo "[INFO] Starting application..."
echo ""

# Run application in desktop mode
venv/bin/python3 app.py --mode desktop
