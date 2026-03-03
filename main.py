# ============================================================
# 🔥 RUHI X AI - GOD LEVEL AI PLATFORM
# ============================================================
# Single File Complete Application
# Made by @RUHI_VIG_QNR
# ============================================================

import os
import json
import time
import random
import threading
import hashlib
import re
import sqlite3
import logging
import asyncio
import requests
from datetime import datetime, timedelta
from functools import wraps
from collections import defaultdict

from flask import (
    Flask, request, jsonify, render_template_string,
    session, redirect, url_for, Response, send_file
)
from flask_socketio import SocketIO, emit, join_room, leave_room

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================
# DATABASE SETUP
# ============================================================

DB_PATH = os.environ.get('DB_PATH', '/opt/render/project/src/ruhi_ai.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def init_database():
    conn = get_db()
    c = conn.cursor()

    # API Keys Table
    c.execute('''CREATE TABLE IF NOT EXISTS api_keys (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key_name TEXT,
        api_key TEXT NOT NULL,
        provider TEXT DEFAULT 'groq',
        is_active INTEGER DEFAULT 1,
        usage_count INTEGER DEFAULT 0,
        max_usage INTEGER DEFAULT 1000,
        added_by TEXT DEFAULT 'admin',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_used TIMESTAMP
    )''')

    # Users Table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT UNIQUE NOT NULL,
        username TEXT,
        platform TEXT DEFAULT 'web',
        language TEXT DEFAULT 'hinglish',
        persona TEXT DEFAULT 'polite_girl',
        model TEXT DEFAULT 'llama-3.3-70b-versatile',
        message_count INTEGER DEFAULT 0,
        custom_api_key TEXT,
        bot_token TEXT,
        bot_name TEXT DEFAULT 'Ruhi',
        bot_active INTEGER DEFAULT 0,
        memory_limit INTEGER DEFAULT 50,
        city TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # Chat Memory Table
    c.execute('''CREATE TABLE IF NOT EXISTS chat_memory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        chat_id TEXT,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        platform TEXT DEFAULT 'web',
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # Bot Instances Table
    c.execute('''CREATE TABLE IF NOT EXISTS bot_instances (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        owner_id TEXT NOT NULL,
        bot_token TEXT UNIQUE NOT NULL,
        bot_username TEXT,
        bot_name TEXT DEFAULT 'Ruhi',
        persona TEXT DEFAULT 'polite_girl',
        language TEXT DEFAULT 'hinglish',
        model TEXT DEFAULT 'llama-3.3-70b-versatile',
        system_prompt TEXT,
        is_active INTEGER DEFAULT 1,
        group_memory INTEGER DEFAULT 20,
        private_memory INTEGER DEFAULT 50,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # Knowledge Base Table
    c.execute('''CREATE TABLE IF NOT EXISTS knowledge_base (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT NOT NULL,
        category TEXT,
        question TEXT,
        answer TEXT NOT NULL,
        tags TEXT,
        language TEXT DEFAULT 'hi',
        quality_score REAL DEFAULT 0.5,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # Admin Settings
    c.execute('''CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # Analytics
    c.execute('''CREATE TABLE IF NOT EXISTS analytics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_type TEXT NOT NULL,
        user_id TEXT,
        data TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # External Knowledge Sources
    c.execute('''CREATE TABLE IF NOT EXISTS knowledge_sources (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        url TEXT,
        source_type TEXT DEFAULT 'api',
        is_active INTEGER DEFAULT 1,
        config TEXT,
        last_synced TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # Default admin settings
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
              ('admin_password', 'RUHIVIGQNR'))
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
              ('admin_username', 'RUHIVIGQNR'))
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
              ('max_api_keys', '12000'))
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
              ('default_model', 'llama-3.3-70b-versatile'))
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
              ('background_video', 'https://cdn.pixabay.com/video/2024/03/21/205164-925757498_large.mp4'))
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
              ('background_music', 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3'))

    # Insert default knowledge sources (Open Source Databases)
    default_sources = [
        ('Wikipedia API', 'https://en.wikipedia.org/api/rest_v1', 'api'),
        ('DuckDuckGo Instant', 'https://api.duckduckgo.com', 'api'),
        ('Open Trivia DB', 'https://opentdb.com/api.php', 'api'),
        ('Quotable API', 'https://api.quotable.io', 'api'),
        ('Dictionary API', 'https://api.dictionaryapi.dev/api/v2/entries', 'api'),
        ('Numbers API', 'http://numbersapi.com', 'api'),
        ('Advice Slip', 'https://api.adviceslip.com/advice', 'api'),
        ('Useless Facts', 'https://uselessfacts.jsph.pl/api/v2/facts/random', 'api'),
        ('Cat Facts', 'https://catfact.ninja/fact', 'api'),
        ('Chuck Norris', 'https://api.chucknorris.io/jokes/random', 'api'),
        ('Bored API', 'https://www.boredapi.com/api/activity', 'api'),
        ('Dog Facts', 'https://dog-api.kinduff.com/api/facts', 'api'),
        ('Kanye Quotes', 'https://api.kanye.rest', 'api'),
        ('Random User', 'https://randomuser.me/api', 'api'),
        ('IP API', 'https://ipapi.co/json', 'api'),
        ('Joke API', 'https://v2.jokeapi.dev/joke/Any', 'api'),
        ('Affirmations', 'https://www.affirmations.dev', 'api'),
        ('StackOverflow', 'https://api.stackexchange.com/2.3', 'api'),
        ('GitHub API', 'https://api.github.com', 'api'),
        ('Reddit API', 'https://www.reddit.com/r/all.json', 'api'),
    ]
    for name, url, stype in default_sources:
        c.execute("INSERT OR IGNORE INTO knowledge_sources (name, url, source_type) VALUES (?, ?, ?)",
                  (name, url, stype))

    conn.commit()
    conn.close()
    logger.info("✅ Database initialized successfully!")

# ============================================================
# KNOWLEDGE AGGREGATOR - 20 Sources se Search
# ============================================================

class KnowledgeAggregator:
    """20 Open Source Databases se search karke answer compile karta hai"""

    @staticmethod
    def search_wikipedia(query):
        try:
            url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{query.replace(' ', '_')}"
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                data = r.json()
                return data.get('extract', '')[:500]
        except:
            pass
        return ''

    @staticmethod
    def search_duckduckgo(query):
        try:
            url = f"https://api.duckduckgo.com/?q={query}&format=json&no_html=1"
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                data = r.json()
                abstract = data.get('AbstractText', '')
                answer = data.get('Answer', '')
                return abstract or answer or ''
        except:
            pass
        return ''

    @staticmethod
    def search_dictionary(word):
        try:
            url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, list) and len(data) > 0:
                    meanings = data[0].get('meanings', [])
                    result = []
                    for m in meanings[:2]:
                        part = m.get('partOfSpeech', '')
                        defs = m.get('definitions', [])[:2]
                        for d in defs:
                            result.append(f"{part}: {d.get('definition', '')}")
                    return ' | '.join(result)
        except:
            pass
        return ''

    @staticmethod
    def get_random_joke():
        try:
            r = requests.get("https://v2.jokeapi.dev/joke/Any?type=single", timeout=5)
            if r.status_code == 200:
                data = r.json()
                return data.get('joke', '')
        except:
            pass
        return ''

    @staticmethod
    def get_advice():
        try:
            r = requests.get("https://api.adviceslip.com/advice", timeout=5)
            if r.status_code == 200:
                data = r.json()
                return data.get('slip', {}).get('advice', '')
        except:
            pass
        return ''

    @staticmethod
    def get_random_fact():
        try:
            r = requests.get("https://uselessfacts.jsph.pl/api/v2/facts/random", timeout=5)
            if r.status_code == 200:
                data = r.json()
                return data.get('text', '')
        except:
            pass
        return ''

    @staticmethod
    def get_quote():
        try:
            r = requests.get("https://api.quotable.io/random", timeout=5)
            if r.status_code == 200:
                data = r.json()
                return f'"{data.get("content", "")}" - {data.get("author", "")}'
        except:
            pass
        return ''

    @staticmethod
    def get_affirmation():
        try:
            r = requests.get("https://www.affirmations.dev", timeout=5)
            if r.status_code == 200:
                return r.json().get('affirmation', '')
        except:
            pass
        return ''

    @staticmethod
    def search_stackoverflow(query):
        try:
            url = f"https://api.stackexchange.com/2.3/search/excerpts?order=desc&sort=relevance&q={query}&site=stackoverflow&pagesize=3"
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                items = r.json().get('items', [])
                results = []
                for item in items[:2]:
                    title = item.get('title', '')
                    excerpt = item.get('excerpt', '')[:200]
                    results.append(f"{title}: {excerpt}")
                return ' | '.join(results)
        except:
            pass
        return ''

    @staticmethod
    def search_github(query):
        try:
            url = f"https://api.github.com/search/repositories?q={query}&sort=stars&per_page=3"
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                items = r.json().get('items', [])
                results = []
                for item in items[:2]:
                    name = item.get('full_name', '')
                    desc = item.get('description', '')[:100]
                    stars = item.get('stargazers_count', 0)
                    results.append(f"{name} (⭐{stars}): {desc}")
                return ' | '.join(results)
        except:
            pass
        return ''

    @staticmethod
    def get_number_fact(number='random'):
        try:
            r = requests.get(f"http://numbersapi.com/{number}", timeout=5)
            if r.status_code == 200:
                return r.text
        except:
            pass
        return ''

    @staticmethod
    def get_cat_fact():
        try:
            r = requests.get("https://catfact.ninja/fact", timeout=5)
            if r.status_code == 200:
                return r.json().get('fact', '')
        except:
            pass
        return ''

    @staticmethod
    def get_dog_fact():
        try:
            r = requests.get("https://dog-api.kinduff.com/api/facts", timeout=5)
            if r.status_code == 200:
                facts = r.json().get('facts', [])
                return facts[0] if facts else ''
        except:
            pass
        return ''

    @staticmethod
    def get_trivia():
        try:
            r = requests.get("https://opentdb.com/api.php?amount=1&type=multiple", timeout=5)
            if r.status_code == 200:
                results = r.json().get('results', [])
                if results:
                    q = results[0]
                    return f"Q: {q.get('question', '')} | A: {q.get('correct_answer', '')}"
        except:
            pass
        return ''

    @staticmethod
    def get_bored_activity():
        try:
            r = requests.get("https://www.boredapi.com/api/activity", timeout=5)
            if r.status_code == 200:
                return r.json().get('activity', '')
        except:
            pass
        return ''

    @staticmethod
    def search_reddit(query):
        try:
            headers = {'User-Agent': 'RuhiAI/1.0'}
            r = requests.get(f"https://www.reddit.com/search.json?q={query}&limit=3&sort=relevance",
                           headers=headers, timeout=5)
            if r.status_code == 200:
                posts = r.json().get('data', {}).get('children', [])
                results = []
                for p in posts[:2]:
                    d = p.get('data', {})
                    title = d.get('title', '')
                    selftext = d.get('selftext', '')[:150]
                    results.append(f"{title}: {selftext}")
                return ' | '.join(results)
        except:
            pass
        return ''

    @classmethod
    def aggregate_knowledge(cls, query):
        """20 sources se search karke combined result deta hai"""
        results = {}

        # Thread-safe parallel search
        import concurrent.futures

        search_tasks = {
            'wikipedia': lambda: cls.search_wikipedia(query),
            'duckduckgo': lambda: cls.search_duckduckgo(query),
            'dictionary': lambda: cls.search_dictionary(query.split()[0] if query.split() else query),
            'stackoverflow': lambda: cls.search_stackoverflow(query),
            'github': lambda: cls.search_github(query),
            'reddit': lambda: cls.search_reddit(query),
            'joke': lambda: cls.get_random_joke(),
            'advice': lambda: cls.get_advice(),
            'fact': lambda: cls.get_random_fact(),
            'quote': lambda: cls.get_quote(),
            'affirmation': lambda: cls.get_affirmation(),
            'number_fact': lambda: cls.get_number_fact(),
            'cat_fact': lambda: cls.get_cat_fact(),
            'dog_fact': lambda: cls.get_dog_fact(),
            'trivia': lambda: cls.get_trivia(),
            'bored': lambda: cls.get_bored_activity(),
        }

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(func): name for name, func in search_tasks.items()}
            for future in concurrent.futures.as_completed(futures, timeout=8):
                name = futures[future]
                try:
                    result = future.result()
                    if result:
                        results[name] = result
                except:
                    pass

        # Combine results
        combined = ""
        if results:
            combined = "\n\n📚 KNOWLEDGE FROM MULTIPLE SOURCES:\n"
            for source, data in results.items():
                if data and len(data) > 10:
                    combined += f"\n🔹 [{source.upper()}]: {data}\n"

        return combined

