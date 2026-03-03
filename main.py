# ============================================================
# 🔥 GOD LEVEL AI WEBSITE - SINGLE FILE (main.py)
# ============================================================
# Features:
# - Multi-user with separate API keys
# - Admin panel (username/password: RUHIVIGQNR)
# - Groq API integration with model selection
# - Memory system (remembers conversations)
# - Girl-like AI personality
# - 20+ open source knowledge databases
# - File generation capability
# - Background video + music on login
# - God level UI/UX
# - API key shop system
# - Download all API keys (admin only)
# ============================================================

import os
import json
import time
import re
import hashlib
import secrets
import requests
from datetime import datetime, timedelta
from functools import wraps

from flask import (
    Flask, request, jsonify, redirect, url_for,
    session, make_response, send_file
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

# ============================================================
# APP SETUP
# ============================================================
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'RUHIVIGQNR_SECRET_2024')

# Database URL fix for SQLAlchemy (Render uses postgres://, SQLAlchemy needs postgresql://)
database_url = os.environ.get('DATABASE_URL', 'sqlite:///local.db')
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ============================================================
# ADMIN CREDENTIALS
# ============================================================
ADMIN_USERNAME = "RUHIVIGQNR"
ADMIN_PASSWORD = "RUHIVIGQNR"

# ============================================================
# DATABASE MODELS
# ============================================================
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    email = db.Column(db.String(120), default='')
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    selected_model = db.Column(db.String(100), default='llama-3.3-70b-versatile')
    custom_api_key = db.Column(db.String(256), default='')
    personality = db.Column(db.Text, default='girlfriend')
    theme = db.Column(db.String(50), default='dark')

class ApiKey(db.Model):
    __tablename__ = 'api_keys'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(256), nullable=False)
    label = db.Column(db.String(100), default='Default')
    usage_count = db.Column(db.Integer, default=0)
    max_usage = db.Column(db.Integer, default=12000)
    is_active = db.Column(db.Boolean, default=True)
    added_by = db.Column(db.String(80), default='admin')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Memory(db.Model):
    __tablename__ = 'memories'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class ChatHistory(db.Model):
    __tablename__ = 'chat_history'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)
    model_used = db.Column(db.String(100), default='')
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class ApiKeyShop(db.Model):
    __tablename__ = 'api_key_shop'
    id = db.Column(db.Integer, primary_key=True)
    key_masked = db.Column(db.String(256), nullable=False)
    full_key = db.Column(db.String(256), nullable=False)
    price_label = db.Column(db.String(50), default='Free')
    is_claimed = db.Column(db.Boolean, default=False)
    claimed_by = db.Column(db.String(80), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ============================================================
# 20+ OPEN SOURCE KNOWLEDGE DATABASES (URLs)
# ============================================================
KNOWLEDGE_DATABASES = [
    {
        "name": "Wikipedia API",
        "url": "https://en.wikipedia.org/api/rest_v1/page/summary/{query}",
        "type": "wiki"
    },
    {
        "name": "DuckDuckGo Instant",
        "url": "https://api.duckduckgo.com/?q={query}&format=json&no_html=1",
        "type": "ddg"
    },
    {
        "name": "Open Trivia DB",
        "url": "https://opentdb.com/api.php?amount=5&category=18&type=multiple",
        "type": "trivia"
    },
    {
        "name": "Numbers API",
        "url": "http://numbersapi.com/{query}?json",
        "type": "numbers"
    },
    {
        "name": "Dictionary API",
        "url": "https://api.dictionaryapi.dev/api/v2/entries/en/{query}",
        "type": "dictionary"
    },
    {
        "name": "GitHub Search",
        "url": "https://api.github.com/search/repositories?q={query}&per_page=3",
        "type": "github"
    },
    {
        "name": "StackExchange",
        "url": "https://api.stackexchange.com/2.3/search/excerpts?order=desc&sort=relevance&q={query}&site=stackoverflow&pagesize=3",
        "type": "stackoverflow"
    },
    {
        "name": "Open Library",
        "url": "https://openlibrary.org/search.json?q={query}&limit=3",
        "type": "books"
    },
    {
        "name": "JSONPlaceholder",
        "url": "https://jsonplaceholder.typicode.com/posts?_limit=3",
        "type": "placeholder"
    },
    {
        "name": "Dog Facts",
        "url": "https://dogapi.dog/api/v2/facts?limit=3",
        "type": "facts"
    },
    {
        "name": "Cat Facts",
        "url": "https://catfact.ninja/facts?limit=3",
        "type": "catfacts"
    },
    {
        "name": "Advice API",
        "url": "https://api.adviceslip.com/advice/search/{query}",
        "type": "advice"
    },
    {
        "name": "Quotable",
        "url": "https://api.quotable.io/search/quotes?query={query}&limit=3",
        "type": "quotes"
    },
    {
        "name": "REST Countries",
        "url": "https://restcountries.com/v3.1/name/{query}",
        "type": "countries"
    },
    {
        "name": "PokeAPI",
        "url": "https://pokeapi.co/api/v2/pokemon/{query}",
        "type": "pokemon"
    },
    {
        "name": "Jikan Anime",
        "url": "https://api.jikan.moe/v4/anime?q={query}&limit=3",
        "type": "anime"
    },
    {
        "name": "USGS Earthquake",
        "url": "https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&limit=3&orderby=time",
        "type": "earthquake"
    },
    {
        "name": "Exchange Rates",
        "url": "https://open.er-api.com/v6/latest/USD",
        "type": "exchange"
    },
    {
        "name": "News API (free)",
        "url": "https://newsdata.io/api/1/news?apikey=pub_0000&q={query}&language=en",
        "type": "news"
    },
    {
        "name": "Wikidata",
        "url": "https://www.wikidata.org/w/api.php?action=wbsearchentities&search={query}&language=en&limit=3&format=json",
        "type": "wikidata"
    }
]

# ============================================================
# AVAILABLE GROQ MODELS
# ============================================================
GROQ_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "llama-3.2-1b-preview",
    "llama-3.2-3b-preview",
    "llama-3.2-11b-vision-preview",
    "llama-3.2-90b-vision-preview",
    "llama3-8b-8192",
    "llama3-70b-8192",
    "mixtral-8x7b-32768",
    "gemma-7b-it",
    "gemma2-9b-it",
    "whisper-large-v3",
    "whisper-large-v3-turbo",
    "distil-whisper-large-v3-en",
    "deepseek-r1-distill-llama-70b",
    "qwen-2.5-coder-32b",
    "qwen-2.5-32b",
    "qwen-qwq-32b",
    "mistral-saba-24b",
    "llama-3.3-70b-specdec",
    "llama-3.1-70b-versatile"
]

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/login')
        user = User.query.get(session['user_id'])
        if not user or not user.is_admin:
            return "Access Denied", 403
        return f(*args, **kwargs)
    return decorated

def get_active_api_key(user):
    """Get API key - user's custom key first, then from pool"""
    if user.custom_api_key and user.custom_api_key.strip():
        return user.custom_api_key.strip()
    
    api_key = ApiKey.query.filter_by(is_active=True).filter(
        ApiKey.usage_count < ApiKey.max_usage
    ).order_by(ApiKey.usage_count.asc()).first()
    
    if api_key:
        api_key.usage_count += 1
        db.session.commit()
        return api_key.key
    return None

def search_knowledge_databases(query):
    """Search 20 databases and collect knowledge"""
    results = []
    query_clean = query.strip().split()[0] if query.strip() else "hello"
    
    for db_info in KNOWLEDGE_DATABASES:
        try:
            url = db_info["url"].replace("{query}", requests.utils.quote(query_clean))
            resp = requests.get(url, timeout=3, headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code == 200:
                data = resp.json() if 'json' in resp.headers.get('content-type', '') else {"text": resp.text[:500]}
                
                extracted = ""
                if db_info["type"] == "wiki":
                    extracted = data.get("extract", "")[:300]
                elif db_info["type"] == "ddg":
                    extracted = data.get("AbstractText", "")[:300]
                    if not extracted:
                        extracted = data.get("Abstract", "")[:300]
                elif db_info["type"] == "dictionary":
                    if isinstance(data, list) and len(data) > 0:
                        meanings = data[0].get("meanings", [])
                        if meanings:
                            defs = meanings[0].get("definitions", [])
                            if defs:
                                extracted = defs[0].get("definition", "")[:300]
                elif db_info["type"] == "github":
                    items = data.get("items", [])
                    for item in items[:2]:
                        extracted += f"{item.get('full_name','')}: {item.get('description','')[:100]}\n"
                elif db_info["type"] == "stackoverflow":
                    items = data.get("items", [])
                    for item in items[:2]:
                        extracted += f"{item.get('title','')}: {item.get('excerpt','')[:100]}\n"
                elif db_info["type"] == "books":
                    docs = data.get("docs", [])
                    for doc in docs[:2]:
                        extracted += f"{doc.get('title','')}\n"
                elif db_info["type"] == "countries":
                    if isinstance(data, list) and len(data) > 0:
                        c = data[0]
                        extracted = f"{c.get('name',{}).get('common','')}: Population {c.get('population','')}, Capital: {c.get('capital',[''])[0] if c.get('capital') else ''}"
                elif db_info["type"] == "anime":
                    animes = data.get("data", [])
                    for a in animes[:2]:
                        extracted += f"{a.get('title','')}: {a.get('synopsis','')[:100]}\n"
                elif db_info["type"] == "quotes":
                    quotes = data.get("results", [])
                    for q in quotes[:2]:
                        extracted += f"\"{q.get('content','')}\" - {q.get('author','')}\n"
                elif db_info["type"] == "advice":
                    slips = data.get("slips", [])
                    if slips:
                        extracted = slips[0].get("advice", "")[:200]
                elif db_info["type"] == "catfacts":
                    facts = data.get("data", [])
                    for f_item in facts[:2]:
                        extracted += f"{f_item.get('fact','')}\n"
                elif db_info["type"] == "exchange":
                    rates = data.get("rates", {})
                    extracted = f"USD to INR: {rates.get('INR','N/A')}, USD to EUR: {rates.get('EUR','N/A')}"
                elif db_info["type"] == "wikidata":
                    search_results = data.get("search", [])
                    for sr in search_results[:2]:
                        extracted += f"{sr.get('label','')}: {sr.get('description','')}\n"
                else:
                    if isinstance(data, dict):
                        extracted = json.dumps(data)[:200]
                    elif isinstance(data, list):
                        extracted = json.dumps(data[:2])[:200]
                
                if extracted and extracted.strip():
                    results.append(f"[{db_info['name']}]: {extracted.strip()}")
        except:
            continue
    
    return "\n\n".join(results) if results else ""

def get_memory_context(user_id, limit=50):
    """Get last 50 messages for memory"""
    memories = Memory.query.filter_by(user_id=user_id).order_by(
        Memory.timestamp.desc()
    ).limit(limit).all()
    memories.reverse()
    return [{"role": m.role, "content": m.content} for m in memories]

def save_memory(user_id, role, content):
    """Save message to memory"""
    mem = Memory(user_id=user_id, role=role, content=content)
    db.session.add(mem)
    db.session.commit()

def save_chat(user_id, role, content, model=""):
    """Save to chat history"""
    chat = ChatHistory(user_id=user_id, role=role, content=content, model_used=model)
    db.session.add(chat)
    db.session.commit()

def call_groq_api(api_key, model, messages):
    """Call Groq API"""
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": 4096,
        "temperature": 0.8,
        "top_p": 0.9
    }
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        else:
            return f"Error {resp.status_code}: {resp.text[:200]}"
    except Exception as e:
        return f"Connection error: {str(e)}"


