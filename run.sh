#!/bin/bash
# One-click startup script for EPUB/MOBI to PDF Converter

echo "📚 EPUB/MOBI to PDF Converter"
echo "=============================="
echo ""

cd "$(dirname "$0")"

# Kill existing processes
pkill -f "python.*app.py" 2>/dev/null
pkill -f cloudflared 2>/dev/null
sleep 1

# Start Flask
echo "🚀 Starting Flask..."
nohup python3 app.py > /tmp/flask.log 2>&1 &
FLASK_PID=$!
sleep 3

if ps -p $FLASK_PID > /dev/null; then
    echo "✅ Flask running (PID: $FLASK_PID)"
else
    echo "❌ Flask failed to start"
    cat /tmp/flask.log
    exit 1
fi

# Start Cloudflare Tunnel
echo "🌐 Starting Cloudflare Tunnel..."
cd /tmp
if [ ! -f cloudflared-linux-amd64 ]; then
    echo "⬇️  Downloading cloudflared..."
    curl -sLO https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
    chmod +x cloudflared-linux-amd64
fi

nohup ./cloudflared-linux-amd64 tunnel --url http://localhost:5000 > /tmp/cf.log 2>&1 &
CF_PID=$!
sleep 6

# Get tunnel URL
TUNNEL_URL=$(grep "trycloudflare.com" /tmp/cf.log | grep -o 'https://[^[:space:]]*trycloudflare.com' | head -1)

if [ -n "$TUNNEL_URL" ]; then
    echo "✅ Cloudflare Tunnel running"
    echo ""
    echo "=============================="
    echo "🌐 Public URL: $TUNNEL_URL"
    echo "🏠 Local URL: http://localhost:5000"
    echo "=============================="
    echo ""
    echo "Press Ctrl+C to stop all services"
    
    # Keep running
    wait
else
    echo "⚠️  Tunnel URL not found, check /tmp/cf.log"
    echo "Local access: http://localhost:5000"
fi