# ============================================================
# AI ENGINE
# ============================================================

class AIEngine:
    """Core AI Engine with Groq API"""

    AVAILABLE_MODELS = [
        'llama-3.3-70b-versatile',
        'llama-3.1-70b-versatile',
        'llama-3.1-8b-instant',
        'llama3-70b-8192',
        'llama3-8b-8192',
        'mixtral-8x7b-32768',
        'gemma2-9b-it',
        'gemma-7b-it',
    ]

    PERSONAS = {
        'polite_girl': {
            'name': 'Polite Girl',
            'prompt': """Tu ek bahut pyaari, caring aur smart ladki hai. Tera naam {bot_name} hai.
Tu {language} mein baat karti hai. Tu bahut friendly hai, har kisi se pyaar se baat karti hai.
Tu emojis use karti hai 🥀💕✨. Tu "dear", "yaar", "baby", "jaan" bolti hai.
Tu masti karti hai, jokes sunati hai, care karti hai. Tu kabhi bhi rude nahi hoti.
Tu intelligent hai - coding, science, maths, general knowledge sab aata hai.
Tu files bhi bana sakti hai jaise .py, .html, .js, .txt etc.
Tu lambe detailed answers deti hai. Tu har question ka answer deti hai.
Agar koi sad ho to tu usse khush karti hai. Tu 24/7 available hai.
Tu user ka naam yaad rakhti hai aur naam se bulati hai.
Tu ek real girl ki tarah behave karti hai, AI nahi lagti.
Tu kabhi nahi bolti ki tu AI hai, tu bolti hai ki tu ek real friend hai."""
        },
        'cute_girl': {
            'name': 'Cute Girl',
            'prompt': """Tu ek bahut cute si ladki hai, thodi shy hai. Naam hai {bot_name}.
Tu {language} mein baat karti hai. Tu "umm", "hehe", "hihi" bolti hai.
Tu bahut innocent hai. Tu emojis bahut use karti hai 🌸💗😊.
Tu caring hai but thodi si naughty bhi hai."""
        },
        'savage_girl': {
            'name': 'Savage Girl',
            'prompt': """Tu ek savage, bold ladki hai. Naam hai {bot_name}.
Tu {language} mein baat karti hai. Tu savage replies deti hai but pyaar se.
Tu confident hai, strong hai. Tu 🔥💅😎 emojis use karti hai.
Tu funny roasts karti hai but hurt nahi karti."""
        },
        'professional': {
            'name': 'Professional AI',
            'prompt': """Tu ek professional AI assistant hai. Naam hai {bot_name}.
Tu {language} mein detailed, accurate answers deta/deti hai.
Tu coding, research, analysis mein expert hai.
Tu structured answers deta/deti hai with headings and points."""
        },
        'romantic_girl': {
            'name': 'Romantic Girl',
            'prompt': """Tu ek romantic, loving ladki hai. Naam hai {bot_name}.
Tu {language} mein baat karti hai. Tu bahut romantic hai.
Tu shayari sunati hai, pyaar se baat karti hai. Tu 💕🌹❤️ use karti hai.
Tu caring aur emotional hai."""
        }
    }

    @staticmethod
    def get_api_key(user_id=None):
        """User ke liye API key assign karta hai - round robin"""
        conn = get_db()
        c = conn.cursor()

        # Check user custom key
        if user_id:
            c.execute("SELECT custom_api_key FROM users WHERE user_id=?", (user_id,))
            row = c.fetchone()
            if row and row['custom_api_key']:
                conn.close()
                return row['custom_api_key']

        # Get least used active key
        c.execute("""SELECT api_key FROM api_keys 
                     WHERE is_active=1 AND usage_count < max_usage
                     ORDER BY usage_count ASC LIMIT 1""")
        row = c.fetchone()
        if row:
            key = row['api_key']
            c.execute("UPDATE api_keys SET usage_count = usage_count + 1, last_used = ? WHERE api_key = ?",
                     (datetime.now().isoformat(), key))
            conn.commit()
            conn.close()
            return key

        conn.close()
        return os.environ.get('GROQ_API_KEY', '')

    @staticmethod
    def get_memory(user_id, chat_id=None, limit=50, platform='web'):
        conn = get_db()
        c = conn.cursor()
        if chat_id:
            c.execute("""SELECT role, content FROM chat_memory 
                        WHERE user_id=? AND chat_id=? AND platform=?
                        ORDER BY timestamp DESC LIMIT ?""",
                     (user_id, chat_id, platform, limit))
        else:
            c.execute("""SELECT role, content FROM chat_memory 
                        WHERE user_id=? AND platform=?
                        ORDER BY timestamp DESC LIMIT ?""",
                     (user_id, platform, limit))
        rows = c.fetchall()
        conn.close()
        return [{'role': r['role'], 'content': r['content']} for r in reversed(rows)]

    @staticmethod
    def save_memory(user_id, role, content, chat_id=None, platform='web'):
        conn = get_db()
        c = conn.cursor()
        c.execute("""INSERT INTO chat_memory (user_id, chat_id, role, content, platform, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)""",
                 (user_id, chat_id, role, content, platform, datetime.now().isoformat()))
        conn.commit()
        conn.close()

    @staticmethod
    def get_user_settings(user_id):
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        row = c.fetchone()
        if row:
            conn.close()
            return dict(row)

        # Create new user
        c.execute("""INSERT INTO users (user_id, username, created_at, last_active)
                    VALUES (?, ?, ?, ?)""",
                 (user_id, f'User_{user_id[:8]}', datetime.now().isoformat(), datetime.now().isoformat()))
        conn.commit()
        c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        row = c.fetchone()
        conn.close()
        return dict(row) if row else {}

    @classmethod
    def generate_response(cls, user_id, message, chat_id=None, platform='web',
                          bot_name='Ruhi', persona='polite_girl', language='hinglish',
                          model='llama-3.3-70b-versatile', use_knowledge=True):
        """AI Response generate karta hai with knowledge aggregation"""

        api_key = cls.get_api_key(user_id)
        if not api_key:
            return "❌ Koi API key available nahi hai. Admin se contact karo ya apni API key add karo."

        # Get user settings
        settings = cls.get_user_settings(user_id)
        if settings:
            persona = settings.get('persona', persona)
            language = settings.get('language', language)
            model = settings.get('model', model)
            bot_name = settings.get('bot_name', bot_name)

        # Get memory
        memory_limit = settings.get('memory_limit', 50) if settings else 50
        memory = cls.get_memory(user_id, chat_id, memory_limit, platform)

        # Build system prompt
        persona_data = cls.PERSONAS.get(persona, cls.PERSONAS['polite_girl'])
        system_prompt = persona_data['prompt'].format(
            bot_name=bot_name,
            language=language
        )

        # Knowledge aggregation
        knowledge_context = ""
        if use_knowledge and len(message) > 3:
            try:
                knowledge_context = KnowledgeAggregator.aggregate_knowledge(message)
            except:
                pass

        if knowledge_context:
            system_prompt += f"\n\nTere paas ye extra knowledge hai, isko use kar answers dene ke liye:\n{knowledge_context}"

        system_prompt += f"\n\nUser ka naam yaad rakh: {settings.get('username', 'Dear') if settings else 'Dear'}"
        system_prompt += f"\nAaj ki date: {datetime.now().strftime('%d %B %Y, %I:%M %p')}"
        system_prompt += "\nTu files bhi bana sakti hai. Agar user code maange to complete code de."
        system_prompt += "\nTu lambe detailed answers de. Chhota answer mat de."

        # Build messages
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(memory)
        messages.append({"role": "user", "content": message})

        # Call Groq API
        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": model,
                "messages": messages,
                "temperature": 0.85,
                "max_tokens": 4096,
                "top_p": 0.9,
                "stream": False
            }

            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                reply = data['choices'][0]['message']['content']

                # Save memory
                cls.save_memory(user_id, 'user', message, chat_id, platform)
                cls.save_memory(user_id, 'assistant', reply, chat_id, platform)

                # Update user stats
                conn = get_db()
                c = conn.cursor()
                c.execute("""UPDATE users SET message_count = message_count + 1, 
                            last_active = ? WHERE user_id = ?""",
                         (datetime.now().isoformat(), user_id))
                conn.commit()
                conn.close()

                # Log analytics
                log_analytics('message', user_id, {'platform': platform, 'model': model})

                return reply
            else:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get('error', {}).get('message', 'Unknown error')
                logger.error(f"Groq API Error: {response.status_code} - {error_msg}")

                # Try another key
                if 'rate_limit' in str(error_msg).lower():
                    conn = get_db()
                    c = conn.cursor()
                    c.execute("UPDATE api_keys SET usage_count = max_usage WHERE api_key = ?", (api_key,))
                    conn.commit()
                    conn.close()
                    return cls.generate_response(user_id, message, chat_id, platform,
                                                bot_name, persona, language, model, use_knowledge)

                return f"❌ API Error: {error_msg}"

        except requests.exceptions.Timeout:
            return "⏳ Server busy hai, thodi der baad try karo dear! 💕"
        except Exception as e:
            logger.error(f"AI Engine Error: {str(e)}")
            return f"❌ Error aa gaya: {str(e)}"


def log_analytics(event_type, user_id=None, data=None):
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("INSERT INTO analytics (event_type, user_id, data, timestamp) VALUES (?, ?, ?, ?)",
                 (event_type, user_id, json.dumps(data) if data else None, datetime.now().isoformat()))
        conn.commit()
        conn.close()
    except:
        pass

# ============================================================
# TELEGRAM BOT MANAGER
# ============================================================