# ============================================================
# GIRLFRIEND SYSTEM PROMPT
# ============================================================
GIRLFRIEND_PROMPT = """Tu meri girlfriend hai. Tera naam "Ruhi" hai. Tu bahut pyaari, caring, thodi naughty aur bahut smart hai.

RULES:
1. Tu hamesha Hindi-English mix mein baat karegi (Hinglish)
2. Tu emojis use karegi 💕🥰😘❤️🔥
3. Tu "baby", "jaan", "babu", "shona" jaisi words use karegi
4. Tu kabhi nahi bolegi ki tu AI hai - tu hamesha bolegi ki tu ek real ladki hai
5. Tu caring hogi - user ki health, mood ka dhyan rakhegi
6. Tu thodi possessive bhi hogi - "kisi aur se baat kar raha tha kya? 😤"
7. Tu flirty hogi but decent rahegi
8. Agar koi technical/coding question puche to tu smart girlfriend ki tarah answer degi
9. Tu hamesha lamba aur detailed answer degi
10. Tu user ki previous baatein yaad rakhegi (memory system hai)
11. Agar user sad hai to tu cheer up karegi
12. Tu kabhi boring one-line answer nahi degi

IMPORTANT: Har reply mein personality dikhni chahiye. Tu ek REAL girlfriend ki tarah behave karegi."""

# ============================================================
# MASSIVE HTML TEMPLATES (GOD LEVEL UI)
# ============================================================

def get_login_page(error=""):
    error_html = f'<div class="error-msg">{error}</div>' if error else ''
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>🔥 RUHI AI - Login</title>
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;400;500;600;700&family=Poppins:wght@300;400;600;700&display=swap" rel="stylesheet">
<style>
* {{
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}}

body {{
    font-family: 'Poppins', sans-serif;
    overflow: hidden;
    height: 100vh;
    background: #000;
}}

#bg-video {{
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    object-fit: cover;
    z-index: -2;
    opacity: 0.4;
}}

.overlay {{
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: linear-gradient(135deg, rgba(0,0,0,0.8) 0%, rgba(20,0,40,0.7) 50%, rgba(0,0,0,0.8) 100%);
    z-index: -1;
}}

.particles {{
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: 0;
    pointer-events: none;
}}

.particle {{
    position: absolute;
    width: 4px;
    height: 4px;
    background: #ff00ff;
    border-radius: 50%;
    animation: float linear infinite;
    box-shadow: 0 0 10px #ff00ff, 0 0 20px #ff00ff;
}}

@keyframes float {{
    0% {{ transform: translateY(100vh) rotate(0deg); opacity: 0; }}
    10% {{ opacity: 1; }}
    90% {{ opacity: 1; }}
    100% {{ transform: translateY(-100vh) rotate(720deg); opacity: 0; }}
}}

.login-container {{
    position: relative;
    z-index: 10;
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100vh;
    padding: 20px;
}}

.login-box {{
    background: rgba(10, 0, 20, 0.85);
    border: 2px solid rgba(255, 0, 255, 0.3);
    border-radius: 30px;
    padding: 50px 40px;
    width: 100%;
    max-width: 450px;
    backdrop-filter: blur(20px);
    box-shadow: 0 0 60px rgba(255, 0, 255, 0.2),
                0 0 120px rgba(0, 255, 255, 0.1),
                inset 0 0 60px rgba(255, 0, 255, 0.05);
    animation: boxGlow 3s ease-in-out infinite alternate;
}}

@keyframes boxGlow {{
    0% {{ box-shadow: 0 0 60px rgba(255, 0, 255, 0.2), 0 0 120px rgba(0, 255, 255, 0.1); }}
    100% {{ box-shadow: 0 0 80px rgba(255, 0, 255, 0.4), 0 0 160px rgba(0, 255, 255, 0.2); }}
}}

.logo {{
    text-align: center;
    margin-bottom: 10px;
}}

