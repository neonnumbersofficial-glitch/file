import logging
import asyncio
import secrets
import threading
import time
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from flask import Flask, render_template_string, jsonify, request
import json
import os
import sys

# Flask app for web dashboard and keep-alive
app = Flask(__name__)

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot Configuration
BOT_TOKEN = "8587129513:AAE6denzbgGIcbKMStYRtF4Jd1z5XiBSxFQ"
ADMIN_ID = 8469461108
BOT_USERNAME = "EXUBOTAI_1BOT"  # Plain text for URLs

# Display name with Unicode bold
BOT_DISPLAY_NAME = "𝐑𝐑𝐂 <𝐊> 𝐄𝐗𝐔 | 𝐗𝐒𝐔"

# Channels to verify (format: @channel_username or channel ID)
CHANNELS = [
    "@exulive",
    "@exucoder1",
    "@funcodex"
]

# Channel display names (for hiding in buttons)
CHANNEL_DISPLAY_NAMES = [
    "𝐂𝐡𝐚𝐧𝐧𝐞𝐥 𝟏",
    "𝐂𝐡𝐚𝐧𝐧𝐞𝐥 𝟐", 
    "𝐂𝐡𝐚𝐧𝐧𝐞𝐥 𝟑"
]

# Allowed groups for bot to respond (empty list means no groups allowed)
ALLOWED_GROUPS = []  # Add group IDs here like [-1001234567890]

# Files storage
FILES_DATA_FILE = "files_data.json"
LINKS_DATA_FILE = "links_data.json"
USERS_DATA_FILE = "users_data.json"
SETTINGS_DATA_FILE = "settings_data.json"

# Initialize data files with proper error handling
def load_json_file(filename, default_data):
    """Load JSON file with error handling."""
    try:
        if os.path.exists(filename) and os.path.getsize(filename) > 0:
            with open(filename, 'r') as f:
                return json.load(f)
        else:
            # Create file with default data
            with open(filename, 'w') as f:
                json.dump(default_data, f)
            return default_data
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logger.error(f"Error loading {filename}: {e}. Creating new file.")
        # File is corrupted, create new one
        with open(filename, 'w') as f:
            json.dump(default_data, f)
        return default_data

# Default data structures
files_data = load_json_file(FILES_DATA_FILE, {})
links_data = load_json_file(LINKS_DATA_FILE, {})
users_data = load_json_file(USERS_DATA_FILE, {})
settings_data = load_json_file(SETTINGS_DATA_FILE, {
    "allowed_groups": [],
    "group_chat_enabled": False,
    "bot_uptime": datetime.now().isoformat()
})

# Track bot start time
BOT_START_TIME = datetime.now()

def generate_unique_id():
    """Generate unique ID for files."""
    return secrets.token_urlsafe(8)

def generate_link_id():
    """Generate unique link ID."""
    return secrets.token_urlsafe(6)

def save_files_data():
    """Save files data to file."""
    with open(FILES_DATA_FILE, 'w') as f:
        json.dump(files_data, f)

def save_links_data():
    """Save links data to file."""
    with open(LINKS_DATA_FILE, 'w') as f:
        json.dump(links_data, f)

def save_users_data():
    """Save users data to file."""
    with open(USERS_DATA_FILE, 'w') as f:
        json.dump(users_data, f)

def save_settings_data():
    """Save settings data to file."""
    with open(SETTINGS_DATA_FILE, 'w') as f:
        json.dump(settings_data, f)

def clear_terminal():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def show_banner():
    """Display the bot banner."""
    banner = """
███████╗██╗  ██╗██╗   ██╗     ██████╗ ██████╗ ██████╗ ███████╗██╗  ██╗
██╔════╝╚██╗██╔╝██║   ██║    ██╔════╝██╔═══██╗██╔══██╗██╔════╝╚██╗██╔╝
█████╗   ╚███╔╝ ██║   ██║    ██║     ██║   ██║██║  ██║█████╗   ╚███╔╝ 
██╔══╝   ██╔██╗ ██║   ██║    ██║     ██║   ██║██║  ██║██╔══╝   ██╔██╗ 
███████╗██╔╝ ██╗╚██████╔╝    ╚██████╗╚██████╔╝██████╔╝███████╗██╔╝ ██╗
╚══════╝╚═╝  ╚═╝ ╚═════╝      ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝
    """
    print(banner)
    print(f"╔{'═'*60}╗")
    print(f"║ {BOT_DISPLAY_NAME:<58} ║")
    print(f"║ {'-'*58} ║")
    print(f"║ 🤖 Bot Status: RUNNING {' ':<38} ║")
    print(f"║ 👑 Admin ID: {ADMIN_ID:<44} ║")
    print(f"║ 📢 Channels: {len(CHANNELS)} configured {' ':<37} ║")
    print(f"║ 💬 Group Chat: {'ENABLED' if settings_data.get('group_chat_enabled') else 'DISABLED':<42} ║")
    print(f"║ 📁 Total Files: {len(files_data):<41} ║")
    print(f"║ 🔗 Total Links: {len(links_data):<41} ║")
    print(f"║ 👥 Total Users: {len(users_data):<41} ║")
    print(f"╚{'═'*60}╝")
    print("\n📝 Press Ctrl+C to stop the bot\n")
    print("🌐 Web Dashboard: http://localhost:5000 (or your deployed URL)")