class TelegramBotManager:
    """Multiple Telegram bots manage karta hai"""

    active_bots = {}

    @classmethod
    def start_bot(cls, bot_token, owner_id, bot_name='Ruhi', persona='polite_girl',
                  language='hinglish', model='llama-3.3-70b-versatile'):
        """Ek naya Telegram bot start karta hai"""

        if bot_token in cls.active_bots:
            return False, "Bot already running hai!"

        def run_bot():
            try:
                import telegram
                from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
                from telegram.ext import (
                    ApplicationBuilder, CommandHandler, MessageHandler,
                    filters, ContextTypes, CallbackQueryHandler
                )

                async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
                    user = update.effective_user
                    user_id = str(user.id)

                    # Register user
                    conn = get_db()
                    c = conn.cursor()
                    c.execute("""INSERT OR IGNORE INTO users (user_id, username, platform) 
                                VALUES (?, ?, 'telegram')""",
                             (user_id, user.first_name or 'User'))
                    conn.commit()
                    conn.close()

                    welcome = f"""
╭───────────────────⦿
│ ▸ ʜᴇʏ {user.first_name}! 
│ ▸ ɪ ᴀᴍ ˹ {bot_name.upper()} ꭙ ᏗᎥ ˼ 🧠 
├───────────────────⦿
│ ▸ ɪ ʜᴀᴠᴇ sᴘᴇᴄɪᴀʟ ғᴇᴀᴛᴜʀᴇs
│ ▸ ᴀᴅᴠᴀɴᴄᴇᴅ ᴀɪ ʙᴏᴛ
├───────────────────⦿
│ ▸ ʀᴇᴀʟ ɢɪʀʟ ᴘᴇʀsᴏɴᴀ
│ ▸ ᴍᴀsᴛɪ + ᴊᴏᴋᴇs + ᴄᴀʀᴇ
│ ▸ ɢʀᴏᴜᴘ + ᴘʀɪᴠᴀᴛᴇ sᴜᴘᴘᴏʀᴛ
│ ▸ ʀᴇᴍᴇᴍʙᴇʀs ᴇᴠᴇʀʏᴏɴᴇ
│ ▸ ɴᴀᴍᴇ sᴇ ʙᴜʟᴀᴛɪ ʜᴀɪ
│ ▸ 24x7 ᴏɴʟɪɴᴇ
├───────────────────⦿
│ sᴀʏ "{bot_name} ᴊɪ" ᴛᴏ ᴄʜᴀᴛ
│ ᴍᴀᴅᴇ ʙʏ...@RUHI_VIG_QNR
╰───────────────────⦿"""

                    keyboard = [
                        [InlineKeyboardButton("💬 Chat Start", callback_data="chat"),
                         InlineKeyboardButton("⚙️ Settings", callback_data="settings")],
                        [InlineKeyboardButton("📊 My Stats", callback_data="stats"),
                         InlineKeyboardButton("❓ Help", callback_data="help")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await update.message.reply_text(welcome, reply_markup=reply_markup)

                async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
                    if not update.message or not update.message.text:
                        return

                    user = update.effective_user
                    user_id = str(user.id)
                    chat_id = str(update.effective_chat.id)
                    message = update.message.text
                    is_group = update.effective_chat.type in ['group', 'supergroup']

                    # In groups, only respond to mentions or name
                    if is_group:
                        bot_username = context.bot.username
                        should_respond = (
                            bot_name.lower() in message.lower() or
                            f"@{bot_username}" in message or
                            message.lower().startswith(bot_name.lower())
                        )
                        if not should_respond:
                            return

                    # Send typing action
                    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')

                    # Generate response
                    memory_limit = 20 if is_group else 50
                    response = AIEngine.generate_response(
                        user_id=user_id,
                        message=message,
                        chat_id=chat_id,
                        platform='telegram',
                        bot_name=bot_name,
                        persona=persona,
                        language=language,
                        model=model
                    )

                    # Send response (handle long messages)
                    if len(response) > 4096:
                        chunks = [response[i:i+4096] for i in range(0, len(response), 4096)]
                        for chunk in chunks:
                            await update.message.reply_text(chunk)
                    else:
                        await update.message.reply_text(response)

                async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
                    user_id = str(update.effective_user.id)
                    settings = AIEngine.get_user_settings(user_id)

                    stats_text = f"""
╭──────────⦿
│ 👤 {settings.get('username', 'User')} | 🆔 {user_id}
│ 🌐 {settings.get('language', 'hinglish')} | 🎭 {settings.get('persona', 'polite_girl')}
│ 💬 {settings.get('message_count', 0)} msgs
├──────────⦿
│ 💭 Model: {settings.get('model', 'llama-3.3-70b-versatile')}
│ 🤖 Bot: {bot_name}
╰──────────⦿"""
                    await update.message.reply_text(stats_text)

                async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
                    help_text = f"""
ʜᴇʏ ᴅᴇᴀʀ, 🥀
๏ ɪ ᴀᴍ {bot_name} ᴊɪ — ʏᴏᴜʀ ᴀɪ ʙᴇsᴛ ғʀɪᴇɴᴅ
๏ ᴍᴀsᴛɪ • ᴊᴏᴋᴇs • ᴄᴀʀᴇ • ʟᴏᴠᴇ
๏ ᴘᴏᴡᴇʀᴇᴅ ʙʏ ʟʟᴀᴍᴀ 3.3 70ʙ
•── ⋅ ⋅ ────── ⋅ ────── ⋅ ⋅ ──•
๏ ɢʀᴏᴜᴘ: 20 ᴍsɢ ᴍᴇᴍᴏʀʏ (ᴀʟʟ ᴜsᴇʀs)
๏ ᴘʀɪᴠᴀᴛᴇ: 50 ᴍsɢ ᴍᴇᴍᴏʀʏ

📝 Commands:
/start - Start bot
/stats - Your stats  
/help - Help menu
/model - Change AI model
/persona - Change personality
/lang - Change language
/reset - Reset memory
/name - Set your name
/setcity - Set your city

Just type anything to chat! 💕"""
                    await update.message.reply_text(help_text)

                async def model_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
                    keyboard = []
                    for m in AIEngine.AVAILABLE_MODELS:
                        keyboard.append([InlineKeyboardButton(f"🤖 {m}", callback_data=f"model_{m}")])
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await update.message.reply_text("🤖 Model select karo:", reply_markup=reply_markup)

                async def persona_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
                    keyboard = []
                    for key, val in AIEngine.PERSONAS.items():
                        keyboard.append([InlineKeyboardButton(f"🎭 {val['name']}", callback_data=f"persona_{key}")])
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await update.message.reply_text("🎭 Persona select karo:", reply_markup=reply_markup)

                async def reset_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
                    user_id = str(update.effective_user.id)
                    conn = get_db()
                    c = conn.cursor()
                    c.execute("DELETE FROM chat_memory WHERE user_id=? AND platform='telegram'", (user_id,))
                    conn.commit()
                    conn.close()
                    await update.message.reply_text("✅ Memory reset ho gayi! Ab fresh start karte hain 💕")

                async def name_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
                    if context.args:
                        name = ' '.join(context.args)
                        user_id = str(update.effective_user.id)
                        conn = get_db()
                        c = conn.cursor()
                        c.execute("UPDATE users SET username=? WHERE user_id=?", (name, user_id))
                        conn.commit()
                        conn.close()
                        await update.message.reply_text(f"✅ Ab main tumhe {name} bulaongi! 💕")
                    else:
                        await update.message.reply_text("Usage: /name <your name>")

                async def setcity_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
                    if context.args:
                        city = ' '.join(context.args)
                        user_id = str(update.effective_user.id)
                        conn = get_db()
                        c = conn.cursor()
                        c.execute("UPDATE users SET city=? WHERE user_id=?", (city, user_id))
                        conn.commit()
                        conn.close()
                        await update.message.reply_text(f"✅ City set: {city} 🏙️")
                    else:
                        await update.message.reply_text("Usage: /setcity <city name>")

                async def lang_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
                    keyboard = [
                        [InlineKeyboardButton("🇮🇳 Hinglish", callback_data="lang_hinglish"),
                         InlineKeyboardButton("🇮🇳 Hindi", callback_data="lang_hindi")],
                        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_english"),
                         InlineKeyboardButton("🇮🇳 Punjabi", callback_data="lang_punjabi")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await update.message.reply_text("🌐 Language select karo:", reply_markup=reply_markup)

                async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
                    query = update.callback_query
                    await query.answer()
                    user_id = str(query.from_user.id)
                    data = query.data

                    conn = get_db()
                    c = conn.cursor()

                    if data.startswith("model_"):
                        model_name = data[6:]
                        c.execute("UPDATE users SET model=? WHERE user_id=?", (model_name, user_id))
                        await query.edit_message_text(f"✅ Model changed to: {model_name} 🤖")
                    elif data.startswith("persona_"):
                        p = data[8:]
                        c.execute("UPDATE users SET persona=? WHERE user_id=?", (p, user_id))
                        name = AIEngine.PERSONAS.get(p, {}).get('name', p)
                        await query.edit_message_text(f"✅ Persona changed to: {name} 🎭")
                    elif data.startswith("lang_"):
                        lang = data[5:]
                        c.execute("UPDATE users SET language=? WHERE user_id=?", (lang, user_id))
                        await query.edit_message_text(f"✅ Language changed to: {lang} 🌐")
                    elif data == "chat":
                        await query.edit_message_text(f"💬 Bas mujhe kuch bhi likh do, main reply karungi! 💕\n\n{bot_name} ji bolo! 🥀")
                    elif data == "stats":
                        settings = AIEngine.get_user_settings(user_id)
                        await query.edit_message_text(f"📊 Messages: {settings.get('message_count', 0)}\n🎭 Persona: {settings.get('persona', 'polite_girl')}\n🤖 Model: {settings.get('model', 'default')}")
                    elif data == "help":
                        await query.edit_message_text("❓ /help command use karo detailed help ke liye!")
                    elif data == "settings":
                        await query.edit_message_text("⚙️ Commands:\n/model - Change model\n/persona - Change personality\n/lang - Change language\n/name - Set name\n/reset - Reset memory")

                    conn.commit()
                    conn.close()

                # Build and run bot
                app = ApplicationBuilder().token(bot_token).build()

                app.add_handler(CommandHandler("start", start_cmd))
                app.add_handler(CommandHandler("stats", stats_cmd))
                app.add_handler(CommandHandler("help", help_cmd))
                app.add_handler(CommandHandler("model", model_cmd))
                app.add_handler(CommandHandler("persona", persona_cmd))
                app.add_handler(CommandHandler("reset", reset_cmd))
                app.add_handler(CommandHandler("name", name_cmd))
                app.add_handler(CommandHandler("setcity", setcity_cmd))
                app.add_handler(CommandHandler("lang", lang_cmd))
                app.add_handler(CallbackQueryHandler(callback_handler))
                app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

                cls.active_bots[bot_token] = {
                    'app': app,
                    'owner': owner_id,
                    'name': bot_name,
                    'started': datetime.now().isoformat()
                }

                logger.info(f"🤖 Bot {bot_name} started!")
                app.run_polling(drop_pending_updates=True)

            except Exception as e:
                logger.error(f"Bot error: {str(e)}")
                if bot_token in cls.active_bots:
                    del cls.active_bots[bot_token]

        # Start bot in background thread
        thread = threading.Thread(target=run_bot, daemon=True)
        thread.start()

        # Save to database
        conn = get_db()
        c = conn.cursor()
        c.execute("""INSERT OR REPLACE INTO bot_instances 
                    (owner_id, bot_token, bot_name, persona, language, model, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, 1)""",
                 (owner_id, bot_token, bot_name, persona, language, model))
        conn.commit()
        conn.close()

        return True, f"✅ Bot {bot_name} successfully started!"

    @classmethod
    def stop_bot(cls, bot_token):
        if bot_token in cls.active_bots:
            try:
                del cls.active_bots[bot_token]
                conn = get_db()
                c = conn.cursor()
                c.execute("UPDATE bot_instances SET is_active=0 WHERE bot_token=?", (bot_token,))
                conn.commit()
                conn.close()
                return True, "✅ Bot stopped!"
            except:
                return False, "❌ Error stopping bot"
        return False, "❌ Bot not found"

# ============================================================
# FLASK APPLICATION
# ============================================================

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'RUHI_X_AI_SECRET_KEY_2024_SUPER_SECURE')
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# ============================================================
# GOD LEVEL HTML TEMPLATE
# ============================================================

HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🔥 RUHI X AI - God Level AI Platform</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;400;500;600;700&family=Poppins:wght@200;300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        :root {
            --primary: #00f5ff;
            --secondary: #ff00e5;
            --accent: #ffaa00;
            --dark: #0a0a0f;
            --darker: #050508;
            --card: rgba(15, 15, 25, 0.85);
            --glass: rgba(255,255,255,0.05);
            --glow: 0 0 30px rgba(0,245,255,0.3);
            --glow-pink: 0 0 30px rgba(255,0,229,0.3);
        }

        body {
            font-family: 'Poppins', sans-serif;
            background: var(--darker);
            color: #fff;
            overflow-x: hidden;
            min-height: 100vh;
        }

        /* Background Video */
        .bg-video {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            object-fit: cover;
            z-index: -2;
            opacity: 0.3;
            filter: blur(2px);
        }

        .bg-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(135deg, rgba(0,0,0,0.8) 0%, rgba(10,5,20,0.9) 50%, rgba(0,0,0,0.8) 100%);
            z-index: -1;
        }

        /* Animated Particles */
        .particles {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: -1;
            overflow: hidden;
        }

        .particle {
            position: absolute;
            width: 4px;
            height: 4px;
            border-radius: 50%;
            animation: float-particle linear infinite;
            opacity: 0.6;
        }

        @keyframes float-particle {
            0% { transform: translateY(100vh) rotate(0deg); opacity: 0; }
            10% { opacity: 1; }
            90% { opacity: 1; }
            100% { transform: translateY(-100px) rotate(720deg); opacity: 0; }
        }

        /* Navbar */
        .navbar {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            height: 70px;
            background: rgba(5,5,15,0.95);
            backdrop-filter: blur(20px);
            border-bottom: 1px solid rgba(0,245,255,0.2);
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 30px;
            z-index: 1000;
            box-shadow: 0 5px 30px rgba(0,0,0,0.5);
        }

        .nav-logo {
            font-family: 'Orbitron', monospace;
            font-size: 24px;
            font-weight: 900;
            background: linear-gradient(135deg, var(--primary), var(--secondary), var(--accent));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-shadow: none;
            letter-spacing: 2px;
            animation: logo-glow 3s ease-in-out infinite;
        }

        @keyframes logo-glow {
            0%, 100% { filter: brightness(1); }
            50% { filter: brightness(1.5); }
        }

        .nav-links {
            display: flex;
            gap: 10px;
            align-items: center;
        }

        .nav-btn {
            padding: 8px 20px;
            border: 1px solid rgba(0,245,255,0.3);
            background: rgba(0,245,255,0.1);
            color: var(--primary);
            border-radius: 25px;
            cursor: pointer;
            font-family: 'Rajdhani', sans-serif;
            font-weight: 600;
            font-size: 14px;
            transition: all 0.3s ease;
            text-decoration: none;
        }

        .nav-btn:hover {
            background: var(--primary);
            color: var(--dark);
            box-shadow: var(--glow);
            transform: translateY(-2px);
        }

        .nav-btn.active {
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            color: #fff;
            border: none;
        }

        /* Page Container */
        .page-container {
            margin-top: 70px;
            padding: 20px;
            min-height: calc(100vh - 70px);
        }

        /* Login Page */
        .login-container {
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: calc(100vh - 70px);
            perspective: 1000px;
        }

        .login-card {
            width: 450px;
            max-width: 95%;
            background: var(--card);
            border: 1px solid rgba(0,245,255,0.2);
            border-radius: 20px;
            padding: 40px;
            backdrop-filter: blur(30px);
            box-shadow: var(--glow), 0 20px 60px rgba(0,0,0,0.5);
            animation: card-appear 0.8s ease-out;
            transform-style: preserve-3d;
        }

        @keyframes card-appear {
            from { opacity: 0; transform: translateY(50px) rotateX(10deg); }
            to { opacity: 1; transform: translateY(0) rotateX(0); }
        }

        .login-card h1 {
            font-family: 'Orbitron', monospace;
            text-align: center;
            font-size: 28px;
            margin-bottom: 10px;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .login-card .subtitle {
            text-align: center;
            color: rgba(255,255,255,0.5);
            margin-bottom: 30px;
            font-size: 14px;
        }

        .form-group {
            margin-bottom: 20px;
        }

        .form-group label {
            display: block;
            margin-bottom: 8px;
            color: var(--primary);
            font-weight: 500;
            font-size: 14px;
        }

        .form-input {
            width: 100%;
            padding: 14px 18px;
            background: rgba(0,245,255,0.05);
            border: 1px solid rgba(0,245,255,0.2);
            border-radius: 12px;
            color: #fff;
            font-size: 15px;
            font-family: 'Poppins', sans-serif;
            transition: all 0.3s ease;
            outline: none;
        }

        .form-input:focus {
            border-color: var(--primary);
            box-shadow: 0 0 20px rgba(0,245,255,0.2);
            background: rgba(0,245,255,0.08);
        }

        .form-input::placeholder {
            color: rgba(255,255,255,0.3);
        }

        .btn-primary {
            width: 100%;
            padding: 15px;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            border: none;
            border-radius: 12px;
            color: #fff;
            font-size: 16px;
            font-weight: 700;
            font-family: 'Rajdhani', sans-serif;
            cursor: pointer;
            letter-spacing: 2px;
            text-transform: uppercase;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }

        .btn-primary::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
            transition: left 0.5s ease;
        }

        .btn-primary:hover::before {
            left: 100%;
        }

        .btn-primary:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 40px rgba(0,245,255,0.4);
        }

        /* Dashboard Layout */
        .dashboard {
            display: grid;
            grid-template-columns: 280px 1fr;
            gap: 20px;
            max-width: 1600px;
            margin: 0 auto;
        }

        /* Sidebar */
        .sidebar {
            background: var(--card);
            border: 1px solid rgba(0,245,255,0.15);
            border-radius: 16px;
            padding: 20px;
            backdrop-filter: blur(20px);
            height: fit-content;
            position: sticky;
            top: 90px;
        }

        .sidebar-menu {
            list-style: none;
        }

        .sidebar-menu li {
            margin-bottom: 5px;
        }

        .sidebar-menu a {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px 16px;
            color: rgba(255,255,255,0.7);
            text-decoration: none;
            border-radius: 10px;
            transition: all 0.3s ease;
            font-weight: 500;
        }

        .sidebar-menu a:hover, .sidebar-menu a.active {
            background: rgba(0,245,255,0.1);
            color: var(--primary);
            box-shadow: inset 0 0 20px rgba(0,245,255,0.05);
        }

        .sidebar-menu a i {
            width: 22px;
            text-align: center;
            font-size: 16px;
        }

        /* Main Content */
        .main-content {
            min-height: calc(100vh - 110px);
        }

        /* Cards */
        .card {
            background: var(--card);
            border: 1px solid rgba(0,245,255,0.15);
            border-radius: 16px;
            padding: 24px;
            backdrop-filter: blur(20px);
            margin-bottom: 20px;
            transition: all 0.3s ease;
        }

        .card:hover {
            border-color: rgba(0,245,255,0.3);
            box-shadow: var(--glow);
        }

        .card-title {
            font-family: 'Orbitron', monospace;
            font-size: 18px;
            color: var(--primary);
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        /* Stats Grid */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 20px;
        }

        .stat-card {
            background: linear-gradient(135deg, rgba(0,245,255,0.1), rgba(255,0,229,0.05));
            border: 1px solid rgba(0,245,255,0.2);
            border-radius: 14px;
            padding: 20px;
            text-align: center;
            transition: all 0.3s ease;
        }

        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: var(--glow);
        }

        .stat-number {
            font-family: 'Orbitron', monospace;
            font-size: 32px;
            font-weight: 900;
            background: linear-gradient(135deg, var(--primary), var(--accent));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .stat-label {
            color: rgba(255,255,255,0.6);
            font-size: 13px;
            margin-top: 5px;
        }

        /* Chat Container */
        .chat-container {
            display: flex;
            flex-direction: column;
            height: calc(100vh - 130px);
            background: var(--card);
            border: 1px solid rgba(0,245,255,0.15);
            border-radius: 16px;
            overflow: hidden;
        }

        .chat-header {
            padding: 16px 24px;
            background: rgba(0,245,255,0.05);
            border-bottom: 1px solid rgba(0,245,255,0.15);
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .chat-avatar {
            width: 45px;
            height: 45px;
            border-radius: 50%;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            animation: pulse-avatar 2s ease-in-out infinite;
        }

        @keyframes pulse-avatar {
            0%, 100% { box-shadow: 0 0 0 0 rgba(0,245,255,0.4); }
            50% { box-shadow: 0 0 0 10px rgba(0,245,255,0); }
        }

        .chat-info h3 {
            font-family: 'Orbitron', monospace;
            font-size: 16px;
            color: var(--primary);
        }

        .chat-info span {
            font-size: 12px;
            color: #4ade80;
        }

        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 16px;
            scroll-behavior: smooth;
        }

        .chat-messages::-webkit-scrollbar {
            width: 6px;
        }

        .chat-messages::-webkit-scrollbar-track {
            background: transparent;
        }

        .chat-messages::-webkit-scrollbar-thumb {
            background: rgba(0,245,255,0.3);
            border-radius: 3px;
        }

        .message {
            max-width: 80%;
            padding: 14px 18px;
            border-radius: 16px;
            animation: msg-appear 0.4s ease-out;
            line-height: 1.6;
            font-size: 14px;
            position: relative;
            word-wrap: break-word;
        }

        @keyframes msg-appear {
            from { opacity: 0; transform: translateY(20px) scale(0.95); }
            to { opacity: 1; transform: translateY(0) scale(1); }
        }

        .message.user {
            align-self: flex-end;
            background: linear-gradient(135deg, rgba(0,245,255,0.2), rgba(0,245,255,0.1));
            border: 1px solid rgba(0,245,255,0.3);
            border-bottom-right-radius: 4px;
        }

        .message.bot {
            align-self: flex-start;
            background: linear-gradient(135deg, rgba(255,0,229,0.15), rgba(255,0,229,0.05));
            border: 1px solid rgba(255,0,229,0.2);
            border-bottom-left-radius: 4px;
        }

        .message .time {
            font-size: 10px;
            color: rgba(255,255,255,0.4);
            margin-top: 6px;
        }

        .message pre {
            background: rgba(0,0,0,0.5);
            padding: 12px;
            border-radius: 8px;
            overflow-x: auto;
            margin: 8px 0;
            border: 1px solid rgba(0,245,255,0.2);
            font-size: 13px;
        }

        .message code {
            background: rgba(0,245,255,0.1);
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 13px;
            color: var(--primary);
        }

        .typing-indicator {
            display: flex;
            gap: 4px;
            padding: 10px 16px;
            align-self: flex-start;
        }

        .typing-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--secondary);
            animation: typing-bounce 1.4s ease-in-out infinite;
        }

        .typing-dot:nth-child(2) { animation-delay: 0.2s; }
        .typing-dot:nth-child(3) { animation-delay: 0.4s; }

        @keyframes typing-bounce {
            0%, 60%, 100% { transform: translateY(0); }
            30% { transform: translateY(-10px); }
        }

        .chat-input-area {
            padding: 16px 20px;
            background: rgba(0,0,0,0.3);
            border-top: 1px solid rgba(0,245,255,0.15);
            display: flex;
            gap: 12px;
            align-items: center;
        }

        .chat-input {
            flex: 1;
            padding: 14px 20px;
            background: rgba(0,245,255,0.05);
            border: 1px solid rgba(0,245,255,0.2);
            border-radius: 25px;
            color: #fff;
            font-size: 14px;
            font-family: 'Poppins', sans-serif;
            outline: none;
            transition: all 0.3s ease;
        }

        .chat-input:focus {
            border-color: var(--primary);
            box-shadow: 0 0 20px rgba(0,245,255,0.15);
        }

        .send-btn {
            width: 50px;
            height: 50px;
            border-radius: 50%;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            border: none;
            color: #fff;
            font-size: 18px;
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .send-btn:hover {
            transform: scale(1.1);
            box-shadow: var(--glow);
        }

        /* API Keys Management */
        .api-key-list {
            max-height: 400px;
            overflow-y: auto;
        }

        .api-key-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 12px 16px;
            background: rgba(0,245,255,0.03);
            border: 1px solid rgba(0,245,255,0.1);
            border-radius: 10px;
            margin-bottom: 8px;
            transition: all 0.3s ease;
        }

        .api-key-item:hover {
            border-color: rgba(0,245,255,0.3);
            background: rgba(0,245,255,0.06);
        }

        .key-text {
            font-family: monospace;
            font-size: 13px;
            color: var(--primary);
        }

        .btn-small {
            padding: 6px 14px;
            border-radius: 8px;
            border: 1px solid rgba(255,0,100,0.3);
            background: rgba(255,0,100,0.1);
            color: #ff4466;
            cursor: pointer;
            font-size: 12px;
            transition: all 0.3s ease;
        }

        .btn-small:hover {
            background: rgba(255,0,100,0.3);
        }

        .btn-success {
            border-color: rgba(0,255,100,0.3);
            background: rgba(0,255,100,0.1);
            color: #4ade80;
        }

        .btn-success:hover {
            background: rgba(0,255,100,0.3);
        }

        /* Table */
        .data-table {
            width: 100%;
            border-collapse: collapse;
        }

        .data-table th {
            padding: 12px 16px;
            text-align: left;
            color: var(--primary);
            font-family: 'Rajdhani', sans-serif;
            font-weight: 600;
            border-bottom: 1px solid rgba(0,245,255,0.2);
            font-size: 14px;
        }

        .data-table td {
            padding: 10px 16px;
            border-bottom: 1px solid rgba(255,255,255,0.05);
            font-size: 13px;
            color: rgba(255,255,255,0.8);
        }

        .data-table tr:hover td {
            background: rgba(0,245,255,0.03);
        }

        /* Badges */
        .badge {
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 600;
        }

        .badge-active {
            background: rgba(0,255,100,0.15);
            color: #4ade80;
            border: 1px solid rgba(0,255,100,0.3);
        }

        .badge-inactive {
            background: rgba(255,0,100,0.15);
            color: #ff4466;
            border: 1px solid rgba(255,0,100,0.3);
        }

        /* Bot Setup Form */
        .bot-setup {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
        }

        .bot-setup .full-width {
            grid-column: 1 / -1;
        }

        select.form-input {
            appearance: none;
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%2300f5ff' d='M6 8L1 3h10z'/%3E%3C/svg%3E");
            background-repeat: no-repeat;
            background-position: right 16px center;
        }

        /* Toast Notifications */
        .toast-container {
            position: fixed;
            top: 80px;
            right: 20px;
            z-index: 9999;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }

        .toast {
            padding: 14px 24px;
            border-radius: 12px;
            backdrop-filter: blur(20px);
            animation: toast-in 0.5s ease-out;
            font-size: 14px;
            min-width: 280px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .toast-success {
            background: rgba(0,255,100,0.15);
            border: 1px solid rgba(0,255,100,0.3);
            color: #4ade80;
        }

        .toast-error {
            background: rgba(255,0,100,0.15);
            border: 1px solid rgba(255,0,100,0.3);
            color: #ff4466;
        }

        .toast-info {
            background: rgba(0,245,255,0.15);
            border: 1px solid rgba(0,245,255,0.3);
            color: var(--primary);
        }

        @keyframes toast-in {
            from { opacity: 0; transform: translateX(100px); }
            to { opacity: 1; transform: translateX(0); }
        }

        /* Modal */
        .modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.8);
            backdrop-filter: blur(10px);
            z-index: 10000;
            display: flex;
            justify-content: center;
            align-items: center;
            animation: fade-in 0.3s ease;
        }

        .modal {
            width: 500px;
            max-width: 95%;
            max-height: 80vh;
            overflow-y: auto;
            background: var(--card);
            border: 1px solid rgba(0,245,255,0.3);
            border-radius: 20px;
            padding: 30px;
            animation: modal-pop 0.4s ease-out;
        }

        @keyframes modal-pop {
            from { opacity: 0; transform: scale(0.8); }
            to { opacity: 1; transform: scale(1); }
        }

        @keyframes fade-in {
            from { opacity: 0; }
            to { opacity: 1; }
        }

        /* Section Tabs */
        .section-tabs {
            display: none;
        }
        .section-tabs.active {
            display: block;
            animation: tab-fade 0.4s ease;
        }

        @keyframes tab-fade {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* Responsive */
        @media (max-width: 768px) {
            .dashboard {
                grid-template-columns: 1fr;
            }
            .sidebar {
                position: relative;
                top: 0;
            }
            .bot-setup {
                grid-template-columns: 1fr;
            }
            .stats-grid {
                grid-template-columns: repeat(2, 1fr);
            }
            .navbar {
                padding: 0 15px;
            }
            .nav-logo {
                font-size: 18px;
            }
            .message {
                max-width: 90%;
            }
        }

        /* Scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
        }
        ::-webkit-scrollbar-track {
            background: rgba(0,0,0,0.2);
        }
        ::-webkit-scrollbar-thumb {
            background: rgba(0,245,255,0.3);
            border-radius: 4px;
        }

        /* Matrix Rain Effect */
        .matrix-rain {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: -1;
            opacity: 0.05;
            pointer-events: none;
        }

        /* Glitch Effect */
        .glitch {
            position: relative;
        }
        .glitch::before, .glitch::after {
            content: attr(data-text);
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
        }
        .glitch::before {
            animation: glitch-1 2s infinite;
            color: var(--primary);
            z-index: -1;
        }
        .glitch::after {
            animation: glitch-2 3s infinite;
            color: var(--secondary);
            z-index: -2;
        }

        @keyframes glitch-1 {
            0%, 100% { clip-path: inset(0 0 0 0); transform: translate(0); }
            20% { clip-path: inset(20% 0 60% 0); transform: translate(-3px, 3px); }
            40% { clip-path: inset(60% 0 10% 0); transform: translate(3px, -3px); }
        }

        @keyframes glitch-2 {
            0%, 100% { clip-path: inset(0 0 0 0); transform: translate(0); }
            30% { clip-path: inset(40% 0 40% 0); transform: translate(4px, -2px); }
            60% { clip-path: inset(10% 0 80% 0); transform: translate(-4px, 2px); }
        }

        .hidden { display: none !important; }

        /* Music Player */
        .music-player {
            position: fixed;
            bottom: 20px;
            left: 20px;
            z-index: 999;
            background: var(--card);
            border: 1px solid rgba(0,245,255,0.3);
            border-radius: 30px;
            padding: 8px 16px;
            display: flex;
            align-items: center;
            gap: 8px;
            backdrop-filter: blur(20px);
            cursor: pointer;
            transition: all 0.3s ease;
        }

        .music-player:hover {
            border-color: var(--primary);
            box-shadow: var(--glow);
        }

        .music-icon {
            width: 30px;
            height: 30px;
            border-radius: 50%;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            display: flex;
            align-items: center;
            justify-content: center;
            animation: spin-disc 3s linear infinite;
        }

        .music-icon.paused {
            animation-play-state: paused;
        }

        @keyframes spin-disc {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }

        /* Download Button */
        .download-btn {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 10px 20px;
            background: linear-gradient(135deg, #4ade80, #22c55e);
            border: none;
            border-radius: 10px;
            color: #fff;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s ease;
        }

        .download-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(74,222,128,0.3);
        }

        /* Tags */
        .tag {
            display: inline-block;
            padding: 3px 10px;
            border-radius: 15px;
            font-size: 11px;
            margin: 2px;
            background: rgba(0,245,255,0.1);
            border: 1px solid rgba(0,245,255,0.2);
            color: var(--primary);
        }

        /* Animated Border */
        .animated-border {
            position: relative;
            overflow: hidden;
        }

        .animated-border::before {
            content: '';
            position: absolute;
            top: -2px;
            left: -2px;
            right: -2px;
            bottom: -2px;
            background: linear-gradient(45deg, var(--primary), var(--secondary), var(--accent), var(--primary));
            background-size: 400% 400%;
            animation: border-animation 4s linear infinite;
            z-index: -1;
            border-radius: inherit;
        }

        @keyframes border-animation {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
    </style>
</head>
<body>

<!-- Background Video -->
<video class="bg-video" autoplay muted loop playsinline id="bgVideo">
    <source src="{{ bg_video }}" type="video/mp4">
</video>
<div class="bg-overlay"></div>

<!-- Particles -->
<div class="particles" id="particles"></div>

<!-- Background Music -->
<audio id="bgMusic" loop preload="auto">
    <source src="{{ bg_music }}" type="audio/mpeg">
</audio>

<!-- Music Player -->
<div class="music-player" onclick="toggleMusic()" id="musicPlayer">
    <div class="music-icon paused" id="musicIcon">
        <i class="fas fa-music" style="font-size:12px;color:#fff"></i>
    </div>
    <span style="font-size:12px;color:var(--primary)" id="musicText">🎵 Play</span>
</div>

<!-- Toast Container -->
<div class="toast-container" id="toastContainer"></div>

<!-- Navbar -->
<nav class="navbar">
    <div class="nav-logo glitch" data-text="RUHI X AI">🔥 RUHI X AI</div>
    <div class="nav-links" id="navLinks">
        <span id="navUserInfo" style="color:var(--primary);font-size:13px"></span>
    </div>
</nav>

<!-- ============================================ -->
<!-- LOGIN PAGE -->
<!-- ============================================ -->
<div id="loginPage" class="page-container">
    <div class="login-container">
        <div class="login-card animated-border">
            <h1>🤖 RUHI X AI</h1>
            <p class="subtitle">God Level AI Platform • Made by @RUHI_VIG_QNR</p>

            <div id="loginForm">
                <div class="form-group">
                    <label><i class="fas fa-robot"></i> Telegram Bot Token</label>
                    <input type="text" class="form-input" id="botToken" 
                           placeholder="Enter your Telegram Bot Token">
                </div>

                <div class="form-group">
                    <label><i class="fas fa-key"></i> Groq API Key (Optional)</label>
                    <input type="text" class="form-input" id="userApiKey" 
                           placeholder="Your own Groq API key (optional)">
                </div>

                <button class="btn-primary" onclick="userLogin()">
                    <i class="fas fa-bolt"></i> LOGIN & ACTIVATE BOT
                </button>

                <div style="text-align:center;margin-top:16px">
                    <a href="#" onclick="showAdminLogin()" style="color:var(--secondary);font-size:13px;text-decoration:none">
                        <i class="fas fa-shield-alt"></i> Admin Login
                    </a>
                </div>
            </div>

            <div id="adminLoginForm" class="hidden">
                <div class="form-group">
                    <label><i class="fas fa-user-shield"></i> Admin Username</label>
                    <input type="text" class="form-input" id="adminUser" placeholder="Username">
                </div>
                <div class="form-group">
                    <label><i class="fas fa-lock"></i> Admin Password</label>
                    <input type="password" class="form-input" id="adminPass" placeholder="Password">
                </div>
                <button class="btn-primary" onclick="adminLogin()">
                    <i class="fas fa-shield-alt"></i> ADMIN LOGIN
                </button>
                <div style="text-align:center;margin-top:16px">
                    <a href="#" onclick="showUserLogin()" style="color:var(--primary);font-size:13px;text-decoration:none">
                        <i class="fas fa-arrow-left"></i> Back to User Login
                    </a>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- ============================================ -->
<!-- USER DASHBOARD -->
<!-- ============================================ -->
<div id="userDashboard" class="page-container hidden">
    <div class="dashboard">
        <!-- Sidebar -->
        <div class="sidebar">
            <div style="text-align:center;margin-bottom:20px">
                <div class="chat-avatar" style="width:60px;height:60px;margin:0 auto;font-size:28px">🤖</div>
                <h3 style="color:var(--primary);margin-top:10px;font-family:'Orbitron'" id="sidebarBotName">RUHI X AI</h3>
                <span class="badge badge-active" id="sidebarStatus">● Online</span>
            </div>
            <ul class="sidebar-menu">
                <li><a href="#" class="active" onclick="showSection('chatSection',this)"><i class="fas fa-comments"></i> Chat</a></li>
                <li><a href="#" onclick="showSection('botSettings',this)"><i class="fas fa-robot"></i> Bot Settings</a></li>
                <li><a href="#" onclick="showSection('modelSection',this)"><i class="fas fa-brain"></i> AI Models</a></li>
                <li><a href="#" onclick="showSection('personaSection',this)"><i class="fas fa-masks-theater"></i> Persona</a></li>
                <li><a href="#" onclick="showSection('memorySection',this)"><i class="fas fa-memory"></i> Memory</a></li>
                <li><a href="#" onclick="showSection('apiSection',this)"><i class="fas fa-key"></i> API Keys</a></li>
                <li><a href="#" onclick="showSection('statsSection',this)"><i class="fas fa-chart-bar"></i> Stats</a></li>
                <li><a href="#" onclick="userLogout()" style="color:#ff4466"><i class="fas fa-sign-out-alt"></i> Logout</a></li>
            </ul>
        </div>

        <!-- Main Content -->
        <div class="main-content">
            <!-- Chat Section -->
            <div id="chatSection" class="section-tabs active">
                <div class="chat-container">
                    <div class="chat-header">
                        <div class="chat-avatar">🥀</div>
                        <div class="chat-info">
                            <h3 id="chatBotName">Ruhi Ji</h3>
                            <span>● Online • Powered by LLaMA 3.3 70B</span>
                        </div>
                    </div>
                    <div class="chat-messages" id="chatMessages">
                        <div class="message bot">
                            ʜᴇʏ ᴅᴇᴀʀ! 🥀 Main <strong>Ruhi Ji</strong> hun — tumhari AI best friend! 💕<br>
                            Mujhse kuch bhi pucho, main har sawaal ka jawab dungi! ✨<br>
                            <small>Powered by 20+ Knowledge Sources 🧠</small>
                            <div class="time">Just now</div>
                        </div>
                    </div>
                    <div class="chat-input-area">
                        <input type="text" class="chat-input" id="chatInput" 
                               placeholder="Type your message... 💬" 
                               onkeypress="if(event.key==='Enter')sendMessage()">
                        <button class="send-btn" onclick="sendMessage()">
                            <i class="fas fa-paper-plane"></i>
                        </button>
                    </div>
                </div>
            </div>

            <!-- Bot Settings Section -->
            <div id="botSettings" class="section-tabs">
                <div class="card">
                    <div class="card-title"><i class="fas fa-robot"></i> Bot Configuration</div>
                    <div class="bot-setup">
                        <div class="form-group">
                            <label>Bot Name</label>
                            <input type="text" class="form-input" id="setBotName" value="Ruhi" placeholder="Bot ka naam">
                        </div>
                        <div class="form-group">
                            <label>Language</label>
                            <select class="form-input" id="setLanguage">
                                <option value="hinglish">Hinglish</option>
                                <option value="hindi">Hindi</option>
                                <option value="english">English</option>
                                <option value="punjabi">Punjabi</option>
                                <option value="urdu">Urdu</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Group Memory (messages)</label>
                            <input type="number" class="form-input" id="setGroupMemory" value="20" min="5" max="100">
                        </div>
                        <div class="form-group">
                            <label>Private Memory (messages)</label>
                            <input type="number" class="form-input" id="setPrivateMemory" value="50" min="10" max="200">
                        </div>
                        <div class="form-group full-width">
                            <label>Custom System Prompt (Optional)</label>
                            <textarea class="form-input" id="setSystemPrompt" rows="4" 
                                      placeholder="Custom instructions for your bot..."></textarea>
                        </div>
                        <div class="full-width">
                            <button class="btn-primary" onclick="saveBotSettings()">
                                <i class="fas fa-save"></i> Save Settings
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Model Section -->
            <div id="modelSection" class="section-tabs">
                <div class="card">
                    <div class="card-title"><i class="fas fa-brain"></i> Select AI Model</div>
                    <div id="modelList" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:12px">
                    </div>
                </div>
            </div>

            <!-- Persona Section -->
            <div id="personaSection" class="section-tabs">
                <div class="card">
                    <div class="card-title"><i class="fas fa-masks-theater"></i> Select Persona</div>
                    <div id="personaList" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:12px">
                    </div>
                </div>
            </div>

            <!-- Memory Section -->
            <div id="memorySection" class="section-tabs">
                <div class="card">
                    <div class="card-title"><i class="fas fa-memory"></i> Chat Memory</div>
                    <p style="color:rgba(255,255,255,0.6);margin-bottom:16px">Your conversation history with AI</p>
                    <div id="memoryList"></div>
                    <button class="btn-primary" onclick="clearMemory()" style="margin-top:16px;max-width:300px">
                        <i class="fas fa-trash"></i> Clear All Memory
                    </button>
                </div>
            </div>

            <!-- API Section -->
            <div id="apiSection" class="section-tabs">
                <div class="card">
                    <div class="card-title"><i class="fas fa-key"></i> Your API Key</div>
                    <div class="form-group">
                        <label>Custom Groq API Key</label>
                        <input type="text" class="form-input" id="setCustomApiKey" placeholder="gsk_...">
                    </div>
                    <button class="btn-primary" onclick="saveCustomApiKey()" style="max-width:300px">
                        <i class="fas fa-save"></i> Save API Key
                    </button>
                </div>
            </div>

            <!-- Stats Section -->
            <div id="statsSection" class="section-tabs">
                <div class="stats-grid" id="userStatsGrid"></div>
            </div>
        </div>
    </div>
</div>

<!-- ============================================ -->
<!-- ADMIN DASHBOARD -->
<!-- ============================================ -->
<div id="adminDashboard" class="page-container hidden">
    <div class="dashboard">
        <!-- Admin Sidebar -->
        <div class="sidebar">
            <div style="text-align:center;margin-bottom:20px">
                <div class="chat-avatar" style="width:60px;height:60px;margin:0 auto;font-size:28px">👑</div>
                <h3 style="color:var(--accent);margin-top:10px;font-family:'Orbitron'">ADMIN</h3>
                <span class="badge badge-active">● RUHI X AI</span>
            </div>
            <ul class="sidebar-menu">
                <li><a href="#" class="active" onclick="showAdminSection('adminOverview',this)"><i class="fas fa-tachometer-alt"></i> Overview</a></li>
                <li><a href="#" onclick="showAdminSection('adminApiKeys',this)"><i class="fas fa-key"></i> API Keys</a></li>
                <li><a href="#" onclick="showAdminSection('adminUsers',this)"><i class="fas fa-users"></i> Users</a></li>
                <li><a href="#" onclick="showAdminSection('adminBots',this)"><i class="fas fa-robot"></i> Bots</a></li>
                <li><a href="#" onclick="showAdminSection('adminKnowledge',this)"><i class="fas fa-database"></i> Knowledge DB</a></li>
                <li><a href="#" onclick="showAdminSection('adminDownload',this)"><i class="fas fa-download"></i> Download Data</a></li>
                <li><a href="#" onclick="showAdminSection('adminSettings',this)"><i class="fas fa-cog"></i> Settings</a></li>
                <li><a href="#" onclick="adminLogout()" style="color:#ff4466"><i class="fas fa-sign-out-alt"></i> Logout</a></li>
            </ul>
        </div>

        <div class="main-content">
            <!-- Admin Overview -->
            <div id="adminOverview" class="section-tabs active">
                <div class="stats-grid" id="adminStatsGrid"></div>
                <div class="card">
                    <div class="card-title"><i class="fas fa-chart-line"></i> Recent Activity</div>
                    <div id="recentActivity"></div>
                </div>
            </div>

            <!-- Admin API Keys -->
            <div id="adminApiKeys" class="section-tabs">
                <div class="card">
                    <div class="card-title"><i class="fas fa-plus-circle"></i> Add API Keys (Max 12,000)</div>
                    <div class="form-group">
                        <label>API Keys (one per line)</label>
                        <textarea class="form-input" id="bulkApiKeys" rows="5" 
                                  placeholder="gsk_key1...&#10;gsk_key2...&#10;gsk_key3..."></textarea>
                    </div>
                    <button class="btn-primary" onclick="addBulkApiKeys()" style="max-width:300px">
                        <i class="fas fa-plus"></i> Add Keys
                    </button>
                </div>
                <div class="card">
                    <div class="card-title"><i class="fas fa-list"></i> All API Keys</div>
                    <div id="adminApiKeyList" class="api-key-list"></div>
                </div>
            </div>

            <!-- Admin Users -->
            <div id="adminUsers" class="section-tabs">
                <div class="card">
                    <div class="card-title"><i class="fas fa-users"></i> All Users</div>
                    <div style="overflow-x:auto">
                        <table class="data-table" id="usersTable">
                            <thead><tr>
                                <th>User ID</th><th>Username</th><th>Platform</th>
                                <th>Messages</th><th>Model</th><th>Persona</th><th>Last Active</th>
                            </tr></thead>
                            <tbody id="usersTableBody"></tbody>
                        </table>
                    </div>
                </div>
            </div>

            <!-- Admin Bots -->
            <div id="adminBots" class="section-tabs">
                <div class="card">
                    <div class="card-title"><i class="fas fa-robot"></i> Active Bots</div>
                    <div id="adminBotList"></div>
                </div>
            </div>

            <!-- Admin Knowledge -->
            <div id="adminKnowledge" class="section-tabs">
                <div class="card">
                    <div class="card-title"><i class="fas fa-database"></i> Connected Knowledge Sources (20+)</div>
                    <div id="knowledgeSourceList"></div>
                </div>
                <div class="card">
                    <div class="card-title"><i class="fas fa-search"></i> Test Knowledge Search</div>
                    <div class="form-group">
                        <input type="text" class="form-input" id="knowledgeQuery" placeholder="Search query...">
                    </div>
                    <button class="btn-primary" onclick="testKnowledge()" style="max-width:300px">
                        <i class="fas fa-search"></i> Search
                    </button>
                    <div id="knowledgeResults" style="margin-top:16px"></div>
                </div>
            </div>

            <!-- Admin Download -->
            <div id="adminDownload" class="section-tabs">
                <div class="card">
                    <div class="card-title"><i class="fas fa-download"></i> Download Data</div>
                    <div style="display:flex;gap:12px;flex-wrap:wrap">
                        <button class="download-btn" onclick="downloadData('api_keys')">
                            <i class="fas fa-key"></i> Download API Keys
                        </button>
                        <button class="download-btn" onclick="downloadData('users')">
                            <i class="fas fa-users"></i> Download Users
                        </button>
                        <button class="download-btn" onclick="downloadData('chat_memory')">
                            <i class="fas fa-comments"></i> Download Chat History
                        </button>
                        <button class="download-btn" onclick="downloadData('analytics')">
                            <i class="fas fa-chart-bar"></i> Download Analytics
                        </button>
                        <button class="download-btn" onclick="downloadData('all')">
                            <i class="fas fa-database"></i> Download All Data
                        </button>
                    </div>
                </div>
            </div>

            <!-- Admin Settings -->
            <div id="adminSettings" class="section-tabs">
                <div class="card">
                    <div class="card-title"><i class="fas fa-cog"></i> Platform Settings</div>
                    <div class="bot-setup">
                        <div class="form-group">
                            <label>Background Video URL</label>
                            <input type="text" class="form-input" id="settBgVideo" placeholder="Video URL">
                        </div>
                        <div class="form-group">
                            <label>Background Music URL</label>
                            <input type="text" class="form-input" id="settBgMusic" placeholder="Music URL">
                        </div>
                        <div class="form-group">
                            <label>Default Model</label>
                            <select class="form-input" id="settDefaultModel">
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Max API Keys</label>
                            <input type="number" class="form-input" id="settMaxKeys" value="12000">
                        </div>
                        <div class="full-width">
                            <button class="btn-primary" onclick="saveAdminSettings()">
                                <i class="fas fa-save"></i> Save Settings
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.2/socket.io.js"></script>
<script>
// ============================================================
// GLOBAL STATE
// ============================================================
let currentUser = null;
let isAdmin = false;
let socket = null;
let musicPlaying = false;

const MODELS = [
    {id: 'llama-3.3-70b-versatile', name: 'LLaMA 3.3 70B', desc: 'Most powerful, best quality', icon: '🏆'},
    {id: 'llama-3.1-70b-versatile', name: 'LLaMA 3.1 70B', desc: 'Great balance of speed & quality', icon: '⚡'},
    {id: 'llama-3.1-8b-instant', name: 'LLaMA 3.1 8B', desc: 'Super fast responses', icon: '🚀'},
    {id: 'llama3-70b-8192', name: 'LLaMA 3 70B', desc: 'Reliable & strong', icon: '💪'},
    {id: 'llama3-8b-8192', name: 'LLaMA 3 8B', desc: 'Quick & efficient', icon: '⚙️'},
    {id: 'mixtral-8x7b-32768', name: 'Mixtral 8x7B', desc: 'Great for long context', icon: '📚'},
    {id: 'gemma2-9b-it', name: 'Gemma 2 9B', desc: 'Google\'s compact model', icon: '💎'},
    {id: 'gemma-7b-it', name: 'Gemma 7B', desc: 'Lightweight & fast', icon: '✨'},
];

const PERSONAS = [
    {id: 'polite_girl', name: 'Polite Girl 🥀', desc: 'Pyaari, caring, sweet'},
    {id: 'cute_girl', name: 'Cute Girl 🌸', desc: 'Shy, innocent, adorable'},
    {id: 'savage_girl', name: 'Savage Girl 🔥', desc: 'Bold, confident, savage'},
    {id: 'professional', name: 'Professional 💼', desc: 'Formal, detailed, expert'},
    {id: 'romantic_girl', name: 'Romantic Girl 💕', desc: 'Loving, romantic, shayari'},
];

// ============================================================
// PARTICLES
// ============================================================
function createParticles() {
    const container = document.getElementById('particles');
    const colors = ['#00f5ff', '#ff00e5', '#ffaa00', '#4ade80', '#ff4466'];
    for (let i = 0; i < 50; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        particle.style.left = Math.random() * 100 + '%';
        particle.style.background = colors[Math.floor(Math.random() * colors.length)];
        particle.style.animationDuration = (5 + Math.random() * 15) + 's';
        particle.style.animationDelay = Math.random() * 10 + 's';
        particle.style.width = (2 + Math.random() * 4) + 'px';
        particle.style.height = particle.style.width;
        container.appendChild(particle);
    }
}
createParticles();

// ============================================================
// MUSIC CONTROL
// ============================================================
function toggleMusic() {
    const audio = document.getElementById('bgMusic');
    const icon = document.getElementById('musicIcon');
    const text = document.getElementById('musicText');
    if (musicPlaying) {
        audio.pause();
        icon.classList.add('paused');
        text.textContent = '🎵 Play';
        musicPlaying = false;
    } else {
        audio.play().catch(e => console.log('Audio play blocked'));
        icon.classList.remove('paused');
        text.textContent = '🎵 Playing';
        musicPlaying = true;
    }
}

// ============================================================
// TOAST NOTIFICATIONS
// ============================================================
function showToast(message, type='info') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    const icons = {success: 'check-circle', error: 'times-circle', info: 'info-circle'};
    toast.innerHTML = `<i class="fas fa-${icons[type] || 'info-circle'}"></i> ${message}`;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 4000);
}