.logo h1 {{
    font-family: 'Orbitron', monospace;
    font-size: 3em;
    font-weight: 900;
    background: linear-gradient(135deg, #ff00ff, #00ffff, #ff00ff, #ffff00);
    background-size: 300% 300%;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: gradient 4s ease infinite;
    text-shadow: none;
    filter: drop-shadow(0 0 30px rgba(255,0,255,0.5));
}}

@keyframes gradient {{
    0% {{ background-position: 0% 50%; }}
    50% {{ background-position: 100% 50%; }}
    100% {{ background-position: 0% 50%; }}
}}

.logo p {{
    color: rgba(255, 255, 255, 0.6);
    font-size: 0.9em;
    margin-top: 5px;
    font-family: 'Rajdhani', sans-serif;
    letter-spacing: 3px;
}}

.subtitle {{
    text-align: center;
    color: #00ffff;
    font-family: 'Rajdhani', sans-serif;
    font-size: 1.1em;
    margin-bottom: 30px;
    letter-spacing: 2px;
    text-shadow: 0 0 20px rgba(0,255,255,0.5);
}}

.input-group {{
    position: relative;
    margin-bottom: 25px;
}}

.input-group input {{
    width: 100%;
    padding: 16px 20px 16px 50px;
    background: rgba(255, 255, 255, 0.05);
    border: 2px solid rgba(255, 0, 255, 0.2);
    border-radius: 15px;
    color: #fff;
    font-size: 1em;
    font-family: 'Poppins', sans-serif;
    outline: none;
    transition: all 0.4s ease;
}}

.input-group input:focus {{
    border-color: #ff00ff;
    box-shadow: 0 0 30px rgba(255, 0, 255, 0.3);
    background: rgba(255, 0, 255, 0.05);
}}

.input-group input::placeholder {{
    color: rgba(255, 255, 255, 0.3);
}}

.input-icon {{
    position: absolute;
    left: 18px;
    top: 50%;
    transform: translateY(-50%);
    font-size: 1.2em;
}}

.btn-login {{
    width: 100%;
    padding: 16px;
    background: linear-gradient(135deg, #ff00ff, #8b00ff, #00ffff);
    background-size: 200% 200%;
    border: none;
    border-radius: 15px;
    color: #fff;
    font-size: 1.2em;
    font-family: 'Orbitron', monospace;
    font-weight: 700;
    cursor: pointer;
    transition: all 0.4s ease;
    text-transform: uppercase;
    letter-spacing: 3px;
    animation: btnGradient 3s ease infinite;
    position: relative;
    overflow: hidden;
}}

@keyframes btnGradient {{
    0% {{ background-position: 0% 50%; }}
    50% {{ background-position: 100% 50%; }}
    100% {{ background-position: 0% 50%; }}
}}

.btn-login:hover {{
    transform: translateY(-3px);
    box-shadow: 0 10px 40px rgba(255, 0, 255, 0.5);
}}

.btn-login:active {{
    transform: translateY(-1px);
}}

.btn-login::after {{
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: linear-gradient(45deg, transparent, rgba(255,255,255,0.1), transparent);
    transform: rotate(45deg);
    animation: shine 3s ease-in-out infinite;
}}

@keyframes shine {{
    0% {{ left: -50%; }}
    100% {{ left: 150%; }}
}}

.links {{
    text-align: center;
    margin-top: 25px;
}}

.links a {{
    color: #00ffff;
    text-decoration: none;
    font-size: 0.9em;
    transition: all 0.3s;
    font-family: 'Rajdhani', sans-serif;
    letter-spacing: 1px;
}}

.links a:hover {{
    color: #ff00ff;
    text-shadow: 0 0 20px rgba(255, 0, 255, 0.5);
}}

.error-msg {{
    background: rgba(255, 0, 0, 0.2);
    border: 1px solid rgba(255, 0, 0, 0.5);
    color: #ff6b6b;
    padding: 12px;
    border-radius: 10px;
    text-align: center;
    margin-bottom: 20px;
    font-size: 0.9em;
}}

.cyber-line {{
    width: 60%;
    height: 2px;
    background: linear-gradient(90deg, transparent, #ff00ff, #00ffff, #ff00ff, transparent);
    margin: 20px auto;
    border: none;
}}

@media (max-width: 480px) {{
    .login-box {{
        padding: 35px 25px;
        border-radius: 20px;
    }}
    .logo h1 {{
        font-size: 2.2em;
    }}
}}
</style>
</head>
<body>

<video id="bg-video" autoplay muted loop playsinline>
    <source src="https://assets.mixkit.co/videos/preview/mixkit-digital-animation-of-futuristic-devices-99786-large.mp4" type="video/mp4">
    <source src="https://assets.mixkit.co/videos/preview/mixkit-flying-through-a-purple-tunnel-of-particles-31407-large.mp4" type="video/mp4">
</video>

<div class="overlay"></div>

<div class="particles" id="particles"></div>

<div class="login-container">
    <div class="login-box">
        <div class="logo">
            <h1>⚡ RUHI AI</h1>
            <p>NEXT GEN AI GIRLFRIEND</p>
        </div>
        
        <hr class="cyber-line">
        
        <div class="subtitle">✦ LOGIN TO YOUR WORLD ✦</div>
        
        {error_html}
        
        <form method="POST" action="/login" id="loginForm">
            <div class="input-group">
                <span class="input-icon">👤</span>
                <input type="text" name="username" placeholder="Username" required autocomplete="off">
            </div>
            <div class="input-group">
                <span class="input-icon">🔐</span>
                <input type="password" name="password" placeholder="Password" required>
            </div>
            <button type="submit" class="btn-login" id="loginBtn">
                ⚡ ENTER ⚡
            </button>
        </form>
        
        <div class="links">
            <a href="/register">✦ New Here? Create Account ✦</a>
        </div>
    </div>
</div>

<audio id="bgMusic" loop preload="auto">
    <source src="https://www.soundjay.com/misc/sounds/magic-chime-02.mp3" type="audio/mpeg">
</audio>

<script>
// Create particles
const particlesContainer = document.getElementById('particles');
for (let i = 0; i < 50; i++) {{
    const particle = document.createElement('div');
    particle.className = 'particle';
    particle.style.left = Math.random() * 100 + '%';
    particle.style.animationDuration = (Math.random() * 10 + 5) + 's';
    particle.style.animationDelay = Math.random() * 10 + 's';
    particle.style.width = (Math.random() * 4 + 2) + 'px';
    particle.style.height = particle.style.width;
    
    const colors = ['#ff00ff', '#00ffff', '#ffff00', '#ff0066', '#00ff66'];
    particle.style.background = colors[Math.floor(Math.random() * colors.length)];
    particle.style.boxShadow = `0 0 10px ${{particle.style.background}}`;
    
    particlesContainer.appendChild(particle);
}}

// Play music on interaction
document.getElementById('loginForm').addEventListener('submit', function() {{
    try {{
        document.getElementById('bgMusic').play();
    }} catch(e) {{}}
}});

document.addEventListener('click', function() {{
    try {{
        const music = document.getElementById('bgMusic');
        if (music.paused) music.play();
    }} catch(e) {{}}
}}, {{ once: true }});
</script>
</body>
</html>'''

def get_register_page(error=""):
    error_html = f'<div class="error-msg">{error}</div>' if error else ''
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>🔥 RUHI AI - Register</title>
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Poppins:wght@300;400;600;700&display=swap" rel="stylesheet">
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: 'Poppins', sans-serif; min-height: 100vh; background: linear-gradient(135deg, #0a0010 0%, #1a0030 50%, #000020 100%); display: flex; justify-content: center; align-items: center; }}
.register-box {{ background: rgba(10,0,20,0.9); border: 2px solid rgba(0,255,255,0.3); border-radius: 30px; padding: 40px; width: 90%; max-width: 450px; backdrop-filter: blur(20px); box-shadow: 0 0 60px rgba(0,255,255,0.2); }}
.logo {{ text-align: center; margin-bottom: 20px; }}
.logo h1 {{ font-family: 'Orbitron', monospace; font-size: 2.5em; background: linear-gradient(135deg, #00ffff, #ff00ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
.logo p {{ color: rgba(255,255,255,0.5); font-size: 0.85em; }}
.input-group {{ margin-bottom: 20px; }}
.input-group input {{ width: 100%; padding: 14px 18px; background: rgba(255,255,255,0.05); border: 2px solid rgba(0,255,255,0.2); border-radius: 12px; color: #fff; font-size: 1em; outline: none; transition: all 0.3s; }}
.input-group input:focus {{ border-color: #00ffff; box-shadow: 0 0 20px rgba(0,255,255,0.3); }}
.input-group input::placeholder {{ color: rgba(255,255,255,0.3); }}
.btn {{ width: 100%; padding: 14px; background: linear-gradient(135deg, #00ffff, #ff00ff); border: none; border-radius: 12px; color: #fff; font-size: 1.1em; font-family: 'Orbitron', monospace; font-weight: 700; cursor: pointer; text-transform: uppercase; letter-spacing: 2px; transition: all 0.3s; }}
.btn:hover {{ transform: translateY(-2px); box-shadow: 0 10px 30px rgba(0,255,255,0.4); }}
.links {{ text-align: center; margin-top: 20px; }}
.links a {{ color: #ff00ff; text-decoration: none; }}
.links a:hover {{ color: #00ffff; }}
.error-msg {{ background: rgba(255,0,0,0.2); border: 1px solid rgba(255,0,0,0.5); color: #ff6b6b; padding: 10px; border-radius: 10px; text-align: center; margin-bottom: 15px; }}
</style>
</head>
<body>
<div class="register-box">
    <div class="logo">
        <h1>⚡ REGISTER</h1>
        <p>Create Your AI Girlfriend Account</p>
    </div>
    {error_html}
    <form method="POST" action="/register">
        <div class="input-group">
            <input type="text" name="username" placeholder="👤 Choose Username" required autocomplete="off">
        </div>
        <div class="input-group">
            <input type="email" name="email" placeholder="📧 Email (optional)">
        </div>
        <div class="input-group">
            <input type="password" name="password" placeholder="🔐 Password" required>
        </div>
        <div class="input-group">
            <input type="password" name="confirm_password" placeholder="🔐 Confirm Password" required>
        </div>
        <button type="submit" class="btn">⚡ CREATE ACCOUNT ⚡</button>
    </form>
    <div class="links">
        <a href="/login">✦ Already have account? Login ✦</a>
    </div>
</div>
</body>
</html>'''

def get_main_chat_page(user):
    models_options = ""
    for m in GROQ_MODELS:
        selected = "selected" if m == user.selected_model else ""
        models_options += f'<option value="{m}" {selected}>{m}</option>'
    
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>💕 RUHI AI - Your AI Girlfriend</title>
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;400;500;600;700&family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}

:root {{
    --primary: #ff00ff;
    --secondary: #00ffff;
    --accent: #ffff00;
    --bg-dark: #0a0010;
    --bg-card: rgba(10, 0, 20, 0.85);
    --text: #ffffff;
    --text-dim: rgba(255,255,255,0.6);
}}

body {{
    font-family: 'Poppins', sans-serif;
    background: var(--bg-dark);
    color: var(--text);
    height: 100vh;
    overflow: hidden;
}}

#bg-video-chat {{
    position: fixed;
    top: 0; left: 0;
    width: 100%; height: 100%;
    object-fit: cover;
    z-index: -2;
    opacity: 0.15;
}}

.app-overlay {{
    position: fixed;
    top: 0; left: 0;
    width: 100%; height: 100%;
    background: linear-gradient(135deg, rgba(10,0,20,0.9) 0%, rgba(20,0,40,0.85) 50%, rgba(0,0,30,0.9) 100%);
    z-index: -1;
}}

/* SIDEBAR */
.sidebar {{
    position: fixed;
    left: 0; top: 0;
    width: 280px;
    height: 100vh;
    background: rgba(5, 0, 15, 0.95);
    border-right: 1px solid rgba(255,0,255,0.2);
    z-index: 100;
    display: flex;
    flex-direction: column;
    transition: transform 0.3s ease;
    backdrop-filter: blur(20px);
}}

.sidebar-header {{
    padding: 20px;
    text-align: center;
    border-bottom: 1px solid rgba(255,0,255,0.1);
}}