# Admin keyboard with styled buttons
def get_admin_keyboard():
    keyboard = [
        [KeyboardButton("📝 𝐇𝐨𝐬𝐭 𝐓𝐞𝐱𝐭"), KeyboardButton("📁 𝐇𝐨𝐬𝐭 𝐅𝐢𝐥𝐞")],
        [KeyboardButton("🔗 𝐆𝐞𝐧𝐞𝐫𝐚𝐭𝐞 𝐋𝐢𝐧𝐤"), KeyboardButton("📊 𝐅𝐢𝐥𝐞𝐬 𝐋𝐢𝐬𝐭")],
        [KeyboardButton("📢 𝐁𝐫𝐨𝐚𝐝𝐜𝐚𝐬𝐭"), KeyboardButton("📋 𝐂𝐨𝐧𝐭𝐞𝐧𝐭 𝐌𝐚𝐧𝐚𝐠𝐞𝐫")],
        [KeyboardButton("📈 𝐒𝐭𝐚𝐭𝐬"), KeyboardButton("⚙️ 𝐒𝐞𝐭𝐭𝐢𝐧𝐠𝐬")],
        [KeyboardButton("❓ 𝐇𝐞𝐥𝐩")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# User keyboard with styled buttons
def get_user_keyboard():
    keyboard = [
        [KeyboardButton("/start")],
        [KeyboardButton("📁 𝐌𝐲 𝐅𝐢𝐥𝐞𝐬"), KeyboardButton("❓ 𝐇𝐞𝐥𝐩")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ==================== FLASK WEB DASHBOARD ====================

# HTML Template for dashboard
DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ bot_name }} Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .header {
            background: white;
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            text-align: center;
        }
        
        .header h1 {
            color: #333;
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header p {
            color: #666;
            font-size: 1.2em;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
        }
        
        .stat-card h3 {
            color: #666;
            font-size: 1.1em;
            margin-bottom: 10px;
        }
        
        .stat-card .number {
            color: #333;
            font-size: 2.5em;
            font-weight: bold;
        }
        
        .stat-card .icon {
            font-size: 3em;
            margin-bottom: 10px;
        }
        
        .channels-section {
            background: white;
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
        }
        
        .channels-section h2 {
            color: #333;
            margin-bottom: 20px;
        }
        
        .channel-list {
            list-style: none;
        }
        
        .channel-item {
            display: flex;
            align-items: center;
            padding: 15px;
            border-bottom: 1px solid #eee;
        }
        
        .channel-item:last-child {
            border-bottom: none;
        }
        
        .channel-status {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 15px;
        }
        
        .status-active {
            background: #4CAF50;
        }
        
        .channel-name {
            flex: 1;
            font-size: 1.1em;
        }
        
        .channel-link {
            color: #667eea;
            text-decoration: none;
            padding: 5px 15px;
            border: 1px solid #667eea;
            border-radius: 5px;
            transition: all 0.3s ease;
        }
        
        .channel-link:hover {
            background: #667eea;
            color: white;
        }
        
        .files-section {
            background: white;
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
        }
        
        .files-section h2 {
            color: #333;
            margin-bottom: 20px;
        }
        
        .files-table {
            width: 100%;
            border-collapse: collapse;
        }
        
        .files-table th,
        .files-table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }
        
        .files-table th {
            background: #f5f5f5;
            color: #666;
            font-weight: 600;
        }
        
        .files-table tr:hover {
            background: #f9f9f9;
        }
        
        .link-btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 5px 10px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 0.9em;
        }
        
        .link-btn:hover {
            background: #764ba2;
        }
        
        .footer {
            text-align: center;
            color: white;
            margin-top: 30px;
        }
        
        .footer a {
            color: white;
            text-decoration: none;
            font-weight: bold;
        }
        
        .refresh-btn {
            background: white;
            color: #667eea;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 1em;
            margin-top: 20px;
            transition: all 0.3s ease;
        }
        
        .refresh-btn:hover {
            background: #f0f0f0;
            transform: scale(1.05);
        }
        
        @media (max-width: 768px) {
            .header h1 {
                font-size: 2em;
            }
            
            .stat-card .number {
                font-size: 2em;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 {{ bot_name }}</h1>
            <p>Telegram Bot Dashboard</p>
            <button class="refresh-btn" onclick="location.reload()">🔄 Refresh Data</button>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="icon">📁</div>
                <h3>Total Files</h3>
                <div class="number">{{ stats.total_files }}</div>
            </div>
            
            <div class="stat-card">
                <div class="icon">🔗</div>
                <h3>Total Links</h3>
                <div class="number">{{ stats.total_links }}</div>
            </div>
            
            <div class="stat-card">
                <div class="icon">📥</div>
                <h3>Total Downloads</h3>
                <div class="number">{{ stats.total_downloads }}</div>
            </div>
            
            <div class="stat-card">
                <div class="icon">👥</div>
                <h3>Total Users</h3>
                <div class="number">{{ stats.total_users }}</div>
            </div>
        </div>
        
        <div class="channels-section">
            <h2>📢 Required Channels</h2>
            <ul class="channel-list">
                {% for channel in channels %}
                <li class="channel-item">
                    <div class="channel-status status-active"></div>
                    <span class="channel-name">{{ channel.display_name }}</span>
                    <a href="https://t.me/{{ channel.username }}" target="_blank" class="channel-link">Join</a>
                </li>
                {% endfor %}
            </ul>
        </div>
        
        <div class="files-section">
            <h2>📁 Recent Files</h2>
            <table class="files-table">
                <thead>
                    <tr>
                        <th>#</th>
                        <th>File Name</th>
                        <th>Type</th>
                        <th>Downloads</th>
                        <th>Date</th>
                        <th>Link</th>
                    </tr>
                </thead>
                <tbody>
                    {% for file in recent_files %}
                    <tr>
                        <td>{{ loop.index }}</td>
                        <td>{{ file.name }}</td>
                        <td>{{ file.type }}</td>
                        <td>{{ file.downloads }}</td>
                        <td>{{ file.date }}</td>
                        <td>
                            <button class="link-btn" onclick="copyLink('{{ file.link }}')">Copy Link</button>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        
        <div class="footer">
            <p>⚡ Powered by <a href="#">{{ bot_name }}</a> | Uptime: {{ uptime }}</p>
        </div>
    </div>
    
    <script>
        function copyLink(link) {
            navigator.clipboard.writeText(link).then(function() {
                alert('Link copied to clipboard!');
            }, function() {
                alert('Failed to copy link');
            });
        }
        
        // Auto refresh every 30 seconds
        setTimeout(function() {
            location.reload();
        }, 30000);
    </script>
</body>
</html>
"""

@app.route('/')
def dashboard():
    """Main dashboard page."""
    # Calculate uptime
    uptime_delta = datetime.now() - BOT_START_TIME
    days = uptime_delta.days
    hours = uptime_delta.seconds // 3600
    minutes = (uptime_delta.seconds % 3600) // 60
    uptime_str = f"{days}d {hours}h {minutes}m"
    
    # Get recent files (last 10)
    recent_files = []
    for file_id, file_data in list(files_data.items())[-10:]:
        link_id = None
        for lid, ldata in links_data.items():
            if ldata["file_id"] == file_id:
                link_id = lid
                break
        
        link_url = f"https://t.me/{BOT_USERNAME}?start={link_id}" if link_id else "#"
        
        recent_files.append({
            "name": file_data.get('name', 'Unknown'),
            "type": file_data.get('file_type', 'Unknown'),
            "downloads": file_data.get('downloads', 0),
            "date": file_data.get('date', 'Unknown'),
            "link": link_url
        })
    
    # Prepare channel data
    channel_data = []
    for i, channel in enumerate(CHANNELS):
        channel_data.append({
            "display_name": CHANNEL_DISPLAY_NAMES[i],
            "username": channel.replace('@', '')
        })
    
    # Stats
    total_downloads = sum(file_data.get('downloads', 0) for file_data in files_data.values())
    
    stats = {
        "total_files": len(files_data),
        "total_links": len(links_data),
        "total_downloads": total_downloads,
        "total_users": len(users_data)
    }
    
    return render_template_string(
        DASHBOARD_TEMPLATE,
        bot_name=BOT_DISPLAY_NAME,
        stats=stats,
        channels=channel_data,
        recent_files=recent_files,
        uptime=uptime_str
    )

@app.route('/api/stats')
def api_stats():
    """API endpoint for stats."""
    total_downloads = sum(file_data.get('downloads', 0) for file_data in files_data.values())
    
    return jsonify({
        "total_files": len(files_data),
        "total_links": len(links_data),
        "total_downloads": total_downloads,
        "total_users": len(users_data),
        "channels": len(CHANNELS),
        "group_chat_enabled": settings_data.get("group_chat_enabled", False)
    })

@app.route('/api/files')
def api_files():
    """API endpoint for files list."""
    files_list = []
    for file_id, file_data in files_data.items():
        files_list.append({
            "id": file_id,
            "name": file_data.get('name', 'Unknown'),
            "type": file_data.get('file_type', 'Unknown'),
            "downloads": file_data.get('downloads', 0),
            "date": file_data.get('date', 'Unknown')
        })
    return jsonify(files_list)

@app.route('/health')
def health():
    """Health check endpoint for keep-alive."""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

@app.route('/ping')
def ping():
    """Simple ping endpoint."""
    return "pong"

def run_flask():
    """Run Flask app in a separate thread."""
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# ==================== TELEGRAM BOT CODE ====================

async def check_group_permission(update: Update) -> bool:
    """Check if bot should respond in this group."""
    if update.effective_chat.type == "private":
        return True
    
    # Group chat
    if not settings_data.get("group_chat_enabled", False):
        return False
    
    group_id = update.effective_chat.id
    allowed_groups = settings_data.get("allowed_groups", [])
    
    if allowed_groups and group_id not in allowed_groups:
        return False
    
    return True

async def check_subscription(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check if user is subscribed to all channels."""
    try:
        for channel in CHANNELS:
            try:
                chat_member = await context.bot.get_chat_member(
                    chat_id=channel,
                    user_id=user_id
                )
                # Check if user is member, administrator, creator
                if chat_member.status in ['left', 'kicked']:
                    logger.info(f"User {user_id} not subscribed to {channel}")
                    return False
                logger.info(f"User {user_id} is {chat_member.status} in {channel}")
            except Exception as e:
                logger.error(f"Error checking channel {channel}: {e}")
                return False
        return True
    except Exception as e:
        logger.error(f"Error checking subscription: {e}")
        return False

async def get_unjoined_channels(user_id: int, context: ContextTypes.DEFAULT_TYPE):
    """Get list of channels user hasn't joined yet."""
    unjoined = []
    for channel in CHANNELS:
        try:
            chat_member = await context.bot.get_chat_member(
                chat_id=channel,
                user_id=user_id
            )
            logger.info(f"User {user_id} is {chat_member.status} in {channel}")
            if chat_member.status in ['left', 'kicked']:
                unjoined.append(channel)
        except Exception as e:
            logger.error(f"Error checking channel {channel}: {e}")
            unjoined.append(channel)  # If can't check, assume not joined
    return unjoined

async def force_subscription_check(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Force subscription check - returns True if user is subscribed, False otherwise."""
    user_id = update.effective_user.id
    
    # Admin bypass
    if user_id == ADMIN_ID:
        return True
    
    # Check subscription
    is_subscribed = await check_subscription(user_id, context)
    
    if not is_subscribed:
        # Get unjoined channels
        unjoined_channels = await get_unjoined_channels(user_id, context)
        unjoined_indices = [CHANNELS.index(ch) for ch in unjoined_channels if ch in CHANNELS]
        
        # Create subscription keyboard
        keyboard = []
        for idx in unjoined_indices:
            keyboard.append([InlineKeyboardButton(
                f"📢 𝐉𝐨𝐢𝐧 {CHANNEL_DISPLAY_NAMES[idx]}",
                url=f"https://t.me/{CHANNELS[idx].replace('@', '')}"
            )])
        
        keyboard.append([InlineKeyboardButton("✅ 𝐕𝐞𝐫𝐢𝐟𝐲 𝐒𝐮𝐛𝐬𝐜𝐫𝐢𝐩𝐭𝐢𝐨𝐧", callback_data="verify_subscription")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        total_channels = len(CHANNELS)
        joined_count = total_channels - len(unjoined_indices)
        
        await update.message.reply_text(
            f"🚫 𝐀𝐜𝐜𝐞𝐬𝐬 𝐃𝐞𝐧𝐢𝐞𝐝!\n\n"
            f"📊 𝐏𝐫𝐨𝐠𝐫𝐞𝐬𝐬: {joined_count}/{total_channels} 𝐜𝐡𝐚𝐧𝐧𝐞𝐥𝐬 𝐣𝐨𝐢𝐧𝐞𝐝\n\n"
            f"⚠️ 𝐓𝐨 𝐮𝐬𝐞 𝐭𝐡𝐢𝐬 𝐛𝐨𝐭, 𝐲𝐨𝐮 𝐦𝐮𝐬𝐭 𝐣𝐨𝐢𝐧 𝐚𝐥𝐥 𝐜𝐡𝐚𝐧𝐧𝐞𝐥𝐬 𝐟𝐢𝐫𝐬𝐭!\n\n"
            f"👇 𝐂𝐥𝐢𝐜𝐤 𝐭𝐡𝐞 𝐛𝐮𝐭𝐭𝐨𝐧𝐬 𝐛𝐞𝐥𝐨𝐰 𝐭𝐨 𝐣𝐨𝐢𝐧: 👇",
            reply_markup=reply_markup
        )
        return False
    
    return True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a professional welcome message when the command /start is issued."""
    # Check group permission
    if not await check_group_permission(update):
        return
    
    user_id = update.effective_user.id
    args = context.args
    user = update.effective_user
    
    # Save user to database
    if str(user_id) not in users_data and user_id != ADMIN_ID:
        users_data[str(user_id)] = {
            "first_seen": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name
        }
        save_users_data()
    
    # Check if coming from a file link
    if args and len(args) > 0:
        link_id = args[0]
        await handle_file_link(update, context, link_id)
        return
    
    # FORCE SUBSCRIPTION CHECK - User must join channels first
    if not await force_subscription_check(update, context):
        return
    
    # Get current time for greeting
    current_hour = datetime.now().hour
    if current_hour < 12:
        greeting = "𝐆𝐨𝐨𝐝 𝐌𝐨𝐫𝐧𝐢𝐧𝐠"
    elif current_hour < 17:
        greeting = "𝐆𝐨𝐨𝐝 𝐀𝐟𝐭𝐞𝐫𝐧𝐨𝐨𝐧"
    else:
        greeting = "𝐆𝐨𝐨𝐝 𝐄𝐯𝐞𝐧𝐢𝐧𝐠"
    
    welcome_text = (
        f"╔═══《 🎉 {greeting}! 》═══╗\n\n"
        f"👤 𝐔𝐬𝐞𝐫: {user.first_name}\n"
        f"🆔 𝐔𝐬𝐞𝐫 𝐈𝐃: {user_id}\n"
        f"🌟 𝐒𝐭𝐚𝐭𝐮𝐬: {'𝐀𝐝𝐦𝐢𝐧𝐢𝐬𝐭𝐫𝐚𝐭𝐨𝐫' if user_id == ADMIN_ID else '𝐕𝐚𝐥𝐮𝐞𝐝 𝐔𝐬𝐞𝐫'}\n\n"
        f"╰═══════《 🤖 》═══════╝\n\n"
        f"𝐖𝐞𝐥𝐜𝐨𝐦𝐞 𝐭𝐨 {BOT_DISPLAY_NAME}\n\n"
        f"📌 𝐀𝐛𝐨𝐮𝐭 𝐓𝐡𝐢𝐬 𝐁𝐨𝐭:\n"
        f"• 🔐 𝐒𝐞𝐜𝐮𝐫𝐞 𝐅𝐢𝐥𝐞 𝐒𝐭𝐨𝐫𝐚𝐠𝐞\n"
        f"• 📤 𝐄𝐚𝐬𝐲 𝐅𝐢𝐥𝐞 𝐒𝐡𝐚𝐫𝐢𝐧𝐠\n"
        f"• 🔗 𝐀𝐮𝐭𝐨𝐦𝐚𝐭𝐢𝐜 𝐋𝐢𝐧𝐤 𝐆𝐞𝐧𝐞𝐫𝐚𝐭𝐢𝐨𝐧\n"
        f"• 📊 𝐑𝐞𝐚𝐥-𝐭𝐢𝐦𝐞 𝐃𝐨𝐰𝐧𝐥𝐨𝐚𝐝 𝐓𝐫𝐚𝐜𝐤𝐢𝐧𝐠\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"✅ 𝐀𝐜𝐜𝐞𝐬𝐬 𝐆𝐫𝐚𝐧𝐭𝐞𝐝!\n"
        f"𝐘𝐨𝐮 𝐡𝐚𝐯𝐞 𝐬𝐮𝐜𝐜𝐞𝐬𝐬𝐟𝐮𝐥𝐥𝐲 𝐣𝐨𝐢𝐧𝐞𝐝 𝐚𝐥𝐥 𝐜𝐡𝐚𝐧𝐧𝐞𝐥𝐬.\n\n"
        f"📌 𝐐𝐮𝐢𝐜𝐤 𝐆𝐮𝐢𝐝𝐞:\n"
        f"• 𝐔𝐬𝐞 𝐦𝐞𝐧𝐮 𝐛𝐮𝐭𝐭𝐨𝐧𝐬 𝐭𝐨 𝐧𝐚𝐯𝐢𝐠𝐚𝐭𝐞\n"
        f"• /𝐡𝐞𝐥𝐩 𝐟𝐨𝐫 𝐦𝐨𝐫𝐞 𝐢𝐧𝐟𝐨𝐫𝐦𝐚𝐭𝐢𝐨𝐧\n"
        f"• 📁 𝐌𝐲 𝐅𝐢𝐥𝐞𝐬 𝐭𝐨 𝐯𝐢𝐞𝐰 𝐚𝐜𝐜𝐞𝐬𝐬𝐞𝐝 𝐟𝐢𝐥𝐞𝐬"
    )
    
    if user_id == ADMIN_ID:
        reply_markup = get_admin_keyboard()
    else:
        reply_markup = get_user_keyboard()
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=reply_markup
    )

async def handle_file_link(update: Update, context: ContextTypes.DEFAULT_TYPE, link_id: str):
    """Handle file link access - STRICT SUBSCRIPTION CHECK."""
    if not await check_group_permission(update):
        return
    
    user_id = update.effective_user.id
    
    if not await force_subscription_check(update, context):
        return
    
    if link_id not in links_data:
        await update.message.reply_text(
            f"❌ 𝐈𝐧𝐯𝐚𝐥𝐢𝐝 𝐋𝐢𝐧𝐤!\n\n"
            f"𝐓𝐡𝐞 𝐥𝐢𝐧𝐤 𝐲𝐨𝐮 𝐚𝐫𝐞 𝐭𝐫𝐲𝐢𝐧𝐠 𝐭𝐨 𝐚𝐜𝐜𝐞𝐬𝐬 𝐢𝐬 𝐢𝐧𝐯𝐚𝐥𝐢𝐝 𝐨𝐫 𝐡𝐚𝐬 𝐞𝐱𝐩𝐢𝐫𝐞𝐝.",
            reply_markup=get_user_keyboard()
        )
        return
    
    file_id = links_data[link_id]["file_id"]
    
    if file_id not in files_data:
        await update.message.reply_text(
            f"❌ 𝐅𝐢𝐥𝐞 𝐍𝐨𝐭 𝐅𝐨𝐮𝐧𝐝!\n\n"
            f"𝐓𝐡𝐞 𝐟𝐢𝐥𝐞 𝐲𝐨𝐮 𝐚𝐫𝐞 𝐥𝐨𝐨𝐤𝐢𝐧𝐠 𝐟𝐨𝐫 𝐢𝐬 𝐧𝐨 𝐥𝐨𝐧𝐠𝐞𝐫 𝐚𝐯𝐚𝐢𝐥𝐚𝐛𝐥𝐞.",
            reply_markup=get_user_keyboard()
        )
        return
    
    await send_file_to_user(update, file_id)
    
    files_data[file_id]["downloads"] = files_data[file_id].get("downloads", 0) + 1
    save_files_data()
    
    user_files = files_data[file_id].get("accessed_by", {})
    if str(user_id) not in user_files:
        user_files[str(user_id)] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        files_data[file_id]["accessed_by"] = user_files
        save_files_data()

async def verify_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle verify subscription button."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    callback_data = query.data
    
    if callback_data == "verify_subscription":
        unjoined_channels = await get_unjoined_channels(user_id, context)
        unjoined_indices = [CHANNELS.index(ch) for ch in unjoined_channels if ch in CHANNELS]
        
        if not unjoined_indices:
            await query.edit_message_text(
                f"✅ 𝐒𝐮𝐛𝐬𝐜𝐫𝐢𝐩𝐭𝐢𝐨𝐧 𝐕𝐞𝐫𝐢𝐟𝐢𝐞𝐝!\n\n"
                f"𝐍𝐨𝐰 𝐲𝐨𝐮 𝐜𝐚𝐧 𝐚𝐜𝐜𝐞𝐬𝐬 𝐚𝐥𝐥 𝐟𝐢𝐥𝐞𝐬.\n"
                f"𝐔𝐬𝐞 /𝐬𝐭𝐚𝐫𝐭 𝐭𝐨 𝐜𝐨𝐧𝐭𝐢𝐧𝐮𝐞.\n\n"
                f"🤖 𝐁𝐨𝐭 𝐛𝐲: {BOT_DISPLAY_NAME}"
            )
        else:
            channel_list = ""
            for i, idx in enumerate(unjoined_indices, 1):
                channel_list += f"{i}. {CHANNEL_DISPLAY_NAMES[idx]}\n"
            
            await query.edit_message_text(
                f"❌ 𝐕𝐞𝐫𝐢𝐟𝐢𝐜𝐚𝐭𝐢𝐨𝐧 𝐅𝐚𝐢𝐥𝐞𝐝!\n\n"
                f"𝐘𝐨𝐮 𝐡𝐚𝐯𝐞𝐧'𝐭 𝐣𝐨𝐢𝐧𝐞𝐝 𝐚𝐥𝐥 𝐜𝐡𝐚𝐧𝐧𝐞𝐥𝐬 𝐲𝐞𝐭.\n\n"
                f"𝐏𝐥𝐞𝐚𝐬𝐞 𝐣𝐨𝐢𝐧 𝐭𝐡𝐞𝐬𝐞 𝐜𝐡𝐚𝐧𝐧𝐞𝐥𝐬:\n\n"
                f"{channel_list}\n"
                f"𝐀𝐟𝐭𝐞𝐫 𝐣𝐨𝐢𝐧𝐢𝐧𝐠, 𝐜𝐥𝐢𝐜𝐤 𝐕𝐞𝐫𝐢𝐟𝐲 𝐚𝐠𝐚𝐢𝐧.\n\n"
                f"🤖 𝐁𝐨𝐭 𝐛𝐲: {BOT_DISPLAY_NAME}"
            )
            await ask_for_subscription_callback(query, context, unjoined_indices)
    
    elif callback_data.startswith("verify_file_"):
        link_id = callback_data.replace("verify_file_", "")
        
        if link_id not in links_data:
            await query.edit_message_text(
                f"❌ 𝐈𝐧𝐯𝐚𝐥𝐢𝐝 𝐋𝐢𝐧𝐤!"
            )
            return
        
        unjoined_channels = await get_unjoined_channels(user_id, context)
        unjoined_indices = [CHANNELS.index(ch) for ch in unjoined_channels if ch in CHANNELS]
        
        if not unjoined_indices:
            file_id = links_data[link_id]["file_id"]
            
            if file_id not in files_data:
                await query.edit_message_text(
                    f"❌ 𝐅𝐢𝐥𝐞 𝐍𝐨𝐭 𝐅𝐨𝐮𝐧𝐝!"
                )
                return
            
            await query.edit_message_text(
                f"✅ 𝐀𝐜𝐜𝐞𝐬𝐬 𝐆𝐫𝐚𝐧𝐭𝐞𝐝!\n\n"
                f"𝐒𝐞𝐧𝐝𝐢𝐧𝐠 𝐲𝐨𝐮𝐫 𝐟𝐢𝐥𝐞...\n\n"
                f"🤖 𝐁𝐨𝐭 𝐛𝐲: {BOT_DISPLAY_NAME}"
            )
            
            await send_file_to_user_callback(query, file_id)
            
            files_data[file_id]["downloads"] = files_data[file_id].get("downloads", 0) + 1
            save_files_data()
            
            user_files = files_data[file_id].get("accessed_by", {})
            if str(user_id) not in user_files:
                user_files[str(user_id)] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                files_data[file_id]["accessed_by"] = user_files
                save_files_data()
        else:
            channel_list = ""
            for i, idx in enumerate(unjoined_indices, 1):
                channel_list += f"{i}. {CHANNEL_DISPLAY_NAMES[idx]}\n"
            
            await query.edit_message_text(
                f"❌ 𝐕𝐞𝐫𝐢𝐟𝐢𝐜𝐚𝐭𝐢𝐨𝐧 𝐅𝐚𝐢𝐥𝐞𝐝!\n\n"
                f"𝐘𝐨𝐮 𝐡𝐚𝐯𝐞𝐧'𝐭 𝐣𝐨𝐢𝐧𝐞𝐝 𝐚𝐥𝐥 𝐜𝐡𝐚𝐧𝐧𝐞𝐥𝐬 𝐲𝐞𝐭.\n\n"
                f"𝐓𝐨 𝐠𝐞𝐭 𝐭𝐡𝐞 𝐟𝐢𝐥𝐞, 𝐩𝐥𝐞𝐚𝐬𝐞 𝐣𝐨𝐢𝐧 𝐭𝐡𝐞𝐬𝐞 𝐜𝐡𝐚𝐧𝐧𝐞𝐥𝐬:\n\n"
                f"{channel_list}\n"
                f"𝐀𝐟𝐭𝐞𝐫 𝐣𝐨𝐢𝐧𝐢𝐧𝐠, 𝐜𝐥𝐢𝐜𝐤 𝐕𝐞𝐫𝐢𝐟𝐲 𝐚𝐠𝐚𝐢𝐧.\n\n"
                f"🤖 𝐁𝐨𝐭 𝐛𝐲: {BOT_DISPLAY_NAME}"
            )
            await ask_for_subscription_with_file_callback(query, context, link_id, unjoined_indices)

async def ask_for_subscription_callback(query, context: ContextTypes.DEFAULT_TYPE, unjoined_indices=None):
    """Ask for subscription via callback - only shows unjoined channels."""
    user_id = query.from_user.id
    
    if unjoined_indices is None:
        unjoined_channels = await get_unjoined_channels(user_id, context)
        unjoined_indices = [CHANNELS.index(ch) for ch in unjoined_channels if ch in CHANNELS]
    
    if not unjoined_indices:
        await query.message.reply_text(
            f"✅ 𝐀𝐥𝐥 𝐂𝐡𝐚𝐧𝐧𝐞𝐥𝐬 𝐉𝐨𝐢𝐧𝐞𝐝!\n\n"
            f"𝐘𝐨𝐮 𝐡𝐚𝐯𝐞 𝐬𝐮𝐜𝐜𝐞𝐬𝐬𝐟𝐮𝐥𝐥𝐲 𝐣𝐨𝐢𝐧𝐞𝐝 𝐚𝐥𝐥 𝐜𝐡𝐚𝐧𝐧𝐞𝐥𝐬.\n"
            f"𝐔𝐬𝐞 /𝐬𝐭𝐚𝐫𝐭 𝐭𝐨 𝐚𝐜𝐜𝐞𝐬𝐬 𝐟𝐢𝐥𝐞𝐬.",
            reply_markup=get_user_keyboard()
        )
        return
    
    keyboard = []
    
    for idx in unjoined_indices:
        keyboard.append([InlineKeyboardButton(
            f"📢 𝐉𝐨𝐢𝐧 {CHANNEL_DISPLAY_NAMES[idx]}",
            url=f"https://t.me/{CHANNELS[idx].replace('@', '')}"
        )])
    
    keyboard.append([InlineKeyboardButton("✅ 𝐕𝐞𝐫𝐢𝐟𝐲 𝐒𝐮𝐛𝐬𝐜𝐫𝐢𝐩𝐭𝐢𝐨𝐧", callback_data="verify_subscription")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    total_channels = len(CHANNELS)
    joined_count = total_channels - len(unjoined_indices)
    
    await query.message.reply_text(
        f"📋 𝐂𝐡𝐚𝐧𝐧𝐞𝐥 𝐕𝐞𝐫𝐢𝐟𝐢𝐜𝐚𝐭𝐢𝐨𝐧 𝐑𝐞𝐪𝐮𝐢𝐫𝐞𝐝\n\n"
        f"📊 𝐏𝐫𝐨𝐠𝐫𝐞𝐬𝐬: {joined_count}/{total_channels} 𝐜𝐡𝐚𝐧𝐧𝐞𝐥𝐬 𝐣𝐨𝐢𝐧𝐞𝐝\n\n"
        f"⚠️ 𝐏𝐥𝐞𝐚𝐬𝐞 𝐣𝐨𝐢𝐧 𝐭𝐡𝐞 𝐟𝐨𝐥𝐥𝐨𝐰𝐢𝐧𝐠 𝐜𝐡𝐚𝐧𝐧𝐞𝐥𝐬 𝐭𝐨 𝐜𝐨𝐧𝐭𝐢𝐧𝐮𝐞:\n\n"
        f"𝐀𝐟𝐭𝐞𝐫 𝐣𝐨𝐢𝐧𝐢𝐧𝐠, 𝐜𝐥𝐢𝐜𝐤 𝐭𝐡𝐞 𝐕𝐞𝐫𝐢𝐟𝐲 𝐛𝐮𝐭𝐭𝐨𝐧 𝐛𝐞𝐥𝐨𝐰.\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🤖 𝐁𝐨𝐭 𝐛𝐲: {BOT_DISPLAY_NAME}",
        reply_markup=reply_markup
    )

async def ask_for_subscription_with_file_callback(query, context: ContextTypes.DEFAULT_TYPE, link_id: str, unjoined_indices=None):
    """Ask for subscription with file context via callback."""
    user_id = query.from_user.id
    
    if unjoined_indices is None:
        unjoined_channels = await get_unjoined_channels(user_id, context)
        unjoined_indices = [CHANNELS.index(ch) for ch in unjoined_channels if ch in CHANNELS]
    
    if not unjoined_indices:
        file_id = links_data[link_id]["file_id"]
        await send_file_to_user_callback(query, file_id)
        
        files_data[file_id]["downloads"] = files_data[file_id].get("downloads", 0) + 1
        save_files_data()
        
        user_files = files_data[file_id].get("accessed_by", {})
        if str(user_id) not in user_files:
            user_files[str(user_id)] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            files_data[file_id]["accessed_by"] = user_files
            save_files_data()
        return
    
    keyboard = []
    
    for idx in unjoined_indices:
        keyboard.append([InlineKeyboardButton(
            f"📢 𝐉𝐨𝐢𝐧 {CHANNEL_DISPLAY_NAMES[idx]}",
            url=f"https://t.me/{CHANNELS[idx].replace('@', '')}"
        )])
    
    keyboard.append([InlineKeyboardButton("✅ 𝐕𝐞𝐫𝐢𝐟𝐲 & 𝐆𝐞𝐭 𝐅𝐢𝐥𝐞", callback_data=f"verify_file_{link_id}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    total_channels = len(CHANNELS)
    joined_count = total_channels - len(unjoined_indices)
    
    file_id = links_data[link_id]["file_id"]
    file_name = files_data[file_id].get('name', '𝐅𝐢𝐥𝐞')
    
    await query.message.reply_text(
        f"📋 𝐅𝐢𝐥𝐞 𝐀𝐜𝐜𝐞𝐬𝐬 𝐑𝐞𝐪𝐮𝐢𝐫𝐞𝐬 𝐂𝐡𝐚𝐧𝐧𝐞𝐥 𝐉𝐨𝐢𝐧𝐢𝐧𝐠\n\n"
        f"📁 𝐅𝐢𝐥𝐞: {file_name}\n"
        f"📊 𝐏𝐫𝐨𝐠𝐫𝐞𝐬𝐬: {joined_count}/{total_channels} 𝐜𝐡𝐚𝐧𝐧𝐞𝐥𝐬 𝐣𝐨𝐢𝐧𝐞𝐝\n\n"
        f"⚠️ 𝐓𝐨 𝐠𝐞𝐭 𝐭𝐡𝐢𝐬 𝐟𝐢𝐥𝐞, 𝐩𝐥𝐞𝐚𝐬𝐞 𝐣𝐨𝐢𝐧 𝐭𝐡𝐞 𝐟𝐨𝐥𝐥𝐨𝐰𝐢𝐧𝐠 𝐜𝐡𝐚𝐧𝐧𝐞𝐥𝐬:\n\n"
        f"𝐀𝐟𝐭𝐞𝐫 𝐣𝐨𝐢𝐧𝐢𝐧𝐠, 𝐜𝐥𝐢𝐜𝐤 𝐭𝐡𝐞 𝐕𝐞𝐫𝐢𝐟𝐲 & 𝐆𝐞𝐭 𝐅𝐢𝐥𝐞 𝐛𝐮𝐭𝐭𝐨𝐧.\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🤖 𝐁𝐨𝐭 𝐛𝐲: {BOT_DISPLAY_NAME}",
        reply_markup=reply_markup
    )

async def send_file_to_user(update: Update, file_id: str):
    """Send file to user."""
    file_data = files_data[file_id]
    
    try:
        caption_text = file_data.get("caption", "")
        caption = f"📁 {file_data.get('name', '𝐅𝐢𝐥𝐞')}\n\n{caption_text}\n\n━━━━━━━━━━━━━━━━━━━━━━\n🤖 𝐁𝐨𝐭 𝐛𝐲: {BOT_DISPLAY_NAME}"
        
        if file_data["file_type"] == "photo":
            await update.message.reply_photo(
                photo=file_data["file_id"],
                caption=caption
            )
        elif file_data["file_type"] == "video":
            await update.message.reply_video(
                video=file_data["file_id"],
                caption=caption
            )
        elif file_data["file_type"] == "document":
            await update.message.reply_document(
                document=file_data["file_id"],
                caption=caption
            )
        elif file_data["file_type"] == "text":
            await update.message.reply_text(
                f"📝 {file_data.get('name', '𝐓𝐞𝐱𝐭')}\n\n{caption_text}\n\n━━━━━━━━━━━━━━━━━━━━━━\n🤖 𝐁𝐨𝐭 𝐛𝐲: {BOT_DISPLAY_NAME}"
            )
    except Exception as e:
        logger.error(f"Error sending file: {e}")
        await update.message.reply_text(
            f"❌ 𝐄𝐫𝐫𝐨𝐫 𝐬𝐞𝐧𝐝𝐢𝐧𝐠 𝐟𝐢𝐥𝐞. 𝐏𝐥𝐞𝐚𝐬𝐞 𝐭𝐫𝐲 𝐚𝐠𝐚𝐢𝐧 𝐥𝐚𝐭𝐞𝐫."
        )

async def send_file_to_user_callback(query, file_id: str):
    """Send file to user via callback."""
    file_data = files_data[file_id]
    
    try:
        caption_text = file_data.get("caption", "")
        caption = f"📁 {file_data.get('name', '𝐅𝐢𝐥𝐞')}\n\n{caption_text}\n\n━━━━━━━━━━━━━━━━━━━━━━\n🤖 𝐁𝐨𝐭 𝐛𝐲: {BOT_DISPLAY_NAME}"
        
        if file_data["file_type"] == "photo":
            await query.message.reply_photo(
                photo=file_data["file_id"],
                caption=caption
            )
        elif file_data["file_type"] == "video":
            await query.message.reply_video(
                video=file_data["file_id"],
                caption=caption
            )
        elif file_data["file_type"] == "document":
            await query.message.reply_document(
                document=file_data["file_id"],
                caption=caption
            )
        elif file_data["file_type"] == "text":
            await query.message.reply_text(
                f"📝 {file_data.get('name', '𝐓𝐞𝐱𝐭')}\n\n{caption_text}\n\n━━━━━━━━━━━━━━━━━━━━━━\n🤖 𝐁𝐨𝐭 𝐛𝐲: {BOT_DISPLAY_NAME}"
            )
    except Exception as e:
        logger.error(f"Error sending file: {e}")
        await query.message.reply_text(
            f"❌ 𝐄𝐫𝐫𝐨𝐫 𝐬𝐞𝐧𝐝𝐢𝐧𝐠 𝐟𝐢𝐥𝐞. 𝐏𝐥𝐞𝐚𝐬𝐞 𝐭𝐫𝐲 𝐚𝐠𝐚𝐢𝐧 𝐥𝐚𝐭𝐞𝐫."
        )

# Admin commands
async def admin_host_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to host text."""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ 𝐘𝐨𝐮 𝐚𝐫𝐞 𝐧𝐨𝐭 𝐚𝐮𝐭𝐡𝐨𝐫𝐢𝐳𝐞𝐝!")
        return
    
    await update.message.reply_text(
        "📝 𝐏𝐥𝐞𝐚𝐬𝐞 𝐬𝐞𝐧𝐝 𝐭𝐡𝐞 𝐭𝐞𝐱𝐭 𝐲𝐨𝐮 𝐰𝐚𝐧𝐭 𝐭𝐨 𝐡𝐨𝐬𝐭:\n"
        "𝐅𝐨𝐫𝐦𝐚𝐭: 𝐓𝐞𝐱𝐭 𝐦𝐞𝐬𝐬𝐚𝐠𝐞 (𝐟𝐢𝐫𝐬𝐭 𝐥𝐢𝐧𝐞 𝐰𝐢𝐥𝐥 𝐛𝐞 𝐮𝐬𝐞𝐝 𝐚𝐬 𝐟𝐢𝐥𝐞𝐧𝐚𝐦𝐞)",
        reply_markup=get_admin_keyboard()
    )
    context.user_data['awaiting_text'] = True

async def admin_host_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to host file with easy process."""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ 𝐘𝐨𝐮 𝐚𝐫𝐞 𝐧𝐨𝐭 𝐚𝐮𝐭𝐡𝐨𝐫𝐢𝐳𝐞𝐝!")
        return
    
    await update.message.reply_text(
        f"📁 𝐄𝐚𝐬𝐲 𝐅𝐢𝐥𝐞 𝐇𝐨𝐬𝐭𝐢𝐧𝐠 𝐒𝐲𝐬𝐭𝐞𝐦\n\n"
        f"𝐏𝐥𝐞𝐚𝐬𝐞 𝐬𝐞𝐧𝐝 𝐦𝐞 𝐭𝐡𝐞 𝐟𝐢𝐥𝐞 𝐲𝐨𝐮 𝐰𝐚𝐧𝐭 𝐭𝐨 𝐡𝐨𝐬𝐭.\n"
        f"𝐈 𝐰𝐢𝐥𝐥 𝐚𝐬𝐤 𝐟𝐨𝐫 𝐧𝐚𝐦𝐞 𝐚𝐧𝐝 𝐜𝐚𝐩𝐭𝐢𝐨𝐧 𝐚𝐟𝐭𝐞𝐫𝐰𝐚𝐫𝐝𝐬.\n\n"
        f"𝐒𝐮𝐩𝐩𝐨𝐫𝐭𝐞𝐝 𝐟𝐢𝐥𝐞𝐬: 𝐃𝐨𝐜𝐮𝐦𝐞𝐧𝐭, 𝐏𝐡𝐨𝐭𝐨, 𝐕𝐢𝐝𝐞𝐨",
        reply_markup=get_admin_keyboard()
    )
    context.user_data['awaiting_file'] = True

async def admin_generate_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate link for a file."""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ 𝐘𝐨𝐮 𝐚𝐫𝐞 𝐧𝐨𝐭 𝐚𝐮𝐭𝐡𝐨𝐫𝐢𝐳𝐞𝐝!")
        return
    
    if not files_data:
        await update.message.reply_text(
            "📭 𝐍𝐨 𝐟𝐢𝐥𝐞𝐬 𝐚𝐯𝐚𝐢𝐥𝐚𝐛𝐥𝐞 𝐭𝐨 𝐠𝐞𝐧𝐞𝐫𝐚𝐭𝐞 𝐥𝐢𝐧𝐤𝐬.\n"
            "𝐅𝐢𝐫𝐬𝐭 𝐡𝐨𝐬𝐭 𝐬𝐨𝐦𝐞 𝐟𝐢𝐥𝐞𝐬.",
            reply_markup=get_admin_keyboard()
        )
        return
    
    keyboard = []
    files_list = list(files_data.items())
    
    for file_id, file_data in files_list[:10]:
        file_name = file_data.get('name', f"𝐅𝐢𝐥𝐞_{file_id[:6]}")
        keyboard.append([InlineKeyboardButton(
            f"📁 {file_name[:20]}",
            callback_data=f"genlink_{file_id}"
        )])
    
    if len(files_list) > 10:
        keyboard.append([InlineKeyboardButton("📋 𝐍𝐞𝐱𝐭 𝐏𝐚𝐠𝐞", callback_data="next_page_1")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"🔗 𝐒𝐞𝐥𝐞𝐜𝐭 𝐚 𝐟𝐢𝐥𝐞 𝐭𝐨 𝐠𝐞𝐧𝐞𝐫𝐚𝐭𝐞 𝐥𝐢𝐧𝐤:\n\n"
        f"𝐂𝐥𝐢𝐜𝐤 𝐨𝐧 𝐚 𝐟𝐢𝐥𝐞 𝐭𝐨 𝐠𝐞𝐧𝐞𝐫𝐚𝐭𝐞 𝐢𝐭𝐬 𝐬𝐡𝐚𝐫𝐢𝐧𝐠 𝐥𝐢𝐧𝐤.\n\n"
        f"🤖 𝐁𝐨𝐭 𝐛𝐲: {BOT_DISPLAY_NAME}",
        reply_markup=reply_markup
    )

async def admin_files_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show list of hosted files."""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ 𝐘𝐨𝐮 𝐚𝐫𝐞 𝐧𝐨𝐭 𝐚𝐮𝐭𝐡𝐨𝐫𝐢𝐳𝐞𝐝!")
        return
    
    if not files_data:
        await update.message.reply_text(
            "📭 𝐍𝐨 𝐟𝐢𝐥𝐞𝐬 𝐡𝐨𝐬𝐭𝐞𝐝 𝐲𝐞𝐭.",
            reply_markup=get_admin_keyboard()
        )
        return
    
    files_list_text = "📁 𝐇𝐨𝐬𝐭𝐞𝐝 𝐅𝐢𝐥𝐞𝐬:\n\n"
    
    for i, (file_id, file_data) in enumerate(files_data.items(), 1):
        file_name = file_data.get('name', f"𝐅𝐢𝐥𝐞_{i}")
        file_type = file_data.get('file_type', '𝐔𝐧𝐤𝐧𝐨𝐰𝐧')
        date = file_data.get('date', '𝐔𝐧𝐤𝐧𝐨𝐰𝐧')
        downloads = file_data.get('downloads', 0)
        
        files_list_text += f"{i}. {file_name}\n"
        files_list_text += f"   𝐓𝐲𝐩𝐞: {file_type} | 📥 {downloads} 𝐝𝐨𝐰𝐧𝐥𝐨𝐚𝐝𝐬\n"
        files_list_text += f"   𝐃𝐚𝐭𝐞: {date}\n"
        files_list_text += f"   🆔: {file_id}\n\n"
    
    files_list_text += f"━━━━━━━━━━━━━━━━━━━━━━\n🤖 𝐁𝐨𝐭 𝐛𝐲: {BOT_DISPLAY_NAME}"
    
    keyboard = [[InlineKeyboardButton("🔗 𝐆𝐞𝐧𝐞𝐫𝐚𝐭𝐞 𝐋𝐢𝐧𝐤", callback_data="generate_link_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        files_list_text,
        reply_markup=reply_markup
    )

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show admin stats."""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ 𝐘𝐨𝐮 𝐚𝐫𝐞 𝐧𝐨𝐭 𝐚𝐮𝐭𝐡𝐨𝐫𝐢𝐳𝐞𝐝!")
        return
    
    total_files = len(files_data)
    total_links = len(links_data)
    total_downloads = sum(file_data.get('downloads', 0) for file_data in files_data.values())
    total_users = len(users_data)
    
    stats_text = (
        f"📈 𝐁𝐨𝐭 𝐒𝐭𝐚𝐭𝐢𝐬𝐭𝐢𝐜𝐬\n\n"
        f"📊 𝐓𝐨𝐭𝐚𝐥 𝐅𝐢𝐥𝐞𝐬: {total_files}\n"
        f"🔗 𝐓𝐨𝐭𝐚𝐥 𝐋𝐢𝐧𝐤𝐬: {total_links}\n"
        f"📥 𝐓𝐨𝐭𝐚𝐥 𝐃𝐨𝐰𝐧𝐥𝐨𝐚𝐝𝐬: {total_downloads}\n"
        f"👥 𝐓𝐨𝐭𝐚𝐥 𝐔𝐬𝐞𝐫𝐬: {total_users}\n"
        f"📢 𝐂𝐡𝐚𝐧𝐧𝐞𝐥𝐬: {len(CHANNELS)}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🤖 𝐁𝐨𝐭 𝐛𝐲: {BOT_DISPLAY_NAME}"
    )
    
    await update.message.reply_text(
        stats_text,
        reply_markup=get_admin_keyboard()
    )

async def admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Broadcast message to all users."""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ 𝐘𝐨𝐮 𝐚𝐫𝐞 𝐧𝐨𝐭 𝐚𝐮𝐭𝐡𝐨𝐫𝐢𝐳𝐞𝐝!")
        return
    
    if not users_data:
        await update.message.reply_text(
            "📭 𝐍𝐨 𝐮𝐬𝐞𝐫𝐬 𝐟𝐨𝐮𝐧𝐝 𝐭𝐨 𝐛𝐫𝐨𝐚𝐝𝐜𝐚𝐬𝐭.",
            reply_markup=get_admin_keyboard()
        )
        return
    
    await update.message.reply_text(
        f"📢 𝐁𝐫𝐨𝐚𝐝𝐜𝐚𝐬𝐭 𝐌𝐨𝐝𝐞\n\n"
        f"𝐓𝐨𝐭𝐚𝐥 𝐔𝐬𝐞𝐫𝐬: {len(users_data)}\n\n"
        f"𝐏𝐥𝐞𝐚𝐬𝐞 𝐬𝐞𝐧𝐝 𝐭𝐡𝐞 𝐦𝐞𝐬𝐬𝐚𝐠𝐞 𝐲𝐨𝐮 𝐰𝐚𝐧𝐭 𝐭𝐨 𝐛𝐫𝐨𝐚𝐝𝐜𝐚𝐬𝐭.\n"
        f"𝐘𝐨𝐮 𝐜𝐚𝐧 𝐬𝐞𝐧𝐝 𝐭𝐞𝐱𝐭, 𝐩𝐡𝐨𝐭𝐨, 𝐯𝐢𝐝𝐞𝐨 𝐨𝐫 𝐝𝐨𝐜𝐮𝐦𝐞𝐧𝐭.\n\n"
        f"𝐓𝐲𝐩𝐞 /𝐜𝐚𝐧𝐜𝐞𝐥 𝐭𝐨 𝐚𝐛𝐨𝐫𝐭.",
        reply_markup=get_admin_keyboard()
    )
    context.user_data['broadcast_mode'] = True

async def handle_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle broadcast message."""
    if update.effective_user.id != ADMIN_ID:
        return
    
    message = update.message
    broadcast_data = context.user_data.get('broadcast_data', {})
    
    if not broadcast_data:
        broadcast_data = {
            'type': 'text',
            'content': None,
            'caption': None
        }
        
        if message.text:
            broadcast_data['type'] = 'text'
            broadcast_data['content'] = message.text
        elif message.photo:
            broadcast_data['type'] = 'photo'
            broadcast_data['content'] = message.photo[-1].file_id
            broadcast_data['caption'] = message.caption
        elif message.video:
            broadcast_data['type'] = 'video'
            broadcast_data['content'] = message.video.file_id
            broadcast_data['caption'] = message.caption
        elif message.document:
            broadcast_data['type'] = 'document'
            broadcast_data['content'] = message.document.file_id
            broadcast_data['caption'] = message.caption
        
        context.user_data['broadcast_data'] = broadcast_data
        
        keyboard = [
            [InlineKeyboardButton("✅ 𝐒𝐞𝐧𝐝 𝐍𝐨𝐰", callback_data="broadcast_confirm")],
            [InlineKeyboardButton("❌ 𝐂𝐚𝐧𝐜𝐞𝐥", callback_data="broadcast_cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await message.reply_text(
            f"📢 𝐁𝐫𝐨𝐚𝐝𝐜𝐚𝐬𝐭 𝐏𝐫𝐞𝐯𝐢𝐞𝐰\n\n"
            f"𝐓𝐲𝐩𝐞: {broadcast_data['type'].upper()}\n"
            f"𝐓𝐨𝐭𝐚𝐥 𝐔𝐬𝐞𝐫𝐬: {len(users_data)}\n\n"
            f"𝐂𝐥𝐢𝐜𝐤 𝐒𝐞𝐧𝐝 𝐍𝐨𝐰 𝐭𝐨 𝐛𝐫𝐨𝐚𝐝𝐜𝐚𝐬𝐭 𝐭𝐡𝐢𝐬 𝐦𝐞𝐬𝐬𝐚𝐠𝐞.",
            reply_markup=reply_markup
        )

async def admin_content_manager(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manage hosted content."""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ 𝐘𝐨𝐮 𝐚𝐫𝐞 𝐧𝐨𝐭 𝐚𝐮𝐭𝐡𝐨𝐫𝐢𝐳𝐞𝐝!")
        return
    
    keyboard = []
    
    if files_data:
        keyboard.append([InlineKeyboardButton("📁 𝐕𝐢𝐞𝐰 𝐀𝐥𝐥 𝐅𝐢𝐥𝐞𝐬", callback_data="view_files_list")])
        keyboard.append([InlineKeyboardButton("🗑️ 𝐃𝐞𝐥𝐞𝐭𝐞 𝐅𝐢𝐥𝐞", callback_data="delete_file_menu")])
        keyboard.append([InlineKeyboardButton("🗑️ 𝐃𝐞𝐥𝐞𝐭𝐞 𝐀𝐥𝐥 𝐅𝐢𝐥𝐞𝐬", callback_data="delete_all_files")])
    
    if links_data:
        keyboard.append([InlineKeyboardButton("🔗 𝐕𝐢𝐞𝐰 𝐀𝐥𝐥 𝐋𝐢𝐧𝐤𝐬", callback_data="view_links_list")])
        keyboard.append([InlineKeyboardButton("🗑️ 𝐃𝐞𝐥𝐞𝐭𝐞 𝐀𝐥𝐥 𝐋𝐢𝐧𝐤𝐬", callback_data="delete_all_links")])
    
    if not files_data and not links_data:
        await update.message.reply_text(
            "📭 𝐍𝐨 𝐜𝐨𝐧𝐭𝐞𝐧𝐭 𝐭𝐨 𝐦𝐚𝐧𝐚𝐠𝐞.\n"
            "𝐇𝐨𝐬𝐭 𝐬𝐨𝐦𝐞 𝐟𝐢𝐥𝐞𝐬 𝐟𝐢𝐫𝐬𝐭.",
            reply_markup=get_admin_keyboard()
        )
        return
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"📋 𝐂𝐨𝐧𝐭𝐞𝐧𝐭 𝐌𝐚𝐧𝐚𝐠𝐞𝐫\n\n"
        f"📁 𝐓𝐨𝐭𝐚𝐥 𝐅𝐢𝐥𝐞𝐬: {len(files_data)}\n"
        f"🔗 𝐓𝐨𝐭𝐚𝐥 𝐋𝐢𝐧𝐤𝐬: {len(links_data)}\n\n"
        f"𝐒𝐞𝐥𝐞𝐜𝐭 𝐚𝐧 𝐨𝐩𝐭𝐢𝐨𝐧:\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🤖 𝐁𝐨𝐭 𝐛𝐲: {BOT_DISPLAY_NAME}",
        reply_markup=reply_markup
    )

async def admin_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin settings menu."""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ 𝐘𝐨𝐮 𝐚𝐫𝐞 𝐧𝐨𝐭 𝐚𝐮𝐭𝐡𝐨𝐫𝐢𝐳𝐞𝐝!")
        return
    
    keyboard = [
        [InlineKeyboardButton("💬 𝐆𝐫𝐨𝐮𝐩 𝐂𝐡𝐚𝐭", callback_data="settings_group")],
        [InlineKeyboardButton("➕ 𝐀𝐝𝐝 𝐀𝐥𝐥𝐨𝐰𝐞𝐝 𝐆𝐫𝐨𝐮𝐩", callback_data="settings_add_group")],
        [InlineKeyboardButton("❌ 𝐑𝐞𝐦𝐨𝐯𝐞 𝐀𝐥𝐥𝐨𝐰𝐞𝐝 𝐆𝐫𝐨𝐮𝐩", callback_data="settings_remove_group")],
        [InlineKeyboardButton("📋 𝐕𝐢𝐞𝐰 𝐀𝐥𝐥𝐨𝐰𝐞𝐝 𝐆𝐫𝐨𝐮𝐩𝐬", callback_data="settings_view_groups")],
        [InlineKeyboardButton("🔙 𝐁𝐚𝐜𝐤", callback_data="settings_back")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    group_status = "✅ 𝐄𝐧𝐚𝐛𝐥𝐞𝐝" if settings_data.get("group_chat_enabled") else "❌ 𝐃𝐢𝐬𝐚𝐛𝐥𝐞𝐝"
    
    await update.message.reply_text(
        f"⚙️ 𝐁𝐨𝐭 𝐒𝐞𝐭𝐭𝐢𝐧𝐠𝐬\n\n"
        f"💬 𝐆𝐫𝐨𝐮𝐩 𝐂𝐡𝐚𝐭: {group_status}\n"
        f"👥 𝐀𝐥𝐥𝐨𝐰𝐞𝐝 𝐆𝐫𝐨𝐮𝐩𝐬: {len(settings_data.get('allowed_groups', []))}\n\n"
        f"𝐒𝐞𝐥𝐞𝐜𝐭 𝐚𝐧 𝐨𝐩𝐭𝐢𝐨𝐧:",
        reply_markup=reply_markup
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all text messages."""
    if not await check_group_permission(update):
        return
    
    user_id = update.effective_user.id
    
    if user_id != ADMIN_ID:
        if not await force_subscription_check(update, context):
            return
    
    message_text = update.message.text
    
    if message_text == "/cancel":
        context.user_data.clear()
        await update.message.reply_text(
            "✅ 𝐀𝐜𝐭𝐢𝐨𝐧 𝐜𝐚𝐧𝐜𝐞𝐥𝐞𝐝.",
            reply_markup=get_admin_keyboard() if user_id == ADMIN_ID else get_user_keyboard()
        )
        return
    
    if context.user_data.get('broadcast_mode'):
        await handle_broadcast(update, context)
        return
    
    if context.user_data.get('awaiting_file_name'):
        file_name = message_text
        context.user_data['temp_file_name'] = file_name
        context.user_data['awaiting_file_name'] = False
        context.user_data['awaiting_file_caption'] = True
        
        await update.message.reply_text(
            f"📝 𝐒𝐭𝐞𝐩 𝟐/𝟐: 𝐀𝐝𝐝 𝐂𝐚𝐩𝐭𝐢𝐨𝐧\n\n"
            f"𝐏𝐥𝐞𝐚𝐬𝐞 𝐬𝐞𝐧𝐝 𝐭𝐡𝐞 𝐜𝐚𝐩𝐭𝐢𝐨𝐧 𝐟𝐨𝐫 𝐭𝐡𝐞 𝐟𝐢𝐥𝐞.\n"
            f"𝐘𝐨𝐮 𝐜𝐚𝐧 𝐬𝐞𝐧𝐝 /𝐬𝐤𝐢𝐩 𝐭𝐨 𝐥𝐞𝐚𝐯𝐞 𝐢𝐭 𝐞𝐦𝐩𝐭𝐲."
        )
        return
    
    if context.user_data.get('awaiting_file_caption'):
        if message_text == "/skip":
            caption = ""
        else:
            caption = message_text
        
        temp_file_id = context.user_data.get('temp_file_id')
        temp_file_type = context.user_data.get('temp_file_type')
        file_name = context.user_data.get('temp_file_name')
        
        if temp_file_id and temp_file_type and file_name:
            unique_id = generate_unique_id()
            files_data[unique_id] = {
                "name": file_name,
                "caption": caption,
                "file_type": temp_file_type,
                "file_id": temp_file_id,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "downloads": 0,
                "accessed_by": {}
            }
            
            save_files_data()
            
            link_id = generate_link_id()
            links_data[link_id] = {
                "file_id": unique_id,
                "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "clicks": 0
            }
            save_links_data()
            
            link_url = f"https://t.me/{BOT_USERNAME}?start={link_id}"
            
            await update.message.reply_text(
                f"✅ 𝐅𝐢𝐥𝐞 𝐇𝐨𝐬𝐭𝐞𝐝 𝐒𝐮𝐜𝐜𝐞𝐬𝐬𝐟𝐮𝐥𝐥𝐲!\n\n"
                f"📁 𝐍𝐚𝐦𝐞: {file_name}\n"
                f"📄 𝐓𝐲𝐩𝐞: {temp_file_type}\n"
                f"🔗 𝐋𝐢𝐧𝐤: {link_url}\n\n"
                f"𝐒𝐡𝐚𝐫𝐞 𝐭𝐡𝐢𝐬 𝐥𝐢𝐧𝐤 𝐰𝐢𝐭𝐡 𝐮𝐬𝐞𝐫𝐬.\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🤖 𝐁𝐨𝐭 𝐛𝐲: {BOT_DISPLAY_NAME}",
                reply_markup=get_admin_keyboard()
            )
            
            context.user_data.clear()
        
        return
    
    if user_id == ADMIN_ID:
        if message_text == "📝 𝐇𝐨𝐬𝐭 𝐓𝐞𝐱𝐭":
            await admin_host_text(update, context)
        elif message_text == "📁 𝐇𝐨𝐬𝐭 𝐅𝐢𝐥𝐞":
            await admin_host_file(update, context)
        elif message_text == "🔗 𝐆𝐞𝐧𝐞𝐫𝐚𝐭𝐞 𝐋𝐢𝐧𝐤":
            await admin_generate_link(update, context)
        elif message_text == "📊 𝐅𝐢𝐥𝐞𝐬 𝐋𝐢𝐬𝐭":
            await admin_files_list(update, context)
        elif message_text == "📈 𝐒𝐭𝐚𝐭𝐬":
            await admin_stats(update, context)
        elif message_text == "📢 𝐁𝐫𝐨𝐚𝐝𝐜𝐚𝐬𝐭":
            await admin_broadcast(update, context)
        elif message_text == "📋 𝐂𝐨𝐧𝐭𝐞𝐧𝐭 𝐌𝐚𝐧𝐚𝐠𝐞𝐫":
            await admin_content_manager(update, context)
        elif message_text == "⚙️ 𝐒𝐞𝐭𝐭𝐢𝐧𝐠𝐬":
            await admin_settings(update, context)
        elif message_text == "❓ 𝐇𝐞𝐥𝐩":
            await help_command(update, context)
        elif context.user_data.get('awaiting_text'):
            text = message_text
            lines = text.split('\n')
            file_name = lines[0][:50] if lines[0].strip() else "𝐓𝐞𝐱𝐭_𝐅𝐢𝐥𝐞"
            caption = text
            
            file_id = generate_unique_id()
            files_data[file_id] = {
                "name": file_name,
                "caption": caption,
                "file_type": "text",
                "file_id": None,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "downloads": 0,
                "accessed_by": {}
            }
            
            save_files_data()
            context.user_data['awaiting_text'] = False
            
            link_id = generate_link_id()
            links_data[link_id] = {
                "file_id": file_id,
                "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "clicks": 0
            }
            save_links_data()
            
            link_url = f"https://t.me/{BOT_USERNAME}?start={link_id}"
            
            await update.message.reply_text(
                f"✅ 𝐓𝐞𝐱𝐭 𝐡𝐨𝐬𝐭𝐞𝐝 𝐬𝐮𝐜𝐜𝐞𝐬𝐬𝐟𝐮𝐥𝐥𝐲!\n\n"
                f"📝 𝐍𝐚𝐦𝐞: {file_name}\n"
                f"🔗 𝐋𝐢𝐧𝐤: {link_url}\n\n"
                f"𝐒𝐡𝐚𝐫𝐞 𝐭𝐡𝐢𝐬 𝐥𝐢𝐧𝐤 𝐰𝐢𝐭𝐡 𝐮𝐬𝐞𝐫𝐬.\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🤖 𝐁𝐨𝐭 𝐛𝐲: {BOT_DISPLAY_NAME}",
                reply_markup=get_admin_keyboard()
            )
        else:
            await update.message.reply_text(
                "𝐏𝐥𝐞𝐚𝐬𝐞 𝐮𝐬𝐞 𝐭𝐡𝐞 𝐦𝐞𝐧𝐮 𝐛𝐮𝐭𝐭𝐨𝐧𝐬 𝐨𝐫 𝐜𝐨𝐦𝐦𝐚𝐧𝐝𝐬.",
                reply_markup=get_admin_keyboard()
            )
    else:
        if message_text == "📁 𝐌𝐲 𝐅𝐢𝐥𝐞𝐬":
            await user_my_files(update, context)
        elif message_text == "❓ 𝐇𝐞𝐥𝐩":
            await help_command(update, context)
        else:
            await update.message.reply_text(
                "𝐔𝐬𝐞 /𝐬𝐭𝐚𝐫𝐭 𝐭𝐨 𝐛𝐞𝐠𝐢𝐧 𝐨𝐫 ❓ 𝐇𝐞𝐥𝐩 𝐟𝐨𝐫 𝐚𝐬𝐬𝐢𝐬𝐭𝐚𝐧𝐜𝐞.",
                reply_markup=get_user_keyboard()
            )

async def user_my_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's accessed files."""
    if not await check_group_permission(update):
        return
    
    user_id = update.effective_user.id
    
    if not await force_subscription_check(update, context):
        return
    
    user_files = []
    for file_id, file_data in files_data.items():
        accessed_by = file_data.get("accessed_by", {})
        if str(user_id) in accessed_by:
            user_files.append((file_id, file_data))
    
    if user_files:
        files_text = "📁 𝐘𝐨𝐮𝐫 𝐀𝐜𝐜𝐞𝐬𝐬𝐞𝐝 𝐅𝐢𝐥𝐞𝐬:\n\n"
        
        for i, (file_id, file_data) in enumerate(user_files, 1):
            file_name = file_data.get('name', f"𝐅𝐢𝐥𝐞_{i}")
            access_date = file_data.get('accessed_by', {}).get(str(user_id), "𝐔𝐧𝐤𝐧𝐨𝐰𝐧")
            
            files_text += f"{i}. {file_name}\n"
            files_text += f"   𝐀𝐜𝐜𝐞𝐬𝐬𝐞𝐝: {access_date}\n\n"
        
        files_text += f"━━━━━━━━━━━━━━━━━━━━━━\n🤖 𝐁𝐨𝐭 𝐛𝐲: {BOT_DISPLAY_NAME}"
        
        await update.message.reply_text(
            files_text,
            reply_markup=get_user_keyboard()
        )
    else:
        await update.message.reply_text(
            f"📭 𝐍𝐨 𝐅𝐢𝐥𝐞𝐬 𝐀𝐜𝐜𝐞𝐬𝐬𝐞𝐝 𝐘𝐞𝐭\n\n"
            f"𝐘𝐨𝐮 𝐡𝐚𝐯𝐞𝐧'𝐭 𝐚𝐜𝐜𝐞𝐬𝐬𝐞𝐝 𝐚𝐧𝐲 𝐟𝐢𝐥𝐞𝐬 𝐲𝐞𝐭.\n"
            f"𝐔𝐬𝐞 /𝐬𝐭𝐚𝐫𝐭 𝐚𝐧𝐝 𝐣𝐨𝐢𝐧 𝐜𝐡𝐚𝐧𝐧𝐞𝐥𝐬 𝐭𝐨 𝐚𝐜𝐜𝐞𝐬𝐬 𝐟𝐢𝐥𝐞𝐬.\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🤖 𝐁𝐨𝐭 𝐛𝐲: {BOT_DISPLAY_NAME}",
            reply_markup=get_user_keyboard()
        )

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle file from admin for hosting with easy process."""
    if not await check_group_permission(update):
        return
    
    if update.effective_user.id != ADMIN_ID:
        return
    
    message = update.message
    
    if context.user_data.get('awaiting_file'):
        file_id = None
        file_type = None
        
        if message.photo:
            file_id = message.photo[-1].file_id
            file_type = "photo"
        elif message.video:
            file_id = message.video.file_id
            file_type = "video"
        elif message.document:
            file_id = message.document.file_id
            file_type = "document"
        else:
            await message.reply_text(
                "❌ 𝐔𝐧𝐬𝐮𝐩𝐩𝐨𝐫𝐭𝐞𝐝 𝐟𝐢𝐥𝐞 𝐭𝐲𝐩𝐞!",
                reply_markup=get_admin_keyboard()
            )
            context.user_data.pop('awaiting_file', None)
            return
        
        context.user_data['temp_file_id'] = file_id
        context.user_data['temp_file_type'] = file_type
        context.user_data['awaiting_file'] = False
        context.user_data['awaiting_file_name'] = True
        
        await message.reply_text(
            f"📝 𝐒𝐭𝐞𝐩 𝟏/𝟐: 𝐄𝐧𝐭𝐞𝐫 𝐅𝐢𝐥𝐞 𝐍𝐚𝐦𝐞\n\n"
            f"𝐏𝐥𝐞𝐚𝐬𝐞 𝐬𝐞𝐧𝐝 𝐭𝐡𝐞 𝐧𝐚𝐦𝐞 𝐟𝐨𝐫 𝐭𝐡𝐢𝐬 𝐟𝐢𝐥𝐞.\n"
            f"𝐄𝐱𝐚𝐦𝐩𝐥𝐞: 𝐌𝐲𝐅𝐢𝐥𝐞.𝐩𝐝𝐟 𝐨𝐫 𝐂𝐨𝐨𝐥 𝐕𝐢𝐝𝐞𝐨"
        )
    elif message.caption and message.caption.startswith('/host'):
        parts = message.caption.split(' ', 2)
        
        if len(parts) < 2:
            await message.reply_text(
                "❌ 𝐅𝐨𝐫𝐦𝐚𝐭: /𝐡𝐨𝐬𝐭 [𝐟𝐢𝐥𝐞𝐧𝐚𝐦𝐞] [𝐜𝐚𝐩𝐭𝐢𝐨𝐧]",
                reply_markup=get_admin_keyboard()
            )
            return
        
        file_name = parts[1]
        caption = parts[2] if len(parts) > 2 else ""
        
        file_id = None
        file_type = None
        
        if message.photo:
            file_id = message.photo[-1].file_id
            file_type = "photo"
        elif message.video:
            file_id = message.video.file_id
            file_type = "video"
        elif message.document:
            file_id = message.document.file_id
            file_type = "document"
        else:
            await message.reply_text("❌ 𝐔𝐧𝐬𝐮𝐩𝐩𝐨𝐫𝐭𝐞𝐝 𝐟𝐢𝐥𝐞 𝐭𝐲𝐩𝐞!", reply_markup=get_admin_keyboard())
            return
        
        unique_id = generate_unique_id()
        files_data[unique_id] = {
            "name": file_name,
            "caption": caption,
            "file_type": file_type,
            "file_id": file_id,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "downloads": 0,
            "accessed_by": {}
        }
        
        save_files_data()
        
        link_id = generate_link_id()
        links_data[link_id] = {
            "file_id": unique_id,
            "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "clicks": 0
        }
        save_links_data()
        
        link_url = f"https://t.me/{BOT_USERNAME}?start={link_id}"
        
        await message.reply_text(
            f"✅ 𝐅𝐢𝐥𝐞 𝐡𝐨𝐬𝐭𝐞𝐝 𝐬𝐮𝐜𝐜𝐞𝐬𝐬𝐟𝐮𝐥𝐥𝐲!\n\n"
            f"📁 𝐍𝐚𝐦𝐞: {file_name}\n"
            f"📄 𝐓𝐲𝐩𝐞: {file_type}\n"
            f"🔗 𝐋𝐢𝐧𝐤: {link_url}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🤖 𝐁𝐨𝐭 𝐛𝐲: {BOT_DISPLAY_NAME}",
            reply_markup=get_admin_keyboard()
        )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callback queries."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    callback_data = query.data
    
    if callback_data == "broadcast_confirm":
        if user_id != ADMIN_ID:
            return
        
        broadcast_data = context.user_data.get('broadcast_data')
        if not broadcast_data:
            await query.edit_message_text("❌ 𝐍𝐨 𝐛𝐫𝐨𝐚𝐝𝐜𝐚𝐬𝐭 𝐝𝐚𝐭𝐚 𝐟𝐨𝐮𝐧𝐝!")
            return
        
        await query.edit_message_text(
            f"📢 𝐁𝐫𝐨𝐚𝐝𝐜𝐚𝐬𝐭𝐢𝐧𝐠...\n\n"
            f"𝐒𝐞𝐧𝐝𝐢𝐧𝐠 𝐦𝐞𝐬𝐬𝐚𝐠𝐞 𝐭𝐨 𝐚𝐥𝐥 𝐮𝐬𝐞𝐫𝐬."
        )
        
        success_count = 0
        fail_count = 0
        
        for user_id_str in users_data.keys():
            try:
                if broadcast_data['type'] == 'text':
                    await context.bot.send_message(
                        chat_id=int(user_id_str),
                        text=broadcast_data['content'] + f"\n\n━━━━━━━━━━━━━━━━━━━━━━\n📢 𝐁𝐫𝐨𝐚𝐝𝐜𝐚𝐬𝐭 𝐌𝐞𝐬𝐬𝐚𝐠𝐞\n🤖 𝐁𝐨𝐭 𝐛𝐲: {BOT_DISPLAY_NAME}"
                    )
                elif broadcast_data['type'] == 'photo':
                    caption = broadcast_data.get('caption', '')
                    caption += f"\n\n━━━━━━━━━━━━━━━━━━━━━━\n📢 𝐁𝐫𝐨𝐚𝐝𝐜𝐚𝐬𝐭 𝐌𝐞𝐬𝐬𝐚𝐠𝐞\n🤖 𝐁𝐨𝐭 𝐛𝐲: {BOT_DISPLAY_NAME}"
                    await context.bot.send_photo(
                        chat_id=int(user_id_str),
                        photo=broadcast_data['content'],
                        caption=caption
                    )
                elif broadcast_data['type'] == 'video':
                    caption = broadcast_data.get('caption', '')
                    caption += f"\n\n━━━━━━━━━━━━━━━━━━━━━━\n📢 𝐁𝐫𝐨𝐚𝐝𝐜𝐚𝐬𝐭 𝐌𝐞𝐬𝐬𝐚𝐠𝐞\n🤖 𝐁𝐨𝐭 𝐛𝐲: {BOT_DISPLAY_NAME}"
                    await context.bot.send_video(
                        chat_id=int(user_id_str),
                        video=broadcast_data['content'],
                        caption=caption
                    )
                elif broadcast_data['type'] == 'document':
                    caption = broadcast_data.get('caption', '')
                    caption += f"\n\n━━━━━━━━━━━━━━━━━━━━━━\n📢 𝐁𝐫𝐨𝐚𝐝𝐜𝐚𝐬𝐭 𝐌𝐞𝐬𝐬𝐚𝐠𝐞\n🤖 𝐁𝐨𝐭 𝐛𝐲: {BOT_DISPLAY_NAME}"
                    await context.bot.send_document(
                        chat_id=int(user_id_str),
                        document=broadcast_data['content'],
                        caption=caption
                    )
                success_count += 1
                await asyncio.sleep(0.05)
            except Exception as e:
                logger.error(f"Broadcast failed for user {user_id_str}: {e}")
                fail_count += 1
        
        await query.message.reply_text(
            f"📢 𝐁𝐫𝐨𝐚𝐝𝐜𝐚𝐬𝐭 𝐂𝐨𝐦𝐩𝐥𝐞𝐭𝐞𝐝!\n\n"
            f"✅ 𝐒𝐮𝐜𝐜𝐞𝐬𝐬: {success_count}\n"
            f"❌ 𝐅𝐚𝐢𝐥𝐞𝐝: {fail_count}\n"
            f"👥 𝐓𝐨𝐭𝐚𝐥: {len(users_data)}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🤖 𝐁𝐨𝐭 𝐛𝐲: {BOT_DISPLAY_NAME}",
            reply_markup=get_admin_keyboard()
        )
        
        context.user_data.pop('broadcast_data', None)
        context.user_data.pop('broadcast_mode', None)
        
    elif callback_data == "broadcast_cancel":
        if user_id != ADMIN_ID:
            return
        
        context.user_data.pop('broadcast_data', None)
        context.user_data.pop('broadcast_mode', None)
        
        await query.edit_message_text(
            "❌ 𝐁𝐫𝐨𝐚𝐝𝐜𝐚𝐬𝐭 𝐜𝐚𝐧𝐜𝐞𝐥𝐞𝐝.",
            reply_markup=get_admin_keyboard()
        )
    
    elif callback_data == "settings_group":
        if user_id != ADMIN_ID:
            return
        
        current = settings_data.get("group_chat_enabled", False)
        settings_data["group_chat_enabled"] = not current
        save_settings_data()
        
        status = "✅ 𝐄𝐧𝐚𝐛𝐥𝐞𝐝" if settings_data["group_chat_enabled"] else "❌ 𝐃𝐢𝐬𝐚𝐛𝐥𝐞𝐝"
        await query.edit_message_text(
            f"✅ 𝐆𝐫𝐨𝐮𝐩 𝐜𝐡𝐚𝐭 𝐢𝐬 𝐧𝐨𝐰 {status}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 𝐁𝐚𝐜𝐤", callback_data="settings_back")]])
        )
    
    elif callback_data == "settings_add_group":
        if user_id != ADMIN_ID:
            return
        
        context.user_data['awaiting_group_id'] = True
        await query.edit_message_text(
            f"📝 𝐀𝐝𝐝 𝐀𝐥𝐥𝐨𝐰𝐞𝐝 𝐆𝐫𝐨𝐮𝐩\n\n"
            f"𝐏𝐥𝐞𝐚𝐬𝐞 𝐬𝐞𝐧𝐝 𝐭𝐡𝐞 𝐠𝐫𝐨𝐮𝐩 𝐈𝐃 𝐲𝐨𝐮 𝐰𝐚𝐧𝐭 𝐭𝐨 𝐚𝐥𝐥𝐨𝐰.\n\n"
            f"𝐘𝐨𝐮 𝐜𝐚𝐧 𝐠𝐞𝐭 𝐠𝐫𝐨𝐮𝐩 𝐈𝐃 𝐛𝐲:\n"
            f"𝟏. 𝐀𝐝𝐝 @username_to_id_bot 𝐭𝐨 𝐭𝐡𝐞 𝐠𝐫𝐨𝐮𝐩\n"
            f"𝟐. 𝐒𝐞𝐧𝐝 /𝐢𝐝 𝐢𝐧 𝐭𝐡𝐞 𝐠𝐫𝐨𝐮𝐩\n\n"
            f"𝐓𝐲𝐩𝐞 /𝐜𝐚𝐧𝐜𝐞𝐥 𝐭𝐨 𝐚𝐛𝐨𝐫𝐭."
        )
    
    elif callback_data == "settings_remove_group":
        if user_id != ADMIN_ID:
            return
        
        allowed = settings_data.get("allowed_groups", [])
        if not allowed:
            await query.edit_message_text(
                "❌ 𝐍𝐨 𝐠𝐫𝐨𝐮𝐩𝐬 𝐚𝐫𝐞 𝐜𝐮𝐫𝐫𝐞𝐧𝐭𝐥𝐲 𝐚𝐥𝐥𝐨𝐰𝐞𝐝.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 𝐁𝐚𝐜𝐤", callback_data="settings_back")]])
            )
            return
        
        keyboard = []
        for group_id in allowed[:10]:
            keyboard.append([InlineKeyboardButton(
                f"❌ {group_id}",
                callback_data=f"remove_group_{group_id}"
            )])
        keyboard.append([InlineKeyboardButton("🔙 𝐁𝐚𝐜𝐤", callback_data="settings_back")])
        
        await query.edit_message_text(
            "📋 𝐒𝐞𝐥𝐞𝐜𝐭 𝐠𝐫𝐨𝐮𝐩 𝐭𝐨 𝐫𝐞𝐦𝐨𝐯𝐞:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif callback_data.startswith("remove_group_"):
        if user_id != ADMIN_ID:
            return
        
        group_id = int(callback_data.replace("remove_group_", ""))
        allowed = settings_data.get("allowed_groups", [])
        if group_id in allowed:
            allowed.remove(group_id)
            settings_data["allowed_groups"] = allowed
            save_settings_data()
            await query.edit_message_text(
                f"✅ 𝐆𝐫𝐨𝐮𝐩 {group_id} 𝐫𝐞𝐦𝐨𝐯𝐞𝐝 𝐟𝐫𝐨𝐦 𝐚𝐥𝐥𝐨𝐰𝐞𝐝 𝐥𝐢𝐬𝐭.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 𝐁𝐚𝐜𝐤", callback_data="settings_back")]])
            )
    
    elif callback_data == "settings_view_groups":
        if user_id != ADMIN_ID:
            return
        
        allowed = settings_data.get("allowed_groups", [])
        if not allowed:
            text = "📋 𝐍𝐨 𝐠𝐫𝐨𝐮𝐩𝐬 𝐚𝐫𝐞 𝐜𝐮𝐫𝐫𝐞𝐧𝐭𝐥𝐲 𝐚𝐥𝐥𝐨𝐰𝐞𝐝."
        else:
            text = "📋 𝐀𝐥𝐥𝐨𝐰𝐞𝐝 𝐆𝐫𝐨𝐮𝐩𝐬:\n\n"
            for i, group_id in enumerate(allowed, 1):
                text += f"{i}. {group_id}\n"
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 𝐁𝐚𝐜𝐤", callback_data="settings_back")]])
        )
    
    elif callback_data == "settings_back":
        if user_id != ADMIN_ID:
            return
        
        keyboard = [
            [InlineKeyboardButton("💬 𝐆𝐫𝐨𝐮𝐩 𝐂𝐡𝐚𝐭", callback_data="settings_group")],
            [InlineKeyboardButton("➕ 𝐀𝐝𝐝 𝐀𝐥𝐥𝐨𝐰𝐞𝐝 𝐆𝐫𝐨𝐮𝐩", callback_data="settings_add_group")],
            [InlineKeyboardButton("❌ 𝐑𝐞𝐦𝐨𝐯𝐞 𝐀𝐥𝐥𝐨𝐰𝐞𝐝 𝐆𝐫𝐨𝐮𝐩", callback_data="settings_remove_group")],
            [InlineKeyboardButton("📋 𝐕𝐢𝐞𝐰 𝐀𝐥𝐥𝐨𝐰𝐞𝐝 𝐆𝐫𝐨𝐮𝐩𝐬", callback_data="settings_view_groups")],
            [InlineKeyboardButton("🔙 𝐁𝐚𝐜𝐤", callback_data="settings_back")]
        ]
        
        group_status = "✅ 𝐄𝐧𝐚𝐛𝐥𝐞𝐝" if settings_data.get("group_chat_enabled") else "❌ 𝐃𝐢𝐬𝐚𝐛𝐥𝐞𝐝"
        
        await query.edit_message_text(
            f"⚙️ 𝐁𝐨𝐭 𝐒𝐞𝐭𝐭𝐢𝐧𝐠𝐬\n\n"
            f"💬 𝐆𝐫𝐨𝐮𝐩 𝐂𝐡𝐚𝐭: {group_status}\n"
            f"👥 𝐀𝐥𝐥𝐨𝐰𝐞𝐝 𝐆𝐫𝐨𝐮𝐩𝐬: {len(settings_data.get('allowed_groups', []))}\n\n"
            f"𝐒𝐞𝐥𝐞𝐜𝐭 𝐚𝐧 𝐨𝐩𝐭𝐢𝐨𝐧:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif callback_data.startswith("genlink_"):
        file_id = callback_data.replace("genlink_", "")
        
        if file_id not in files_data:
            await query.edit_message_text("❌ 𝐅𝐢𝐥𝐞 𝐧𝐨𝐭 𝐟𝐨𝐮𝐧𝐝!")
            return
        
        link_id = generate_link_id()
        links_data[link_id] = {
            "file_id": file_id,
            "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "clicks": 0
        }
        save_links_data()
        
        file_data = files_data[file_id]
        link_url = f"https://t.me/{BOT_USERNAME}?start={link_id}"
        
        await query.edit_message_text(
            f"✅ 𝐋𝐢𝐧𝐤 𝐠𝐞𝐧𝐞𝐫𝐚𝐭𝐞𝐝 𝐬𝐮𝐜𝐜𝐞𝐬𝐬𝐟𝐮𝐥𝐥𝐲!\n\n"
            f"📁 𝐅𝐢𝐥𝐞: {file_data.get('name', '𝐔𝐧𝐧𝐚𝐦𝐞𝐝')}\n"
            f"🔗 𝐋𝐢𝐧𝐤: {link_url}\n\n"
            f"𝐒𝐡𝐚𝐫𝐞 𝐭𝐡𝐢𝐬 𝐥𝐢𝐧𝐤 𝐰𝐢𝐭𝐡 𝐮𝐬𝐞𝐫𝐬.\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🤖 𝐁𝐨𝐭 𝐛𝐲: {BOT_DISPLAY_NAME}"
        )
    
    elif callback_data == "generate_link_menu":
        await admin_generate_link_callback(query, context)
    
    elif callback_data == "view_files_list":
        await admin_files_list_callback(query, context)
    
    elif callback_data == "view_links_list":
        await admin_links_list_callback(query, context)
    
    elif callback_data == "delete_file_menu":
        await admin_delete_file_menu(query, context)
    
    elif callback_data.startswith("delete_file_"):
        file_id = callback_data.replace("delete_file_", "")
        if file_id in files_data:
            links_to_delete = []
            for link_id, link_data in links_data.items():
                if link_data["file_id"] == file_id:
                    links_to_delete.append(link_id)
            
            for link_id in links_to_delete:
                del links_data[link_id]
            
            del files_data[file_id]
            save_files_data()
            save_links_data()
            
            await query.edit_message_text(
                "✅ 𝐅𝐢𝐥𝐞 𝐝𝐞𝐥𝐞𝐭𝐞𝐝 𝐬𝐮𝐜𝐜𝐞𝐬𝐬𝐟𝐮𝐥𝐥𝐲!"
            )
    
    elif callback_data == "delete_all_files":
        if user_id == ADMIN_ID:
            files_data.clear()
            links_data.clear()
            save_files_data()
            save_links_data()
            await query.edit_message_text(
                f"✅ 𝐀𝐥𝐥 𝐟𝐢𝐥𝐞𝐬 𝐚𝐧𝐝 𝐥𝐢𝐧𝐤𝐬 𝐝𝐞𝐥𝐞𝐭𝐞𝐝 𝐬𝐮𝐜𝐜𝐞𝐬𝐬𝐟𝐮𝐥𝐥𝐲!\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🤖 𝐁𝐨𝐭 𝐛𝐲: {BOT_DISPLAY_NAME}"
            )
    
    elif callback_data == "delete_all_links":
        if user_id == ADMIN_ID:
            links_data.clear()
            save_links_data()
            await query.edit_message_text(
                f"✅ 𝐀𝐥𝐥 𝐥𝐢𝐧𝐤𝐬 𝐝𝐞𝐥𝐞𝐭𝐞𝐝 𝐬𝐮𝐜𝐜𝐞𝐬𝐬𝐟𝐮𝐥𝐥𝐲!\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🤖 𝐁𝐨𝐭 𝐛𝐲: {BOT_DISPLAY_NAME}"
            )
    
    elif callback_data == "show_all_files":
        await show_all_files_callback(query, context)
    
    elif callback_data.startswith("next_page_"):
        page = int(callback_data.replace("next_page_", ""))
        await show_files_page(query, context, page)

async def admin_generate_link_callback(query, context: ContextTypes.DEFAULT_TYPE):
    """Generate link menu via callback."""
    if not files_data:
        await query.edit_message_text(
            "📭 𝐍𝐨 𝐟𝐢𝐥𝐞𝐬 𝐚𝐯𝐚𝐢𝐥𝐚𝐛𝐥𝐞!"
        )
        return
    
    keyboard = []
    files_list = list(files_data.items())
    
    for file_id, file_data in files_list[:10]:
        file_name = file_data.get('name', f"𝐅𝐢𝐥𝐞_{file_id[:6]}")
        keyboard.append([InlineKeyboardButton(
            f"📁 {file_name[:20]}",
            callback_data=f"genlink_{file_id}"
        )])
    
    if len(files_list) > 10:
        keyboard.append([InlineKeyboardButton("📋 𝐍𝐞𝐱𝐭 𝐏𝐚𝐠𝐞", callback_data="next_page_1")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"🔗 𝐒𝐞𝐥𝐞𝐜𝐭 𝐚 𝐟𝐢𝐥𝐞 𝐭𝐨 𝐠𝐞𝐧𝐞𝐫𝐚𝐭𝐞 𝐥𝐢𝐧𝐤:",
        reply_markup=reply_markup
    )

async def admin_files_list_callback(query, context: ContextTypes.DEFAULT_TYPE):
    """Show files list via callback."""
    if not files_data:
        await query.edit_message_text(
            "📭 𝐍𝐨 𝐟𝐢𝐥𝐞𝐬 𝐡𝐨𝐬𝐭𝐞𝐝 𝐲𝐞𝐭!"
        )
        return
    
    files_list_text = "📁 𝐇𝐨𝐬𝐭𝐞𝐝 𝐅𝐢𝐥𝐞𝐬:\n\n"
    
    for i, (file_id, file_data) in enumerate(files_data.items(), 1):
        file_name = file_data.get('name', f"𝐅𝐢𝐥𝐞_{i}")
        file_type = file_data.get('file_type', '𝐔𝐧𝐤𝐧𝐨𝐰𝐧')
        downloads = file_data.get('downloads', 0)
        
        files_list_text += f"{i}. {file_name}\n"
        files_list_text += f"   𝐓𝐲𝐩𝐞: {file_type} | 📥 {downloads} 𝐝𝐨𝐰𝐧𝐥𝐨𝐚𝐝𝐬\n\n"
    
    files_list_text += f"━━━━━━━━━━━━━━━━━━━━━━\n🤖 𝐁𝐨𝐭 𝐛𝐲: {BOT_DISPLAY_NAME}"
    
    await query.edit_message_text(files_list_text)

async def admin_links_list_callback(query, context: ContextTypes.DEFAULT_TYPE):
    """Show links list via callback."""
    if not links_data:
        await query.edit_message_text(
            "🔗 𝐍𝐨 𝐥𝐢𝐧𝐤𝐬 𝐠𝐞𝐧𝐞𝐫𝐚𝐭𝐞𝐝 𝐲𝐞𝐭!"
        )
        return
    
    links_list_text = "🔗 𝐆𝐞𝐧𝐞𝐫𝐚𝐭𝐞𝐝 𝐋𝐢𝐧𝐤𝐬:\n\n"
    
    for i, (link_id, link_data) in enumerate(links_data.items(), 1):
        file_id = link_data["file_id"]
        file_name = files_data.get(file_id, {}).get('name', '𝐔𝐧𝐤𝐧𝐨𝐰𝐧')
        created = link_data.get('created', '𝐔𝐧𝐤𝐧𝐨𝐰𝐧')
        clicks = link_data.get('clicks', 0)
        
        link_url = f"https://t.me/{BOT_USERNAME}?start={link_id}"
        
        links_list_text += f"{i}. {file_name}\n"
        links_list_text += f"   🔗 {link_url}\n"
        links_list_text += f"   📅 {created} | 👁️ {clicks} 𝐜𝐥𝐢𝐜𝐤𝐬\n\n"
    
    links_list_text += f"━━━━━━━━━━━━━━━━━━━━━━\n🤖 𝐁𝐨𝐭 𝐛𝐲: {BOT_DISPLAY_NAME}"
    
    await query.edit_message_text(links_list_text)

async def admin_delete_file_menu(query, context: ContextTypes.DEFAULT_TYPE):
    """Show delete file menu."""
    if not files_data:
        await query.edit_message_text(
            "📭 𝐍𝐨 𝐟𝐢𝐥𝐞𝐬 𝐭𝐨 𝐝𝐞𝐥𝐞𝐭𝐞!"
        )
        return
    
    keyboard = []
    files_list = list(files_data.items())[:10]
    
    for file_id, file_data in files_list:
        file_name = file_data.get('name', f"𝐅𝐢𝐥𝐞_{file_id[:6]}")
        keyboard.append([InlineKeyboardButton(
            f"🗑️ {file_name[:20]}",
            callback_data=f"delete_file_{file_id}"
        )])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"🗑️ 𝐒𝐞𝐥𝐞𝐜𝐭 𝐚 𝐟𝐢𝐥𝐞 𝐭𝐨 𝐝𝐞𝐥𝐞𝐭𝐞:",
        reply_markup=reply_markup
    )

async def show_all_files_callback(query, context: ContextTypes.DEFAULT_TYPE):
    """Show all files for link generation."""
    if not files_data:
        await query.edit_message_text(
            "📭 𝐍𝐨 𝐟𝐢𝐥𝐞𝐬 𝐚𝐯𝐚𝐢𝐥𝐚𝐛𝐥𝐞!"
        )
        return
    
    keyboard = []
    all_files = list(files_data.items())
    
    for file_id, file_data in all_files[:10]:
        file_name = file_data.get('name', f"𝐅𝐢𝐥𝐞_{file_id[:6]}")
        keyboard.append([InlineKeyboardButton(
            f"📁 {file_name[:20]}",
            callback_data=f"genlink_{file_id}"
        )])
    
    if len(all_files) > 10:
        keyboard.append([InlineKeyboardButton("📋 𝐍𝐞𝐱𝐭 𝐏𝐚𝐠𝐞", callback_data="next_page_1")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"🔗 𝐒𝐞𝐥𝐞𝐜𝐭 𝐚 𝐟𝐢𝐥𝐞 𝐭𝐨 𝐠𝐞𝐧𝐞𝐫𝐚𝐭𝐞 𝐥𝐢𝐧𝐤:",
        reply_markup=reply_markup
    )

async def show_files_page(query, context: ContextTypes.DEFAULT_TYPE, page: int):
    """Show paginated files list."""
    if not files_data:
        await query.edit_message_text(
            "📭 𝐍𝐨 𝐟𝐢𝐥𝐞𝐬 𝐚𝐯𝐚𝐢𝐥𝐚𝐛𝐥𝐞!"
        )
        return
    
    files_per_page = 10
    all_files = list(files_data.items())
    start_idx = page * files_per_page
    end_idx = start_idx + files_per_page
    current_files = all_files[start_idx:end_idx]
    
    keyboard = []
    for file_id, file_data in current_files:
        file_name = file_data.get('name', f"𝐅𝐢𝐥𝐞_{file_id[:6]}")
        keyboard.append([InlineKeyboardButton(
            f"📁 {file_name[:20]}",
            callback_data=f"genlink_{file_id}"
        )])
    
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("◀️ 𝐏𝐫𝐞𝐯", callback_data=f"next_page_{page-1}"))
    if end_idx < len(all_files):
        nav_buttons.append(InlineKeyboardButton("𝐍𝐞𝐱𝐭 ▶️", callback_data=f"next_page_{page+1}"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"🔗 𝐒𝐞𝐥𝐞𝐜𝐭 𝐚 𝐟𝐢𝐥𝐞 (𝐏𝐚𝐠𝐞 {page+1}):",
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a help message."""
    if not await check_group_permission(update):
        return
    
    user_id = update.effective_user.id
    
    if user_id != ADMIN_ID:
        if not await force_subscription_check(update, context):
            return
    
    if user_id == ADMIN_ID:
        help_text = (
            f"🤖 𝐀𝐝𝐦𝐢𝐧 𝐇𝐞𝐥𝐩 𝐌𝐞𝐧𝐮\n\n"
            f"𝐌𝐞𝐧𝐮 𝐁𝐮𝐭𝐭𝐨𝐧𝐬:\n"
            f"📝 𝐇𝐨𝐬𝐭 𝐓𝐞𝐱𝐭 - 𝐇𝐨𝐬𝐭 𝐭𝐞𝐱𝐭 𝐦𝐞𝐬𝐬𝐚𝐠𝐞𝐬\n"
            f"📁 𝐇𝐨𝐬𝐭 𝐅𝐢𝐥𝐞 - 𝐇𝐨𝐬𝐭 𝐟𝐢𝐥𝐞𝐬 (𝐞𝐚𝐬𝐲 𝐦𝐨𝐝𝐞)\n"
            f"🔗 𝐆𝐞𝐧𝐞𝐫𝐚𝐭𝐞 𝐋𝐢𝐧𝐤 - 𝐂𝐫𝐞𝐚𝐭𝐞 𝐬𝐡𝐚𝐫𝐞𝐚𝐛𝐥𝐞 𝐥𝐢𝐧𝐤𝐬\n"
            f"📊 𝐅𝐢𝐥𝐞𝐬 𝐋𝐢𝐬𝐭 - 𝐕𝐢𝐞𝐰 𝐚𝐥𝐥 𝐡𝐨𝐬𝐭𝐞𝐝 𝐟𝐢𝐥𝐞𝐬\n"
            f"📈 𝐒𝐭𝐚𝐭𝐬 - 𝐕𝐢𝐞𝐰 𝐛𝐨𝐭 𝐬𝐭𝐚𝐭𝐢𝐬𝐭𝐢𝐜𝐬\n"
            f"📋 𝐂𝐨𝐧𝐭𝐞𝐧𝐭 𝐌𝐚𝐧𝐚𝐠𝐞𝐫 - 𝐌𝐚𝐧𝐚𝐠𝐞 𝐜𝐨𝐧𝐭𝐞𝐧𝐭\n"
            f"📢 𝐁𝐫𝐨𝐚𝐝𝐜𝐚𝐬𝐭 - 𝐁𝐫𝐨𝐚𝐝𝐜𝐚𝐬𝐭 𝐦𝐞𝐬𝐬𝐚𝐠𝐞𝐬 𝐭𝐨 𝐚𝐥𝐥 𝐮𝐬𝐞𝐫𝐬\n"
            f"⚙️ 𝐒𝐞𝐭𝐭𝐢𝐧𝐠𝐬 - 𝐁𝐨𝐭 𝐬𝐞𝐭𝐭𝐢𝐧𝐠𝐬 (𝐠𝐫𝐨𝐮𝐩 𝐩𝐞𝐫𝐦𝐢𝐬𝐬𝐢𝐨𝐧𝐬)\n\n"
            f"𝐄𝐚𝐬𝐲 𝐅𝐢𝐥𝐞 𝐇𝐨𝐬𝐭𝐢𝐧𝐠:\n"
            f"𝟏. 𝐂𝐥𝐢𝐜𝐤 𝐇𝐨𝐬𝐭 𝐅𝐢𝐥𝐞\n"
            f"𝟐. 𝐒𝐞𝐧𝐝 𝐭𝐡𝐞 𝐟𝐢𝐥𝐞\n"
            f"𝟑. 𝐄𝐧𝐭𝐞𝐫 𝐟𝐢𝐥𝐞 𝐧𝐚𝐦𝐞\n"
            f"𝟒. 𝐄𝐧𝐭𝐞𝐫 𝐜𝐚𝐩𝐭𝐢𝐨𝐧 (𝐨𝐩𝐭𝐢𝐨𝐧𝐚𝐥)\n"
            f"𝟓. 𝐋𝐢𝐧𝐤 𝐚𝐮𝐭𝐨𝐦𝐚𝐭𝐢𝐜𝐚𝐥𝐥𝐲 𝐠𝐞𝐧𝐞𝐫𝐚𝐭𝐞𝐝\n\n"
            f"𝐂𝐨𝐦𝐦𝐚𝐧𝐝𝐬:\n"
            f"/𝐜𝐚𝐧𝐜𝐞𝐥 - 𝐂𝐚𝐧𝐜𝐞𝐥 𝐜𝐮𝐫𝐫𝐞𝐧𝐭 𝐚𝐜𝐭𝐢𝐨𝐧\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🤖 𝐁𝐨𝐭 𝐛𝐲: {BOT_DISPLAY_NAME}"
        )
        reply_markup = get_admin_keyboard()
    else:
        help_text = (
            f"🤖 𝐔𝐬𝐞𝐫 𝐇𝐞𝐥𝐩\n\n"
            f"𝐇𝐨𝐰 𝐭𝐨 𝐠𝐞𝐭 𝐟𝐢𝐥𝐞𝐬:\n"
            f"𝟏. 𝐆𝐞𝐭 𝐚 𝐟𝐢𝐥𝐞 𝐥𝐢𝐧𝐤 𝐟𝐫𝐨𝐦 𝐚𝐝𝐦𝐢𝐧\n"
            f"𝟐. 𝐂𝐥𝐢𝐜𝐤 𝐭𝐡𝐞 𝐥𝐢𝐧𝐤 𝐭𝐨 𝐨𝐩𝐞𝐧 𝐛𝐨𝐭\n"
            f"𝟑. 𝐉𝐨𝐢𝐧 𝐚𝐥𝐥 𝐫𝐞𝐪𝐮𝐢𝐫𝐞𝐝 𝐜𝐡𝐚𝐧𝐧𝐞𝐥𝐬\n"
            f"𝟒. 𝐂𝐥𝐢𝐜𝐤 𝐕𝐞𝐫𝐢𝐟𝐲 𝐒𝐮𝐛𝐬𝐜𝐫𝐢𝐩𝐭𝐢𝐨𝐧\n"
            f"𝟓. 𝐆𝐞𝐭 𝐲𝐨𝐮𝐫 𝐟𝐢𝐥𝐞 𝐢𝐧𝐬𝐭𝐚𝐧𝐭𝐥𝐲\n\n"
            f"𝐂𝐨𝐦𝐦𝐚𝐧𝐝𝐬:\n"
            f"/𝐬𝐭𝐚𝐫𝐭 - 𝐒𝐭𝐚𝐫𝐭 𝐛𝐨𝐭\n"
            f"📁 𝐌𝐲 𝐅𝐢𝐥𝐞𝐬 - 𝐕𝐢𝐞𝐰 𝐲𝐨𝐮𝐫 𝐚𝐜𝐜𝐞𝐬𝐬𝐞𝐝 𝐟𝐢𝐥𝐞𝐬\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🤖 𝐁𝐨𝐭 𝐛𝐲: {BOT_DISPLAY_NAME}"
        )
        
        reply_markup = get_user_keyboard()
    
    await update.message.reply_text(
        help_text,
        reply_markup=reply_markup
    )

def run_bot():
    """Run the Telegram bot in the main thread."""
    # Create the Application
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("host_text", admin_host_text))
    application.add_handler(CommandHandler("stats", admin_stats))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("cancel", handle_message))
    
    application.add_handler(CallbackQueryHandler(verify_callback, pattern="^(verify_subscription|verify_file_)"))
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    application.add_handler(MessageHandler(
        filters.PHOTO | filters.VIDEO | filters.Document.ALL, 
        handle_file
    ))
    
    # Run the bot (this will block)
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    clear_terminal()
    show_banner()
    
    # Start Flask in a separate thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Run the bot in the main thread
    run_bot()