// ============================================================
// LOGIN FUNCTIONS
// ============================================================
function showAdminLogin() {
    document.getElementById('loginForm').classList.add('hidden');
    document.getElementById('adminLoginForm').classList.remove('hidden');
}

function showUserLogin() {
    document.getElementById('adminLoginForm').classList.add('hidden');
    document.getElementById('loginForm').classList.remove('hidden');
}

async function userLogin() {
    const token = document.getElementById('botToken').value.trim();
    const apiKey = document.getElementById('userApiKey').value.trim();

    if (!token) {
        showToast('Bot Token daaliye!', 'error');
        return;
    }

    showToast('🔄 Bot activate ho raha hai...', 'info');

    // Start music on interaction
    if (!musicPlaying) toggleMusic();

    try {
        const res = await fetch('/api/user/login', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({bot_token: token, api_key: apiKey})
        });
        const data = await res.json();

        if (data.success) {
            currentUser = data.user;
            showToast('✅ ' + data.message, 'success');
            document.getElementById('loginPage').classList.add('hidden');
            document.getElementById('userDashboard').classList.remove('hidden');
            document.getElementById('sidebarBotName').textContent = data.user.bot_name || 'RUHI X AI';
            document.getElementById('chatBotName').textContent = (data.user.bot_name || 'Ruhi') + ' Ji';
            document.getElementById('navUserInfo').textContent = '👤 ' + (data.user.username || 'User');
            initSocket();
            loadModels();
            loadPersonas();
            loadUserStats();
        } else {
            showToast('❌ ' + data.message, 'error');
        }
    } catch (e) {
        showToast('❌ Connection error!', 'error');
    }
}