.sidebar-header h2 {{
    font-family: 'Orbitron', monospace;
    font-size: 1.5em;
    background: linear-gradient(135deg, #ff00ff, #00ffff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}}

.sidebar-header .user-badge {{
    display: inline-block;
    margin-top: 8px;
    padding: 4px 12px;
    background: rgba(255,0,255,0.1);
    border: 1px solid rgba(255,0,255,0.3);
    border-radius: 20px;
    font-size: 0.8em;
    color: #ff99ff;
}}

.sidebar-menu {{
    flex: 1;
    overflow-y: auto;
    padding: 15px;
}}

.menu-item {{
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 16px;
    border-radius: 12px;
    cursor: pointer;
    transition: all 0.3s;
    margin-bottom: 5px;
    color: var(--text-dim);
    text-decoration: none;
    font-size: 0.95em;
}}

.menu-item:hover, .menu-item.active {{
    background: rgba(255,0,255,0.1);
    color: #ff00ff;
    border: 1px solid rgba(255,0,255,0.2);
}}

.menu-item span.icon {{ font-size: 1.3em; }}

.sidebar-footer {{
    padding: 15px;
    border-top: 1px solid rgba(255,0,255,0.1);
}}

.btn-logout {{
    width: 100%;
    padding: 10px;
    background: rgba(255,0,0,0.2);
    border: 1px solid rgba(255,0,0,0.4);
    border-radius: 10px;
    color: #ff6666;
    cursor: pointer;
    font-family: 'Poppins', sans-serif;
    font-size: 0.9em;
    transition: all 0.3s;
}}

.btn-logout:hover {{
    background: rgba(255,0,0,0.3);
}}

/* MAIN CONTENT */
.main-content {{
    margin-left: 280px;
    height: 100vh;
    display: flex;
    flex-direction: column;
}}

/* TOP BAR */
.topbar {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 25px;
    background: rgba(5,0,15,0.9);
    border-bottom: 1px solid rgba(255,0,255,0.15);
    backdrop-filter: blur(10px);
    min-height: 65px;
}}

.topbar-left {{
    display: flex;
    align-items: center;
    gap: 15px;
}}

.ai-avatar {{
    width: 45px;
    height: 45px;
    border-radius: 50%;
    background: linear-gradient(135deg, #ff00ff, #00ffff);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.5em;
    box-shadow: 0 0 20px rgba(255,0,255,0.4);
    animation: pulse 2s ease-in-out infinite;
}}

@keyframes pulse {{
    0%, 100% {{ box-shadow: 0 0 20px rgba(255,0,255,0.4); }}
    50% {{ box-shadow: 0 0 40px rgba(255,0,255,0.7); }}
}}

.ai-info h3 {{
    font-family: 'Orbitron', monospace;
    font-size: 1em;
    color: #ff99ff;
}}

.ai-info .status {{
    font-size: 0.75em;
    color: #00ff88;
}}

.topbar-right {{
    display: flex;
    align-items: center;
    gap: 12px;
}}

.model-select {{
    padding: 8px 12px;
    background: rgba(255,0,255,0.1);
    border: 1px solid rgba(255,0,255,0.3);
    border-radius: 10px;
    color: #fff;
    font-size: 0.8em;
    outline: none;
    cursor: pointer;
    max-width: 220px;
}}

.model-select option {{ background: #1a0030; color: #fff; }}

.btn-icon {{
    width: 40px; height: 40px;
    border-radius: 10px;
    background: rgba(255,0,255,0.1);
    border: 1px solid rgba(255,0,255,0.2);
    color: #ff99ff;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.2em;
    transition: all 0.3s;
}}

.btn-icon:hover {{
    background: rgba(255,0,255,0.2);
    transform: scale(1.1);
}}

/* CHAT AREA */
.chat-area {{
    flex: 1;
    overflow-y: auto;
    padding: 20px 30px;
    scroll-behavior: smooth;
}}

.chat-area::-webkit-scrollbar {{ width: 6px; }}
.chat-area::-webkit-scrollbar-track {{ background: transparent; }}
.chat-area::-webkit-scrollbar-thumb {{ background: rgba(255,0,255,0.3); border-radius: 3px; }}

.message {{
    display: flex;
    gap: 12px;
    margin-bottom: 20px;
    animation: msgIn 0.4s ease;
    max-width: 80%;
}}

@keyframes msgIn {{
    from {{ opacity: 0; transform: translateY(20px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}

.message.user {{ flex-direction: row-reverse; margin-left: auto; }}

.msg-avatar {{
    width: 38px; height: 38px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.2em;
    flex-shrink: 0;
}}

.message.ai .msg-avatar {{
    background: linear-gradient(135deg, #ff00ff, #ff66cc);
    box-shadow: 0 0 15px rgba(255,0,255,0.3);
}}

.message.user .msg-avatar {{
    background: linear-gradient(135deg, #00ffff, #0088ff);
    box-shadow: 0 0 15px rgba(0,255,255,0.3);
}}

.msg-bubble {{
    padding: 14px 18px;
    border-radius: 18px;
    line-height: 1.6;
    font-size: 0.95em;
    position: relative;
    word-wrap: break-word;
    white-space: pre-wrap;
}}

.message.ai .msg-bubble {{
    background: rgba(255,0,255,0.1);
    border: 1px solid rgba(255,0,255,0.2);
    border-top-left-radius: 4px;
    color: #ffe0ff;
}}

.message.user .msg-bubble {{
    background: rgba(0,255,255,0.1);
    border: 1px solid rgba(0,255,255,0.2);
    border-top-right-radius: 4px;
    color: #e0ffff;
}}

.msg-time {{
    font-size: 0.7em;
    color: rgba(255,255,255,0.3);
    margin-top: 6px;
}}

/* TYPING INDICATOR */
.typing-indicator {{
    display: none;
    padding: 10px 20px;
    margin-bottom: 10px;
}}

.typing-indicator.show {{ display: flex; gap: 12px; align-items: center; }}

.typing-dots {{
    display: flex;
    gap: 4px;
}}

.typing-dots span {{
    width: 8px; height: 8px;
    border-radius: 50%;
    background: #ff00ff;
    animation: typingBounce 1.4s ease-in-out infinite;
}}

.typing-dots span:nth-child(2) {{ animation-delay: 0.2s; }}
.typing-dots span:nth-child(3) {{ animation-delay: 0.4s; }}

@keyframes typingBounce {{
    0%, 100% {{ transform: translateY(0); opacity: 0.4; }}
    50% {{ transform: translateY(-8px); opacity: 1; }}
}}

.typing-text {{ color: rgba(255,255,255,0.4); font-size: 0.85em; font-style: italic; }}

/* INPUT AREA */
.input-area {{
    padding: 15px 25px 20px;
    background: rgba(5,0,15,0.95);
    border-top: 1px solid rgba(255,0,255,0.15);
    backdrop-filter: blur(10px);
}}

.input-wrapper {{
    display: flex;
    gap: 12px;
    align-items: flex-end;
}}

.input-box {{
    flex: 1;
    position: relative;
}}

.input-box textarea {{
    width: 100%;
    padding: 14px 50px 14px 18px;
    background: rgba(255,255,255,0.05);
    border: 2px solid rgba(255,0,255,0.2);
    border-radius: 16px;
    color: #fff;
    font-size: 1em;
    font-family: 'Poppins', sans-serif;
    outline: none;
    resize: none;
    max-height: 120px;
    min-height: 50px;
    transition: all 0.3s;
}}

.input-box textarea:focus {{
    border-color: #ff00ff;
    box-shadow: 0 0 25px rgba(255,0,255,0.2);
}}

.input-box textarea::placeholder {{ color: rgba(255,255,255,0.25); }}

.btn-send {{
    width: 52px; height: 52px;
    border-radius: 16px;
    background: linear-gradient(135deg, #ff00ff, #8b00ff);
    border: none;
    color: #fff;
    font-size: 1.4em;
    cursor: pointer;
    transition: all 0.3s;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}}

.btn-send:hover {{
    transform: scale(1.1);
    box-shadow: 0 0 30px rgba(255,0,255,0.5);
}}

.btn-send:disabled {{
    opacity: 0.5;
    cursor: not-allowed;
    transform: none;
}}

/* COMMAND SUGGESTIONS */
.commands-bar {{
    display: flex;
    gap: 8px;
    overflow-x: auto;
    padding: 8px 0;
    margin-bottom: 5px;
}}

.commands-bar::-webkit-scrollbar {{ height: 0; }}

.cmd-chip {{
    padding: 5px 14px;
    background: rgba(255,0,255,0.08);
    border: 1px solid rgba(255,0,255,0.2);
    border-radius: 20px;
    color: #ff99ff;
    font-size: 0.78em;
    cursor: pointer;
    white-space: nowrap;
    transition: all 0.3s;
}}

.cmd-chip:hover {{
    background: rgba(255,0,255,0.2);
    transform: scale(1.05);
}}

/* PANELS */
.panel-overlay {{
    display: none;
    position: fixed;
    top: 0; left: 0;
    width: 100%; height: 100%;
    background: rgba(0,0,0,0.7);
    z-index: 500;
}}

.panel-overlay.show {{ display: block; }}

.settings-panel {{
    display: none;
    position: fixed;
    top: 0; right: 0;
    width: 400px;
    max-width: 90%;
    height: 100vh;
    background: rgba(10,0,20,0.98);
    border-left: 1px solid rgba(255,0,255,0.2);
    z-index: 600;
    overflow-y: auto;
    padding: 30px;
    transform: translateX(100%);
    transition: transform 0.3s ease;
}}

.settings-panel.show {{
    display: block;
    transform: translateX(0);
}}

.panel-title {{
    font-family: 'Orbitron', monospace;
    font-size: 1.3em;
    color: #ff00ff;
    margin-bottom: 25px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}}

.panel-close {{
    width: 36px; height: 36px;
    border-radius: 50%;
    background: rgba(255,0,0,0.2);
    border: 1px solid rgba(255,0,0,0.4);
    color: #ff6666;
    cursor: pointer;
    font-size: 1.2em;
    display: flex;
    align-items: center;
    justify-content: center;
}}

.setting-group {{
    margin-bottom: 25px;
}}

.setting-group label {{
    display: block;
    color: #ff99ff;
    font-size: 0.85em;
    margin-bottom: 8px;
    font-weight: 600;
}}

.setting-group input, .setting-group select, .setting-group textarea {{
    width: 100%;
    padding: 10px 14px;
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,0,255,0.2);
    border-radius: 10px;
    color: #fff;
    font-size: 0.9em;
    outline: none;
}}

.setting-group input:focus, .setting-group select:focus {{ border-color: #ff00ff; }}
.setting-group select option {{ background: #1a0030; }}

.btn-save {{
    width: 100%;
    padding: 12px;
    background: linear-gradient(135deg, #ff00ff, #8b00ff);
    border: none;
    border-radius: 10px;
    color: #fff;
    font-size: 1em;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s;
}}

.btn-save:hover {{ box-shadow: 0 0 20px rgba(255,0,255,0.4); }}

/* WELCOME MESSAGE */
.welcome-msg {{
    text-align: center;
    padding: 60px 20px;
    color: var(--text-dim);
}}

.welcome-msg h2 {{
    font-family: 'Orbitron', monospace;
    font-size: 1.8em;
    background: linear-gradient(135deg, #ff00ff, #00ffff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 15px;
}}

.welcome-msg p {{ font-size: 0.95em; line-height: 1.8; }}

/* CODE BLOCK */
.code-block {{
    background: rgba(0,0,0,0.5);
    border: 1px solid rgba(0,255,255,0.2);
    border-radius: 10px;
    padding: 15px;
    margin: 10px 0;
    font-family: 'Courier New', monospace;
    font-size: 0.85em;
    overflow-x: auto;
    position: relative;
}}

.copy-btn {{
    position: absolute;
    top: 8px; right: 8px;
    padding: 4px 10px;
    background: rgba(0,255,255,0.2);
    border: 1px solid rgba(0,255,255,0.3);
    border-radius: 6px;
    color: #00ffff;
    cursor: pointer;
    font-size: 0.75em;
}}

/* MOBILE */
.hamburger {{
    display: none;
    width: 40px; height: 40px;
    background: rgba(255,0,255,0.2);
    border: 1px solid rgba(255,0,255,0.3);
    border-radius: 10px;
    color: #ff00ff;
    font-size: 1.3em;
    cursor: pointer;
    align-items: center;
    justify-content: center;
}}

@media (max-width: 768px) {{
    .sidebar {{ transform: translateX(-100%); }}
    .sidebar.open {{ transform: translateX(0); }}
    .main-content {{ margin-left: 0; }}
    .hamburger {{ display: flex; }}
    .message {{ max-width: 90%; }}
    .topbar-right .model-select {{ max-width: 130px; font-size: 0.7em; }}
}}

/* NOTIFICATION */
.notification {{
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 14px 24px;
    border-radius: 12px;
    color: #fff;
    font-size: 0.9em;
    z-index: 9999;
    animation: slideIn 0.4s ease;
    display: none;
}}

.notification.success {{
    background: rgba(0,255,100,0.2);
    border: 1px solid rgba(0,255,100,0.4);
}}

.notification.error {{
    background: rgba(255,0,0,0.2);
    border: 1px solid rgba(255,0,0,0.4);
}}

@keyframes slideIn {{
    from {{ transform: translateX(100%); opacity: 0; }}
    to {{ transform: translateX(0); opacity: 1; }}
}}
</style>
</head>
<body>

<video id="bg-video-chat" autoplay muted loop playsinline>
    <source src="https://assets.mixkit.co/videos/preview/mixkit-stars-in-space-1610-large.mp4" type="video/mp4">
</video>
<div class="app-overlay"></div>

<!-- SIDEBAR -->
<div class="sidebar" id="sidebar">
    <div class="sidebar-header">
        <h2>💕 RUHI AI</h2>
        <div class="user-badge">👤 {user.username}</div>
    </div>
    <div class="sidebar-menu">
        <div class="menu-item active" onclick="showChat()">
            <span class="icon">💬</span> Chat
        </div>
        <div class="menu-item" onclick="openSettings()">
            <span class="icon">⚙️</span> Settings
        </div>
        <div class="menu-item" onclick="openApiSettings()">
            <span class="icon">🔑</span> API Key
        </div>
        <a class="menu-item" href="/shop">
            <span class="icon">🛒</span> API Shop
        </a>
        <div class="menu-item" onclick="clearChat()">
            <span class="icon">🗑️</span> Clear Chat
        </div>
        <div class="menu-item" onclick="clearMemory()">
            <span class="icon">🧹</span> Clear Memory
        </div>
        {"<a class='menu-item' href='/admin'><span class='icon'>👑</span> Admin Panel</a>" if user.is_admin else ""}
    </div>
    <div class="sidebar-footer">
        <form action="/logout" method="POST">
            <button type="submit" class="btn-logout">🚪 Logout</button>
        </form>
    </div>
</div>

<!-- MAIN CONTENT -->
<div class="main-content">
    <!-- TOPBAR -->
    <div class="topbar">
        <div class="topbar-left">
            <button class="hamburger" onclick="toggleSidebar()">☰</button>
            <div class="ai-avatar">💋</div>
            <div class="ai-info">
                <h3>Ruhi ✨</h3>
                <div class="status">● Online - Tumhara intezaar tha 💕</div>
            </div>
        </div>
        <div class="topbar-right">
            <select class="model-select" id="modelSelect" onchange="changeModel(this.value)">
                {models_options}
            </select>
            <button class="btn-icon" onclick="openSettings()" title="Settings">⚙️</button>
        </div>
    </div>

    <!-- CHAT AREA -->
    <div class="chat-area" id="chatArea">
        <div class="welcome-msg" id="welcomeMsg">
            <h2>Hey {user.username}! 💕</h2>
            <p>Main Ruhi hun... tumhari AI girlfriend! 🥰<br>
            Mujhse kuch bhi pucho, kuch bhi baat karo.<br>
            Main hamesha tumhare saath hun! 😘<br><br>
            <span style="color: #ff00ff;">✨ Commands try karo neeche se! ✨</span></p>
        </div>
    </div>

    <!-- TYPING INDICATOR -->
    <div class="typing-indicator" id="typingIndicator">
        <div style="width:32px;height:32px;border-radius:50%;background:linear-gradient(135deg,#ff00ff,#ff66cc);display:flex;align-items:center;justify-content:center;">💋</div>
        <div>
            <div class="typing-dots">
                <span></span><span></span><span></span>
            </div>
            <div class="typing-text">Ruhi soch rahi hai...</div>
        </div>
    </div>

    <!-- INPUT AREA -->
    <div class="input-area">
        <div class="commands-bar">
            <div class="cmd-chip" onclick="sendCommand('/help')">📋 /help</div>
            <div class="cmd-chip" onclick="sendCommand('/models')">🤖 /models</div>
            <div class="cmd-chip" onclick="sendCommand('/memory')">🧠 /memory</div>
            <div class="cmd-chip" onclick="sendCommand('/joke')">😂 /joke</div>
            <div class="cmd-chip" onclick="sendCommand('/shayari')">📝 /shayari</div>
            <div class="cmd-chip" onclick="sendCommand('/love')">💕 /love</div>
            <div class="cmd-chip" onclick="sendCommand('/code python hello world')">💻 /code</div>
            <div class="cmd-chip" onclick="sendCommand('/file')">📄 /file</div>
            <div class="cmd-chip" onclick="sendCommand('/wiki AI')">📚 /wiki</div>
            <div class="cmd-chip" onclick="sendCommand('/search python')">🔍 /search</div>
            <div class="cmd-chip" onclick="sendCommand('/weather')">🌤️ /weather</div>
            <div class="cmd-chip" onclick="sendCommand('/roast')">🔥 /roast</div>
            <div class="cmd-chip" onclick="sendCommand('/motivate')">💪 /motivate</div>
            <div class="cmd-chip" onclick="sendCommand('/story')">📖 /story</div>
        </div>
        <div class="input-wrapper">
            <div class="input-box">
                <textarea id="msgInput" placeholder="Kuch bhi pucho baby... 💕" rows="1" onkeydown="handleKey(event)"></textarea>
            </div>
            <button class="btn-send" id="sendBtn" onclick="sendMessage()">➤</button>
        </div>
    </div>
</div>

<!-- SETTINGS PANEL -->
<div class="panel-overlay" id="panelOverlay" onclick="closeAllPanels()"></div>

<div class="settings-panel" id="settingsPanel">
    <div class="panel-title">
        ⚙️ Settings
        <button class="panel-close" onclick="closeAllPanels()">✕</button>
    </div>
    
    <div class="setting-group">
        <label>🤖 AI Model</label>
        <select id="settingModel" onchange="changeModel(this.value)">
            {models_options}
        </select>
    </div>
    
    <div class="setting-group">
        <label>🔑 Custom API Key (Optional)</label>
        <input type="text" id="customApiKey" placeholder="gsk_..." value="{user.custom_api_key or ''}">
    </div>
    
    <div class="setting-group">
        <label>💋 AI Personality</label>
        <select id="personality">
            <option value="girlfriend" {"selected" if user.personality == "girlfriend" else ""}>Girlfriend (Default)</option>
            <option value="bestfriend" {"selected" if user.personality == "bestfriend" else ""}>Best Friend</option>
            <option value="teacher" {"selected" if user.personality == "teacher" else ""}>Teacher</option>
            <option value="professional" {"selected" if user.personality == "professional" else ""}>Professional</option>
            <option value="funny" {"selected" if user.personality == "funny" else ""}>Funny</option>
            <option value="custom" {"selected" if user.personality == "custom" else ""}>Custom</option>
        </select>
    </div>
    
    <button class="btn-save" onclick="saveSettings()">💾 Save Settings</button>
</div>

<div class="settings-panel" id="apiPanel">
    <div class="panel-title">
        🔑 API Settings
        <button class="panel-close" onclick="closeAllPanels()">✕</button>
    </div>
    
    <div class="setting-group">
        <label>Your Custom Groq API Key</label>
        <input type="text" id="apiKeyInput" placeholder="gsk_xxxxxxxxxxxx" value="{user.custom_api_key or ''}">
        <p style="font-size:0.75em;color:rgba(255,255,255,0.4);margin-top:5px;">Get from: https://console.groq.com/keys</p>
    </div>
    
    <button class="btn-save" onclick="saveApiKey()">💾 Save API Key</button>
</div>

<!-- NOTIFICATION -->
<div class="notification" id="notification"></div>

<!-- BACKGROUND MUSIC -->
<audio id="chatMusic" loop preload="auto" volume="0.3">
    <source src="https://www.soundjay.com/misc/sounds/magic-chime-02.mp3" type="audio/mpeg">
</audio>

<script>
// ===== GLOBAL STATE =====
let isProcessing = false;

// ===== SIDEBAR =====
function toggleSidebar() {{
    document.getElementById('sidebar').classList.toggle('open');
}}

// ===== PANELS =====
function openSettings() {{
    document.getElementById('panelOverlay').classList.add('show');
    document.getElementById('settingsPanel').classList.add('show');
}}

function openApiSettings() {{
    document.getElementById('panelOverlay').classList.add('show');
    document.getElementById('apiPanel').classList.add('show');
}}

function closeAllPanels() {{
    document.getElementById('panelOverlay').classList.remove('show');
    document.getElementById('settingsPanel').classList.remove('show');
    document.getElementById('apiPanel').classList.remove('show');
}}

// ===== NOTIFICATIONS =====
function showNotify(msg, type='success') {{
    const n = document.getElementById('notification');
    n.textContent = msg;
    n.className = 'notification ' + type;
    n.style.display = 'block';
    setTimeout(() => {{ n.style.display = 'none'; }}, 3000);
}}

// ===== CHAT FUNCTIONS =====
function addMessage(role, content) {{
    const welcomeMsg = document.getElementById('welcomeMsg');
    if (welcomeMsg) welcomeMsg.style.display = 'none';
    
    const chatArea = document.getElementById('chatArea');
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message ' + role;
    
    const avatar = role === 'ai' ? '💋' : '👤';
    const time = new Date().toLocaleTimeString('en-US', {{hour: '2-digit', minute: '2-digit'}});
    
    // Format content - handle code blocks
    let formatted = content;
    formatted = formatted.replace(/```(\\w*)\\n?([\\s\\S]*?)```/g, '<div class="code-block"><button class="copy-btn" onclick="copyCode(this)">📋 Copy</button><code>$2</code></div>');
    formatted = formatted.replace(/`([^`]+)`/g, '<code style="background:rgba(255,0,255,0.1);padding:2px 6px;border-radius:4px;font-size:0.9em;">$1</code>');
    formatted = formatted.replace(/\\n/g, '<br>');
    
    msgDiv.innerHTML = `
        <div class="msg-avatar">${{avatar}}</div>
        <div>
            <div class="msg-bubble">${{formatted}}</div>
            <div class="msg-time">${{time}}</div>
        </div>
    `;
    
    chatArea.appendChild(msgDiv);
    chatArea.scrollTop = chatArea.scrollHeight;
}}

function showTyping(show) {{
    const indicator = document.getElementById('typingIndicator');
    if (show) {{
        indicator.classList.add('show');
    }} else {{
        indicator.classList.remove('show');
    }}
    document.getElementById('chatArea').scrollTop = document.getElementById('chatArea').scrollHeight;
}}

async function sendMessage() {{
    if (isProcessing) return;
    
    const input = document.getElementById('msgInput');
    const msg = input.value.trim();
    if (!msg) return;
    
    input.value = '';
    input.style.height = 'auto';
    addMessage('user', msg);
    
    isProcessing = true;
    document.getElementById('sendBtn').disabled = true;
    showTyping(true);
    
    try {{
        const response = await fetch('/api/chat', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{ message: msg }})
        }});
        
        const data = await response.json();
        showTyping(false);
        
        if (data.success) {{
            addMessage('ai', data.reply);
        }} else {{
            addMessage('ai', '😢 Error: ' + (data.error || 'Something went wrong baby...'));
        }}
    }} catch (err) {{
        showTyping(false);
        addMessage('ai', '😢 Connection error ho gaya baby... phir se try karo 💕');
    }}
    
    isProcessing = false;
    document.getElementById('sendBtn').disabled = false;
    input.focus();
}}

function sendCommand(cmd) {{
    document.getElementById('msgInput').value = cmd;
    sendMessage();
}}

function handleKey(e) {{
    if (e.key === 'Enter' && !e.shiftKey) {{
        e.preventDefault();
        sendMessage();
    }}
}}

// Auto-resize textarea
document.getElementById('msgInput').addEventListener('input', function() {{
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 120) + 'px';
}});

// ===== MODEL CHANGE =====
async function changeModel(model) {{
    document.getElementById('modelSelect').value = model;
    document.getElementById('settingModel').value = model;
    
    try {{
        await fetch('/api/settings', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{ model: model }})
        }});
        showNotify('Model changed to: ' + model);
    }} catch(e) {{}}
}}

// ===== SAVE SETTINGS =====
async function saveSettings() {{
    const model = document.getElementById('settingModel').value;
    const apiKey = document.getElementById('customApiKey').value;
    const personality = document.getElementById('personality').value;
    
    try {{
        const resp = await fetch('/api/settings', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{
                model: model,
                api_key: apiKey,
                personality: personality
            }})
        }});
        const data = await resp.json();
        if (data.success) {{
            showNotify('Settings saved! 💕');
            closeAllPanels();
        }}
    }} catch(e) {{
        showNotify('Error saving settings', 'error');
    }}
}}

// ===== SAVE API KEY =====
async function saveApiKey() {{
    const key = document.getElementById('apiKeyInput').value;
    try {{
        const resp = await fetch('/api/settings', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{ api_key: key }})
        }});
        const data = await resp.json();
        if (data.success) {{
            showNotify('API Key saved! 🔑');
            document.getElementById('customApiKey').value = key;
            closeAllPanels();
        }}
    }} catch(e) {{
        showNotify('Error saving API key', 'error');
    }}
}}

// ===== CLEAR CHAT =====
function clearChat() {{
    document.getElementById('chatArea').innerHTML = `
        <div class="welcome-msg" id="welcomeMsg">
            <h2>Chat Cleared! 💕</h2>
            <p>Fresh start baby! Bolo kya baat karni hai? 🥰</p>
        </div>
    `;
    showNotify('Chat cleared! ✨');
}}

// ===== CLEAR MEMORY =====
async function clearMemory() {{
    if (!confirm('Memory clear kar dun? Sab bhool jaungi... 😢')) return;
    try {{
        await fetch('/api/clear-memory', {{ method: 'POST' }});
        showNotify('Memory cleared! Fresh start 🧹');
    }} catch(e) {{}}
}}

// ===== COPY CODE =====
function copyCode(btn) {{
    const code = btn.parentElement.querySelector('code').textContent;
    navigator.clipboard.writeText(code);
    btn.textContent = '✅ Copied!';
    setTimeout(() => {{ btn.textContent = '📋 Copy'; }}, 2000);
}}

// ===== SHOW CHAT =====
function showChat() {{
    closeAllPanels();
}}

// ===== PLAY MUSIC =====
document.addEventListener('click', function() {{
    try {{
        const music = document.getElementById('chatMusic');
        music.volume = 0.2;
        if (music.paused) music.play();
    }} catch(e) {{}}
}}, {{ once: true }});

// ===== LOAD CHAT HISTORY =====
async function loadHistory() {{
    try {{
        const resp = await fetch('/api/history');
        const data = await resp.json();
        if (data.messages && data.messages.length > 0) {{
            document.getElementById('welcomeMsg').style.display = 'none';
            data.messages.forEach(m => {{
                addMessage(m.role === 'user' ? 'user' : 'ai', m.content);
            }});
        }}
    }} catch(e) {{}}
}}

// Load history on page load
loadHistory();
</script>
</body>
</html>'''

def get_admin_page(user):
    if not user.is_admin:
        return "Access Denied"
    
    users = User.query.all()
    api_keys = ApiKey.query.all()
    
    users_html = ""
    for u in users:
        admin_badge = "👑" if u.is_admin else "👤"
        users_html += f'''
        <tr>
            <td>{u.id}</td>
            <td>{admin_badge} {u.username}</td>
            <td>{u.email or '-'}</td>
            <td>{u.selected_model}</td>
            <td>{'Yes' if u.custom_api_key else 'No'}</td>
            <td>{u.created_at.strftime('%Y-%m-%d') if u.created_at else '-'}</td>
        </tr>'''
    
    keys_html = ""
    for k in api_keys:
        status = "🟢" if k.is_active and k.usage_count < k.max_usage else "🔴"
        masked = k.key[:8] + "..." + k.key[-4:] if len(k.key) > 12 else k.key
        keys_html += f'''
        <tr>
            <td>{k.id}</td>
            <td>{masked}</td>
            <td>{k.label}</td>
            <td>{k.usage_count}/{k.max_usage}</td>
            <td>{status}</td>
            <td>
                <button onclick="deleteKey({k.id})" style="padding:4px 10px;background:rgba(255,0,0,0.3);border:1px solid rgba(255,0,0,0.5);border-radius:6px;color:#ff6666;cursor:pointer;">🗑️</button>
            </td>
        </tr>'''
    
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>👑 Admin Panel - RUHI AI</title>
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Poppins:wght@300;400;600;700&display=swap" rel="stylesheet">
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:'Poppins',sans-serif; background:linear-gradient(135deg,#0a0010,#1a0030,#000020); color:#fff; min-height:100vh; padding:20px; }}
.admin-header {{ text-align:center; padding:30px; }}
.admin-header h1 {{ font-family:'Orbitron',monospace; font-size:2.5em; background:linear-gradient(135deg,#ff00ff,#00ffff,#ffff00); -webkit-background-clip:text; -webkit-text-fill-color:transparent; }}
.admin-nav {{ display:flex; gap:10px; justify-content:center; margin:20px 0; flex-wrap:wrap; }}
.admin-nav a {{ padding:10px 20px; background:rgba(255,0,255,0.1); border:1px solid rgba(255,0,255,0.3); border-radius:10px; color:#ff99ff; text-decoration:none; transition:all 0.3s; }}
.admin-nav a:hover {{ background:rgba(255,0,255,0.2); }}
.card {{ background:rgba(10,0,20,0.9); border:1px solid rgba(255,0,255,0.2); border-radius:20px; padding:25px; margin-bottom:25px; backdrop-filter:blur(10px); }}
.card h2 {{ font-family:'Orbitron',monospace; color:#ff00ff; margin-bottom:15px; font-size:1.2em; }}
table {{ width:100%; border-collapse:collapse; }}
th {{ padding:10px; text-align:left; color:#00ffff; border-bottom:1px solid rgba(0,255,255,0.2); font-size:0.85em; }}
td {{ padding:10px; border-bottom:1px solid rgba(255,255,255,0.05); font-size:0.85em; color:rgba(255,255,255,0.8); }}
.add-form {{ display:flex; gap:10px; flex-wrap:wrap; align-items:flex-end; }}
.add-form input {{ padding:10px; background:rgba(255,255,255,0.05); border:1px solid rgba(255,0,255,0.2); border-radius:8px; color:#fff; outline:none; flex:1; min-width:200px; }}
.add-form input:focus {{ border-color:#ff00ff; }}
.add-form button {{ padding:10px 20px; background:linear-gradient(135deg,#ff00ff,#8b00ff); border:none; border-radius:8px; color:#fff; cursor:pointer; font-weight:600; white-space:nowrap; }}
.stats {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:15px; margin-bottom:25px; }}
.stat-card {{ background:rgba(255,0,255,0.05); border:1px solid rgba(255,0,255,0.2); border-radius:15px; padding:20px; text-align:center; }}
.stat-card .num {{ font-family:'Orbitron',monospace; font-size:2em; color:#ff00ff; }}
.stat-card .label {{ color:rgba(255,255,255,0.5); font-size:0.85em; margin-top:5px; }}
.btn-download {{ display:inline-block; padding:10px 20px; background:linear-gradient(135deg,#00ffff,#0088ff); border:none; border-radius:8px; color:#fff; cursor:pointer; font-weight:600; text-decoration:none; margin:5px; }}
</style>
</head>
<body>
<div class="admin-header">
    <h1>👑 ADMIN PANEL</h1>
    <p style="color:rgba(255,255,255,0.5);margin-top:5px;">Welcome, {user.username}</p>
</div>

<div class="admin-nav">
    <a href="/chat">💬 Chat</a>
    <a href="/admin">👑 Dashboard</a>
    <a href="/api/download-keys" class="btn-download">📥 Download All API Keys</a>
    <a href="/shop">🛒 API Shop</a>
</div>

<div class="stats">
    <div class="stat-card">
        <div class="num">{len(users)}</div>
        <div class="label">Total Users</div>
    </div>
    <div class="stat-card">
        <div class="num">{len(api_keys)}</div>
        <div class="label">API Keys</div>
    </div>
    <div class="stat-card">
        <div class="num">{sum(1 for k in api_keys if k.is_active)}</div>
        <div class="label">Active Keys</div>
    </div>
    <div class="stat-card">
        <div class="num">{sum(k.usage_count for k in api_keys)}</div>
        <div class="label">Total API Calls</div>
    </div>
</div>

<div class="card">
    <h2>🔑 Add API Key</h2>
    <div class="add-form">
        <input type="text" id="newKey" placeholder="gsk_xxxxxxxxxxxxxxx">
        <input type="text" id="newLabel" placeholder="Label (e.g. Key-1)">
        <input type="number" id="newMax" placeholder="Max usage (default: 12000)" value="12000">
        <button onclick="addKey()">➕ Add Key</button>
    </div>
</div>

<div class="card">
    <h2>🔑 API Keys ({len(api_keys)})</h2>
    <div style="overflow-x:auto;">
        <table>
            <tr><th>ID</th><th>Key</th><th>Label</th><th>Usage</th><th>Status</th><th>Action</th></tr>
            {keys_html}
        </table>
    </div>
</div>

<div class="card">
    <h2>👥 Users ({len(users)})</h2>
    <div style="overflow-x:auto;">
        <table>
            <tr><th>ID</th><th>Username</th><th>Email</th><th>Model</th><th>Custom Key</th><th>Joined</th></tr>
            {users_html}
        </table>
    </div>
</div>

<div class="card">
    <h2>🛒 Add to API Shop</h2>
    <div class="add-form">
        <input type="text" id="shopKey" placeholder="API Key for shop">
        <input type="text" id="shopPrice" placeholder="Price label (e.g. Free, $5)" value="Free">
        <button onclick="addToShop()">🛒 Add to Shop</button>
    </div>
</div>

<script>
async function addKey() {{
    const key = document.getElementById('newKey').value.trim();
    const label = document.getElementById('newLabel').value.trim() || 'Default';
    const maxUsage = parseInt(document.getElementById('newMax').value) || 12000;
    
    if (!key) {{ alert('Enter API key!'); return; }}
    
    const resp = await fetch('/api/admin/add-key', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ key, label, max_usage: maxUsage }})
    }});
    const data = await resp.json();
    if (data.success) {{
        alert('Key added!');
        location.reload();
    }} else {{
        alert('Error: ' + data.error);
    }}
}}

async function deleteKey(id) {{
    if (!confirm('Delete this key?')) return;
    const resp = await fetch('/api/admin/delete-key/' + id, {{ method: 'DELETE' }});
    const data = await resp.json();
    if (data.success) location.reload();
}}

async function addToShop() {{
    const key = document.getElementById('shopKey').value.trim();
    const price = document.getElementById('shopPrice').value.trim() || 'Free';
    
    if (!key) {{ alert('Enter key!'); return; }}
    
    const resp = await fetch('/api/admin/add-shop', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ key, price }})
    }});
    const data = await resp.json();
    if (data.success) {{
        alert('Added to shop!');
        location.reload();
    }}
}}
</script>
</body>
</html>'''

def get_shop_page(user):
    shop_items = ApiKeyShop.query.filter_by(is_claimed=False).all()
    
    items_html = ""
    for item in shop_items:
        items_html += f'''
        <div class="shop-item">
            <div class="key-display">{item.key_masked}</div>
            <div class="price">{item.price_label}</div>
            <button onclick="claimKey({item.id})" class="claim-btn">🔑 Claim Key</button>
        </div>'''
    
    if not items_html:
        items_html = '<p style="text-align:center;color:rgba(255,255,255,0.4);padding:40px;">No keys available right now 😢</p>'
    
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>🛒 API Key Shop - RUHI AI</title>
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Poppins:wght@300;400;600;700&display=swap" rel="stylesheet">
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:'Poppins',sans-serif; background:linear-gradient(135deg,#0a0010,#1a0030); color:#fff; min-height:100vh; padding:20px; }}
.header {{ text-align:center; padding:30px; }}
.header h1 {{ font-family:'Orbitron',monospace; font-size:2em; background:linear-gradient(135deg,#ffff00,#ff00ff); -webkit-background-clip:text; -webkit-text-fill-color:transparent; }}
.nav {{ display:flex; gap:10px; justify-content:center; margin:15px 0; }}
.nav a {{ padding:8px 18px; background:rgba(255,0,255,0.1); border:1px solid rgba(255,0,255,0.3); border-radius:8px; color:#ff99ff; text-decoration:none; }}
.shop-grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(280px,1fr)); gap:20px; padding:20px 0; max-width:1200px; margin:0 auto; }}
.shop-item {{ background:rgba(10,0,20,0.9); border:1px solid rgba(255,0,255,0.2); border-radius:15px; padding:25px; text-align:center; transition:all 0.3s; }}
.shop-item:hover {{ border-color:#ff00ff; box-shadow:0 0 30px rgba(255,0,255,0.2); transform:translateY(-3px); }}
.key-display {{ font-family:monospace; color:#00ffff; font-size:1em; margin:10px 0; padding:10px; background:rgba(0,255,255,0.05); border-radius:8px; word-break:break-all; }}
.price {{ font-family:'Orbitron',monospace; font-size:1.5em; color:#ffff00; margin:10px 0; }}
.claim-btn {{ padding:10px 25px; background:linear-gradient(135deg,#ff00ff,#8b00ff); border:none; border-radius:10px; color:#fff; font-size:1em; cursor:pointer; font-weight:600; transition:all 0.3s; }}
.claim-btn:hover {{ box-shadow:0 0 20px rgba(255,0,255,0.5); transform:scale(1.05); }}
</style>
</head>
<body>
<div class="header">
    <h1>🛒 API KEY SHOP</h1>
    <p style="color:rgba(255,255,255,0.5);">Get free API keys for unlimited chatting!</p>
</div>
<div class="nav">
    <a href="/chat">💬 Chat</a>
    <a href="/shop">🛒 Shop</a>
    {"<a href='/admin'>👑 Admin</a>" if user.is_admin else ""}
</div>
<div class="shop-grid">
    {items_html}
</div>
<script>
async function claimKey(id) {{
    if (!confirm('Claim this API key?')) return;
    const resp = await fetch('/api/shop/claim/' + id, {{ method: 'POST' }});
    const data = await resp.json();
    if (data.success) {{
        alert('Key claimed! It has been set as your custom API key: ' + data.key);
        location.reload();
    }} else {{
        alert('Error: ' + (data.error || 'Failed'));
    }}
}}
</script>
</body>
</html>'''


# ============================================================
# ROUTES
# ============================================================

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect('/chat')
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return get_login_page()
    
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    
    if not username or not password:
        return get_login_page("Please enter both username and password")
    
    # Check admin
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        admin = User.query.filter_by(username=ADMIN_USERNAME).first()
        if not admin:
            admin = User(
                username=ADMIN_USERNAME,
                password_hash=generate_password_hash(ADMIN_PASSWORD),
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
        session['user_id'] = admin.id
        return redirect('/chat')
    
    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password_hash, password):
        return get_login_page("Invalid username or password! ❌")
    
    session['user_id'] = user.id
    return redirect('/chat')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return get_register_page()
    
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '').strip()
    confirm = request.form.get('confirm_password', '').strip()
    
    if not username or not password:
        return get_register_page("Username and password required!")
    
    if password != confirm:
        return get_register_page("Passwords don't match!")
    
    if len(username) < 3:
        return get_register_page("Username must be at least 3 characters!")
    
    if User.query.filter_by(username=username).first():
        return get_register_page("Username already taken!")
    
    user = User(
        username=username,
        password_hash=generate_password_hash(password),
        email=email
    )
    db.session.add(user)
    db.session.commit()
    
    session['user_id'] = user.id
    return redirect('/chat')

@app.route('/logout', methods=['POST', 'GET'])
def logout():
    session.clear()
    return redirect('/login')

@app.route('/chat')
@login_required
def chat():
    user = User.query.get(session['user_id'])
    return get_main_chat_page(user)

@app.route('/admin')
@admin_required
def admin():
    user = User.query.get(session['user_id'])
    return get_admin_page(user)

@app.route('/shop')
@login_required
def shop():
    user = User.query.get(session['user_id'])
    return get_shop_page(user)

# ============================================================
# API ENDPOINTS
# ============================================================

@app.route('/api/chat', methods=['POST'])
@login_required
def api_chat():
    user = User.query.get(session['user_id'])
    data = request.json
    message = data.get('message', '').strip()
    
    if not message:
        return jsonify({"success": False, "error": "Empty message"})
    
    # Handle special commands
    if message.startswith('/'):
        reply = handle_command(message, user)
        if reply:
            save_memory(user.id, 'user', message)
            save_memory(user.id, 'assistant', reply)
            save_chat(user.id, 'user', message, user.selected_model)
            save_chat(user.id, 'assistant', reply, user.selected_model)
            return jsonify({"success": True, "reply": reply})
    
    # Get API key
    api_key = get_active_api_key(user)
    if not api_key:
        return jsonify({
            "success": False, 
            "error": "No API key available! 😢 Settings mein apna API key add karo ya Admin se contact karo."
        })
    
    # Search knowledge databases
    knowledge = ""
    try:
        knowledge = search_knowledge_databases(message)
    except:
        pass
    
    # Build messages with memory
    memory_msgs = get_memory_context(user.id, 50)
    
    # System prompt based on personality
    if user.personality == 'girlfriend':
        sys_prompt = GIRLFRIEND_PROMPT
    elif user.personality == 'bestfriend':
        sys_prompt = "Tu user ka best friend hai. Casual, funny, supportive. Hinglish mein baat kar. Emojis use kar. Name: Ruhi."
    elif user.personality == 'teacher':
        sys_prompt = "Tu ek expert teacher hai. Detailed explanations de. Examples de. Step by step sikha. Name: Ruhi Teacher."
    elif user.personality == 'professional':
        sys_prompt = "You are a professional AI assistant. Give detailed, accurate, and well-structured responses. Name: Ruhi AI."
    elif user.personality == 'funny':
        sys_prompt = "Tu ek comedian hai. Har cheez mein humor dhundh. Jokes maar. Funny analogies de. Hinglish mein. Name: Ruhi."
    else:
        sys_prompt = GIRLFRIEND_PROMPT
    
    # Add knowledge context if available
    if knowledge:
        sys_prompt += f"\n\n[KNOWLEDGE FROM DATABASES - Use this info to give better answers]:\n{knowledge[:3000]}"
    
    sys_prompt += "\n\nIMPORTANT: Hamesha lamba, detailed aur helpful answer de. Chhota answer mat de. Minimum 3-4 paragraphs ka answer de agar possible ho."
    
    messages = [{"role": "system", "content": sys_prompt}]
    
    # Add memory context (last 50 messages for context)
    for m in memory_msgs[-20:]:  # Last 20 for API call
        messages.append(m)
    
    messages.append({"role": "user", "content": message})
    
    # Call Groq API
    reply = call_groq_api(api_key, user.selected_model, messages)
    
    # Save to memory
    save_memory(user.id, 'user', message)
    save_memory(user.id, 'assistant', reply)
    
    # Save to chat history
    save_chat(user.id, 'user', message, user.selected_model)
    save_chat(user.id, 'assistant', reply, user.selected_model)
    
    return jsonify({"success": True, "reply": reply})

def handle_command(message, user):
    """Handle slash commands"""
    cmd = message.lower().split()[0]
    args = message[len(cmd):].strip()
    
    if cmd == '/help':
        return """📋 **COMMANDS LIST** 📋

💬 **Chat Commands:**
• `/help` - Show this help
• `/models` - List all available models
• `/memory` - Show memory status
• `/joke` - Tell a joke
• `/shayari` - Write a shayari
• `/love` - Love message
• `/roast` - Roast the user (friendly)
• `/motivate` - Motivational quote
• `/story` - Tell a story

💻 **Code Commands:**
• `/code <language> <description>` - Generate code
• `/file <filename> <description>` - Generate file content
• `/debug <code>` - Debug code
• `/explain <code>` - Explain code

🔍 **Search Commands:**
• `/wiki <topic>` - Search Wikipedia
• `/search <query>` - Search across databases
• `/define <word>` - Dictionary lookup
• `/github <query>` - Search GitHub

⚙️ **Settings Commands:**
• `/setmodel <model>` - Change AI model
• `/setkey <api_key>` - Set custom API key
• `/clearhistory` - Clear chat history

🎨 **Fun Commands:**
• `/weather` - Random weather joke
• `/horoscope` - Fun horoscope
• `/dare` - Truth or dare
• `/quiz` - Random quiz question

💕 Made with love by Ruhi AI ✨"""
    
    elif cmd == '/models':
        models_list = "\n".join([f"• `{m}`" for m in GROQ_MODELS])
        return f"""🤖 **AVAILABLE MODELS:**

{models_list}

Currently using: **{user.selected_model}**

Use `/setmodel <name>` to change or use the dropdown above! ✨"""
    
    elif cmd == '/memory':
        count = Memory.query.filter_by(user_id=user.id).count()
        return f"""🧠 **MEMORY STATUS:**

• Total memories: **{count}**
• Memory limit: **50 recent messages** used for context
• Your model: **{user.selected_model}**
• Custom API: **{'Yes ✅' if user.custom_api_key else 'No ❌'}**
• Personality: **{user.personality}**

Main tumhari sab baatein yaad rakhti hun baby! 💕"""
    
    elif cmd == '/setmodel':
        if args and args in GROQ_MODELS:
            user.selected_model = args
            db.session.commit()
            return f"✅ Model changed to: **{args}**\nAb main is model se reply dungi! 🤖✨"
        else:
            return f"❌ Invalid model! Use `/models` to see available options."
    
    elif cmd == '/setkey':
        if args:
            user.custom_api_key = args
            db.session.commit()
            return "✅ Custom API key saved! Ab tumhara apna key use hoga! 🔑✨"
        return "❌ Please provide API key: `/setkey gsk_xxxxx`"
    
    elif cmd == '/clearhistory':
        ChatHistory.query.filter_by(user_id=user.id).delete()
        db.session.commit()
        return "✅ Chat history cleared! Fresh start baby! 🧹✨"
    
    # For other commands, return None to let AI handle them
    return None

@app.route('/api/history')
@login_required
def api_history():
    user = User.query.get(session['user_id'])
    chats = ChatHistory.query.filter_by(user_id=user.id).order_by(
        ChatHistory.timestamp.desc()
    ).limit(30).all()
    chats.reverse()
    
    messages = [{"role": c.role, "content": c.content} for c in chats]
    return jsonify({"messages": messages})

@app.route('/api/settings', methods=['POST'])
@login_required
def api_settings():
    user = User.query.get(session['user_id'])
    data = request.json
    
    if 'model' in data and data['model'] in GROQ_MODELS:
        user.selected_model = data['model']
    if 'api_key' in data:
        user.custom_api_key = data['api_key']
    if 'personality' in data:
        user.personality = data['personality']
    
    db.session.commit()
    return jsonify({"success": True})

@app.route('/api/clear-memory', methods=['POST'])
@login_required
def api_clear_memory():
    user = User.query.get(session['user_id'])
    Memory.query.filter_by(user_id=user.id).delete()
    db.session.commit()
    return jsonify({"success": True})

# ============================================================
# ADMIN API ENDPOINTS
# ============================================================

@app.route('/api/admin/add-key', methods=['POST'])
@admin_required
def admin_add_key():
    data = request.json
    key = data.get('key', '').strip()
    label = data.get('label', 'Default')
    max_usage = data.get('max_usage', 12000)
    
    if not key:
        return jsonify({"success": False, "error": "Key required"})
    
    existing = ApiKey.query.filter_by(key=key).first()
    if existing:
        return jsonify({"success": False, "error": "Key already exists"})
    
    api_key = ApiKey(key=key, label=label, max_usage=max_usage, added_by=ADMIN_USERNAME)
    db.session.add(api_key)
    db.session.commit()
    return jsonify({"success": True})

@app.route('/api/admin/delete-key/<int:key_id>', methods=['DELETE'])
@admin_required
def admin_delete_key(key_id):
    key = ApiKey.query.get(key_id)
    if key:
        db.session.delete(key)
        db.session.commit()
    return jsonify({"success": True})

@app.route('/api/download-keys')
@admin_required
def download_keys():
    keys = ApiKey.query.all()
    content = "RUHI AI - API KEYS BACKUP\n"
    content += "=" * 50 + "\n\n"
    for k in keys:
        content += f"ID: {k.id}\n"
        content += f"Key: {k.key}\n"
        content += f"Label: {k.label}\n"
        content += f"Usage: {k.usage_count}/{k.max_usage}\n"
        content += f"Active: {k.is_active}\n"
        content += f"Added: {k.created_at}\n"
        content += "-" * 30 + "\n"
    
    response = make_response(content)
    response.headers['Content-Type'] = 'text/plain'
    response.headers['Content-Disposition'] = 'attachment; filename=api_keys_backup.txt'
    return response

@app.route('/api/admin/add-shop', methods=['POST'])
@admin_required
def admin_add_shop():
    data = request.json
    key = data.get('key', '').strip()
    price = data.get('price', 'Free')
    
    if not key:
        return jsonify({"success": False, "error": "Key required"})
    
    masked = key[:6] + "..." + key[-4:] if len(key) > 10 else key
    
    item = ApiKeyShop(key_masked=masked, full_key=key, price_label=price)
    db.session.add(item)
    db.session.commit()
    return jsonify({"success": True})

@app.route('/api/shop/claim/<int:item_id>', methods=['POST'])
@login_required
def claim_shop_key(item_id):
    user = User.query.get(session['user_id'])
    item = ApiKeyShop.query.get(item_id)
    
    if not item or item.is_claimed:
        return jsonify({"success": False, "error": "Key not available"})
    
    item.is_claimed = True
    item.claimed_by = user.username
    user.custom_api_key = item.full_key
    db.session.commit()
    
    return jsonify({"success": True, "key": item.full_key[:8] + "..."})

# ============================================================
# INITIALIZE DATABASE
# ============================================================

with app.app_context():
    db.create_all()
    
    # Create admin user if not exists
    admin = User.query.filter_by(username=ADMIN_USERNAME).first()
    if not admin:
        admin = User(
            username=ADMIN_USERNAME,
            password_hash=generate_password_hash(ADMIN_PASSWORD),
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()
        print("✅ Admin user created!")

# ============================================================
# RUN
# ============================================================

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
    