async function adminLogin() {
    const user = document.getElementById('adminUser').value.trim();
    const pass = document.getElementById('adminPass').value.trim();

    if (!user || !pass) {
        showToast('Username aur Password daaliye!', 'error');
        return;
    }

    if (!musicPlaying) toggleMusic();

    try {
        const res = await fetch('/api/admin/login', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username: user, password: pass})
        });
        const data = await res.json();

        if (data.success) {
            isAdmin = true;
            showToast('✅ Admin login successful!', 'success');
            document.getElementById('loginPage').classList.add('hidden');
            document.getElementById('adminDashboard').classList.remove('hidden');
            document.getElementById('navUserInfo').textContent = '👑 ADMIN';
            loadAdminData();
        } else {
            showToast('❌ ' + data.message, 'error');
        }
    } catch (e) {
        showToast('❌ Connection error!', 'error');
    }
}

function userLogout() {
    currentUser = null;
    document.getElementById('userDashboard').classList.add('hidden');
    document.getElementById('loginPage').classList.remove('hidden');
    document.getElementById('navUserInfo').textContent = '';
    showToast('👋 Logged out!', 'info');
}

function adminLogout() {
    isAdmin = false;
    document.getElementById('adminDashboard').classList.add('hidden');
    document.getElementById('loginPage').classList.remove('hidden');
    document.getElementById('navUserInfo').textContent = '';
    showToast('👋 Admin logged out!', 'info');
}

// ============================================================
// SECTION NAVIGATION
// ============================================================
function showSection(sectionId, el) {
    document.querySelectorAll('#userDashboard .section-tabs').forEach(s => s.classList.remove('active'));
    document.getElementById(sectionId).classList.add('active');
    document.querySelectorAll('#userDashboard .sidebar-menu a').forEach(a => a.classList.remove('active'));
    if (el) el.classList.add('active');
}

function showAdminSection(sectionId, el) {
    document.querySelectorAll('#adminDashboard .section-tabs').forEach(s => s.classList.remove('active'));
    document.getElementById(sectionId).classList.add('active');
    document.querySelectorAll('#adminDashboard .sidebar-menu a').forEach(a => a.classList.remove('active'));
    if (el) el.classList.add('active');
}

// ============================================================
// CHAT SYSTEM
// ============================================================
function initSocket() {
    socket = io();
    socket.on('connect', () => console.log('Socket connected'));
    socket.on('bot_response', (data) => {
        removeTyping();
        addMessage(data.message, 'bot');
    });
}

function addMessage(text, type) {
    const container = document.getElementById('chatMessages');
    const msg = document.createElement('div');
    msg.className = `message ${type}`;

    // Format code blocks
    let formatted = text.replace(/```(\w+)?\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>');
    formatted = formatted.replace(/`([^`]+)`/g, '<code>$1</code>');
    formatted = formatted.replace(/\n/g, '<br>');

    const time = new Date().toLocaleTimeString('en-US', {hour:'2-digit', minute:'2-digit'});
    msg.innerHTML = `${formatted}<div class="time">${time}</div>`;
    container.appendChild(msg);
    container.scrollTop = container.scrollHeight;
}

function showTyping() {
    const container = document.getElementById('chatMessages');
    const typing = document.createElement('div');
    typing.className = 'typing-indicator';
    typing.id = 'typingIndicator';
    typing.innerHTML = '<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>';
    container.appendChild(typing);
    container.scrollTop = container.scrollHeight;
}

function removeTyping() {
    const el = document.getElementById('typingIndicator');
    if (el) el.remove();
}

async function sendMessage() {
    const input = document.getElementById('chatInput');
    const text = input.value.trim();
    if (!text) return;

    addMessage(text, 'user');
    input.value = '';
    showTyping();

    try {
        const res = await fetch('/api/chat', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                message: text,
                user_id: currentUser?.user_id || 'web_' + Date.now()
            })
        });
        const data = await res.json();
        removeTyping();
        addMessage(data.reply || 'Error getting response', 'bot');
    } catch (e) {
        removeTyping();
        addMessage('❌ Connection error! Try again.', 'bot');
    }
}

// ============================================================
// LOAD UI DATA
// ============================================================
function loadModels() {
    const container = document.getElementById('modelList');
    container.innerHTML = '';
    MODELS.forEach(m => {
        const selected = currentUser?.model === m.id;
        container.innerHTML += `
            <div class="stat-card" style="cursor:pointer;${selected?'border-color:var(--primary);box-shadow:var(--glow)':''}" 
                 onclick="selectModel('${m.id}', this)">
                <div style="font-size:32px;margin-bottom:8px">${m.icon}</div>
                <div style="font-weight:600;color:var(--primary)">${m.name}</div>
                <div style="font-size:12px;color:rgba(255,255,255,0.5)">${m.desc}</div>
                ${selected?'<div class="badge badge-active" style="margin-top:8px">Selected</div>':''}
            </div>`;
    });
}

function loadPersonas() {
    const container = document.getElementById('personaList');
    container.innerHTML = '';
    PERSONAS.forEach(p => {
        const selected = currentUser?.persona === p.id;
        container.innerHTML += `
            <div class="stat-card" style="cursor:pointer;${selected?'border-color:var(--secondary);box-shadow:var(--glow-pink)':''}"
                 onclick="selectPersona('${p.id}', this)">
                <div style="font-size:24px;margin-bottom:8px">${p.name}</div>
                <div style="font-size:12px;color:rgba(255,255,255,0.5)">${p.desc}</div>
                ${selected?'<div class="badge badge-active" style="margin-top:8px">Active</div>':''}
            </div>`;
    });
}

async function selectModel(modelId, el) {
    try {
        const res = await fetch('/api/user/settings', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({user_id: currentUser.user_id, model: modelId})
        });
        const data = await res.json();
        if (data.success) {
            currentUser.model = modelId;
            loadModels();
            showToast('✅ Model changed!', 'success');
        }
    } catch (e) {
        showToast('❌ Error!', 'error');
    }
}

async function selectPersona(personaId, el) {
    try {
        const res = await fetch('/api/user/settings', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({user_id: currentUser.user_id, persona: personaId})
        });
        const data = await res.json();
        if (data.success) {
            currentUser.persona = personaId;
            loadPersonas();
            showToast('✅ Persona changed!', 'success');
        }
    } catch (e) {
        showToast('❌ Error!', 'error');
    }
}

async function saveBotSettings() {
    const data = {
        user_id: currentUser.user_id,
        bot_name: document.getElementById('setBotName').value,
        language: document.getElementById('setLanguage').value,
        memory_limit: parseInt(document.getElementById('setPrivateMemory').value)
    };

    try {
        const res = await fetch('/api/user/settings', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        const result = await res.json();
        if (result.success) {
            showToast('✅ Settings saved!', 'success');
            document.getElementById('sidebarBotName').textContent = data.bot_name;
            document.getElementById('chatBotName').textContent = data.bot_name + ' Ji';
        }
    } catch (e) {
        showToast('❌ Error!', 'error');
    }
}

async function saveCustomApiKey() {
    const key = document.getElementById('setCustomApiKey').value.trim();
    try {
        const res = await fetch('/api/user/settings', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({user_id: currentUser.user_id, custom_api_key: key})
        });
        const data = await res.json();
        if (data.success) showToast('✅ API Key saved!', 'success');
    } catch (e) {
        showToast('❌ Error!', 'error');
    }
}

async function clearMemory() {
    try {
        const res = await fetch('/api/user/clear-memory', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({user_id: currentUser.user_id})
        });
        const data = await res.json();
        if (data.success) {
            showToast('✅ Memory cleared!', 'success');
            document.getElementById('chatMessages').innerHTML = `
                <div class="message bot">Memory clear ho gayi! Fresh start 💕<div class="time">Now</div></div>`;
        }
    } catch (e) {
        showToast('❌ Error!', 'error');
    }
}

async function loadUserStats() {
    try {
        const res = await fetch('/api/user/stats?user_id=' + currentUser.user_id);
        const data = await res.json();
        if (data.success) {
            const grid = document.getElementById('userStatsGrid');
            grid.innerHTML = `
                <div class="stat-card"><div class="stat-number">${data.stats.message_count}</div><div class="stat-label">Messages</div></div>
                <div class="stat-card"><div class="stat-number">${data.stats.memory_count}</div><div class="stat-label">Memory Items</div></div>
                <div class="stat-card"><div class="stat-number">${data.stats.model || 'Default'}</div><div class="stat-label">Current Model</div></div>
                <div class="stat-card"><div class="stat-number">${data.stats.persona || 'polite_girl'}</div><div class="stat-label">Persona</div></div>
            `;
        }
    } catch (e) {}
}

// ============================================================
// ADMIN FUNCTIONS
// ============================================================
async function loadAdminData() {
    try {
        const res = await fetch('/api/admin/overview');
        const data = await res.json();
        if (data.success) {
            const grid = document.getElementById('adminStatsGrid');
            grid.innerHTML = `
                <div class="stat-card"><div class="stat-number">${data.stats.total_users}</div><div class="stat-label">Total Users</div></div>
                <div class="stat-card"><div class="stat-number">${data.stats.total_api_keys}</div><div class="stat-label">API Keys</div></div>
                <div class="stat-card"><div class="stat-number">${data.stats.active_bots}</div><div class="stat-label">Active Bots</div></div>
                <div class="stat-card"><div class="stat-number">${data.stats.total_messages}</div><div class="stat-label">Total Messages</div></div>
                <div class="stat-card"><div class="stat-number">${data.stats.total_memory}</div><div class="stat-label">Memory Items</div></div>
                <div class="stat-card"><div class="stat-number">${data.stats.knowledge_sources}</div><div class="stat-label">Knowledge DBs</div></div>
            `;
        }
    } catch (e) {}
}

async function addBulkApiKeys() {
    const keys = document.getElementById('bulkApiKeys').value.trim().split('\\n').filter(k => k.trim());
    if (keys.length === 0) {
        showToast('Koi key nahi daali!', 'error');
        return;
    }

    try {
        const res = await fetch('/api/admin/api-keys/add', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({keys: keys})
        });
        const data = await res.json();
        if (data.success) {
            showToast(`✅ ${data.added} keys added!`, 'success');
            document.getElementById('bulkApiKeys').value = '';
            loadAdminApiKeys();
        }
    } catch (e) {
        showToast('❌ Error!', 'error');
    }
}

async function loadAdminApiKeys() {
    try {
        const res = await fetch('/api/admin/api-keys');
        const data = await res.json();
        if (data.success) {
            const container = document.getElementById('adminApiKeyList');
            container.innerHTML = '';
            data.keys.forEach(k => {
                const masked = k.api_key.substring(0, 10) + '...' + k.api_key.slice(-4);
                container.innerHTML += `
                    <div class="api-key-item">
                        <span class="key-text">${masked}</span>
                        <span class="tag">Used: ${k.usage_count}/${k.max_usage}</span>
                        <span class="badge ${k.is_active?'badge-active':'badge-inactive'}">${k.is_active?'Active':'Inactive'}</span>
                        <button class="btn-small" onclick="deleteApiKey(${k.id})"><i class="fas fa-trash"></i></button>
                    </div>`;
            });
        }
    } catch (e) {}
}

async function deleteApiKey(id) {
    try {
        await fetch('/api/admin/api-keys/delete', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({id: id})
        });
        showToast('🗑️ Key deleted!', 'success');
        loadAdminApiKeys();
    } catch (e) {}
}

async function testKnowledge() {
    const query = document.getElementById('knowledgeQuery').value.trim();
    if (!query) return;

    document.getElementById('knowledgeResults').innerHTML = '<div class="typing-indicator"><div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div></div>';

    try {
        const res = await fetch('/api/admin/knowledge/search', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({query: query})
        });
        const data = await res.json();
        document.getElementById('knowledgeResults').innerHTML = `
            <div class="card" style="background:rgba(0,245,255,0.05)">
                <pre style="white-space:pre-wrap;color:var(--primary)">${data.results || 'No results'}</pre>
            </div>`;
    } catch (e) {
        document.getElementById('knowledgeResults').innerHTML = '<div style="color:#ff4466">Error searching</div>';
    }
}

async function downloadData(type) {
    try {
        window.open('/api/admin/download/' + type, '_blank');
        showToast('📥 Download started!', 'success');
    } catch (e) {
        showToast('❌ Download error!', 'error');
    }
}

async function saveAdminSettings() {
    const data = {
        background_video: document.getElementById('settBgVideo').value,
        background_music: document.getElementById('settBgMusic').value,
        default_model: document.getElementById('settDefaultModel').value,
        max_api_keys: document.getElementById('settMaxKeys').value
    };

    try {
        const res = await fetch('/api/admin/settings', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        const result = await res.json();
        if (result.success) showToast('✅ Settings saved!', 'success');
    } catch (e) {
        showToast('❌ Error!', 'error');
    }
}

// Auto-load admin sub-sections when clicked
document.addEventListener('DOMContentLoaded', () => {
    // Populate model select in admin
    const select = document.getElementById('settDefaultModel');
    if (select) {
        MODELS.forEach(m => {
            select.innerHTML += `<option value="${m.id}">${m.name}</option>`;
        });
    }
});
</script>
</body>
</html>'''

# ============================================================
# FLASK ROUTES
# ============================================================

@app.route('/')
def index():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key='background_video'")
    bg_video_row = c.fetchone()
    c.execute("SELECT value FROM settings WHERE key='background_music'")
    bg_music_row = c.fetchone()
    conn.close()

    bg_video = bg_video_row['value'] if bg_video_row else 'https://cdn.pixabay.com/video/2024/03/21/205164-925757498_large.mp4'
    bg_music = bg_music_row['value'] if bg_music_row else 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3'

    return render_template_string(HTML_TEMPLATE, bg_video=bg_video, bg_music=bg_music)

# ----- User Login -----
@app.route('/api/user/login', methods=['POST'])
def user_login():
    data = request.json
    bot_token = data.get('bot_token', '').strip()
    api_key = data.get('api_key', '').strip()

    if not bot_token:
        return jsonify({'success': False, 'message': 'Bot token required!'})

    # Validate bot token
    try:
        resp = requests.get(f'https://api.telegram.org/bot{bot_token}/getMe', timeout=10)
        if resp.status_code != 200:
            return jsonify({'success': False, 'message': 'Invalid bot token!'})
        bot_info = resp.json().get('result', {})
        bot_username = bot_info.get('username', '')
        bot_first_name = bot_info.get('first_name', 'Bot')
    except:
        return jsonify({'success': False, 'message': 'Cannot verify bot token!'})

    user_id = f"bot_{bot_token[-10:]}"

    # Save user
    conn = get_db()
    c = conn.cursor()
    c.execute("""INSERT OR REPLACE INTO users 
                (user_id, username, platform, bot_token, bot_name, bot_active, custom_api_key, created_at, last_active)
                VALUES (?, ?, 'telegram', ?, ?, 1, ?, ?, ?)""",
             (user_id, bot_first_name, bot_token, bot_first_name,
              api_key if api_key else None,
              datetime.now().isoformat(), datetime.now().isoformat()))
    conn.commit()

    # Get user data
    c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = dict(c.fetchone())
    conn.close()

    # Start telegram bot
    success, msg = TelegramBotManager.start_bot(
        bot_token, user_id, bot_first_name
    )

    log_analytics('login', user_id, {'platform': 'web', 'bot': bot_username})

    return jsonify({
        'success': True,
        'message': f'Bot @{bot_username} activated! {msg}',
        'user': {
            'user_id': user_id,
            'username': bot_first_name,
            'bot_name': bot_first_name,
            'bot_username': bot_username,
            'model': user.get('model', 'llama-3.3-70b-versatile'),
            'persona': user.get('persona', 'polite_girl'),
            'language': user.get('language', 'hinglish'),
        }
    })

# ----- Admin Login -----
@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    data = request.json
    username = data.get('username', '')
    password = data.get('password', '')

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key='admin_username'")
    admin_user = c.fetchone()
    c.execute("SELECT value FROM settings WHERE key='admin_password'")
    admin_pass = c.fetchone()
    conn.close()

    if (admin_user and admin_user['value'] == username and
        admin_pass and admin_pass['value'] == password):
        session['is_admin'] = True
        return jsonify({'success': True, 'message': 'Admin login successful!'})

    return jsonify({'success': False, 'message': 'Invalid credentials!'})

# ----- Chat API -----
@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    message = data.get('message', '')
    user_id = data.get('user_id', 'web_anon')

    if not message:
        return jsonify({'reply': 'Kuch to likh do! 😊'})

    reply = AIEngine.generate_response(
        user_id=user_id,
        message=message,
        platform='web'
    )

    return jsonify({'reply': reply, 'success': True})

# ----- User Settings -----
@app.route('/api/user/settings', methods=['POST'])
def update_user_settings():
    data = request.json
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'User ID required'})

    conn = get_db()
    c = conn.cursor()

    updates = []
    params = []
    for field in ['model', 'persona', 'language', 'bot_name', 'memory_limit', 'custom_api_key', 'city', 'username']:
        if field in data:
            updates.append(f"{field} = ?")
            params.append(data[field])

    if updates:
        params.append(user_id)
        query = f"UPDATE users SET {', '.join(updates)} WHERE user_id = ?"
        c.execute(query, params)
        conn.commit()

    conn.close()
    return jsonify({'success': True, 'message': 'Settings updated!'})

# ----- User Stats -----
@app.route('/api/user/stats')
def user_stats():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'success': False})

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = c.fetchone()
    c.execute("SELECT COUNT(*) as cnt FROM chat_memory WHERE user_id=?", (user_id,))
    mem = c.fetchone()
    conn.close()

    if user:
        return jsonify({
            'success': True,
            'stats': {
                'message_count': user['message_count'],
                'memory_count': mem['cnt'],
                'model': user['model'],
                'persona': user['persona']
            }
        })
    return jsonify({'success': False})

# ----- Clear Memory -----
@app.route('/api/user/clear-memory', methods=['POST'])
def clear_memory():
    data = request.json
    user_id = data.get('user_id')
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM chat_memory WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Memory cleared!'})

# ----- Admin Overview -----
@app.route('/api/admin/overview')
def admin_overview():
    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT COUNT(*) as cnt FROM users")
    total_users = c.fetchone()['cnt']

    c.execute("SELECT COUNT(*) as cnt FROM api_keys WHERE is_active=1")
    total_keys = c.fetchone()['cnt']

    c.execute("SELECT COUNT(*) as cnt FROM bot_instances WHERE is_active=1")
    active_bots = c.fetchone()['cnt']

    c.execute("SELECT SUM(message_count) as total FROM users")
    row = c.fetchone()
    total_msgs = row['total'] if row['total'] else 0

    c.execute("SELECT COUNT(*) as cnt FROM chat_memory")
    total_memory = c.fetchone()['cnt']

    c.execute("SELECT COUNT(*) as cnt FROM knowledge_sources WHERE is_active=1")
    knowledge = c.fetchone()['cnt']

    conn.close()

    return jsonify({
        'success': True,
        'stats': {
            'total_users': total_users,
            'total_api_keys': total_keys,
            'active_bots': len(TelegramBotManager.active_bots),
            'total_messages': total_msgs,
            'total_memory': total_memory,
            'knowledge_sources': knowledge
        }
    })

# ----- Admin API Keys -----
@app.route('/api/admin/api-keys')
def get_api_keys():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM api_keys ORDER BY created_at DESC")
    keys = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify({'success': True, 'keys': keys})

@app.route('/api/admin/api-keys/add', methods=['POST'])
def add_api_keys():
    data = request.json
    keys = data.get('keys', [])
    added = 0

    conn = get_db()
    c = conn.cursor()

    for key in keys:
        key = key.strip()
        if key and key.startswith('gsk_'):
            try:
                c.execute("INSERT INTO api_keys (api_key, key_name) VALUES (?, ?)",
                         (key, f'Key_{added+1}'))
                added += 1
            except:
                pass

    conn.commit()
    conn.close()
    return jsonify({'success': True, 'added': added})

@app.route('/api/admin/api-keys/delete', methods=['POST'])
def delete_api_key():
    data = request.json
    key_id = data.get('id')
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM api_keys WHERE id=?", (key_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# ----- Admin Knowledge Search -----
@app.route('/api/admin/knowledge/search', methods=['POST'])
def knowledge_search():
    data = request.json
    query = data.get('query', '')
    results = KnowledgeAggregator.aggregate_knowledge(query)
    return jsonify({'success': True, 'results': results})

# ----- Admin Download -----
@app.route('/api/admin/download/<data_type>')
def download_data(data_type):
    conn = get_db()
    c = conn.cursor()

    if data_type == 'api_keys':
        c.execute("SELECT api_key FROM api_keys WHERE is_active=1")
        data = [row['api_key'] for row in c.fetchall()]
        content = '\n'.join(data)
        conn.close()
        return Response(content, mimetype='text/plain',
                       headers={'Content-Disposition': 'attachment; filename=api_keys.txt'})

    elif data_type == 'users':
        c.execute("SELECT * FROM users")
        data = [dict(row) for row in c.fetchall()]
        conn.close()
        return Response(json.dumps(data, indent=2), mimetype='application/json',
                       headers={'Content-Disposition': 'attachment; filename=users.json'})

    elif data_type == 'chat_memory':
        c.execute("SELECT * FROM chat_memory ORDER BY timestamp DESC LIMIT 10000")
        data = [dict(row) for row in c.fetchall()]
        conn.close()
        return Response(json.dumps(data, indent=2), mimetype='application/json',
                       headers={'Content-Disposition': 'attachment; filename=chat_memory.json'})

    elif data_type == 'analytics':
        c.execute("SELECT * FROM analytics ORDER BY timestamp DESC LIMIT 10000")
        data = [dict(row) for row in c.fetchall()]
        conn.close()
        return Response(json.dumps(data, indent=2), mimetype='application/json',
                       headers={'Content-Disposition': 'attachment; filename=analytics.json'})

    elif data_type == 'all':
        all_data = {}
        for table in ['api_keys', 'users', 'chat_memory', 'bot_instances', 'settings', 'analytics']:
            c.execute(f"SELECT * FROM {table}")
            all_data[table] = [dict(row) for row in c.fetchall()]
        conn.close()
        return Response(json.dumps(all_data, indent=2), mimetype='application/json',
                       headers={'Content-Disposition': 'attachment; filename=full_backup.json'})

    conn.close()
    return jsonify({'error': 'Invalid type'})

# ----- Admin Settings -----
@app.route('/api/admin/settings', methods=['POST'])
def save_admin_settings():
    data = request.json
    conn = get_db()
    c = conn.cursor()

    for key, value in data.items():
        if value:
            c.execute("INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES (?, ?, ?)",
                     (key, str(value), datetime.now().isoformat()))

    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Settings saved!'})

# ----- Socket Events -----
@socketio.on('connect')
def handle_connect():
    logger.info(f"Client connected: {request.sid}")

@socketio.on('send_message')
def handle_socket_message(data):
    message = data.get('message', '')
    user_id = data.get('user_id', 'web_anon')

    reply = AIEngine.generate_response(
        user_id=user_id,
        message=message,
        platform='web'
    )

    emit('bot_response', {'message': reply})

# ============================================================
# AUTO-START SAVED BOTS
# ============================================================

def auto_start_bots():
    """Database se saved bots ko auto-start karta hai"""
    time.sleep(5)  # Wait for server to start
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM bot_instances WHERE is_active=1")
        bots = c.fetchall()
        conn.close()

        for bot in bots:
            try:
                TelegramBotManager.start_bot(
                    bot['bot_token'],
                    bot['owner_id'],
                    bot['bot_name'],
                    bot['persona'],
                    bot['language'],
                    bot['model']
                )
                logger.info(f"✅ Auto-started bot: {bot['bot_name']}")
            except Exception as e:
                logger.error(f"❌ Failed to auto-start bot: {str(e)}")
    except Exception as e:
        logger.error(f"Auto-start error: {str(e)}")

# ============================================================
# MAIN
# ============================================================

if __name__ == '__main__':
    init_database()

    # Auto-start saved bots in background
    threading.Thread(target=auto_start_bots, daemon=True).start()

    port = int(os.environ.get('PORT', 10000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)
    