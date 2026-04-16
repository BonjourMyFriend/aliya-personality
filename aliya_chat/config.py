import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent
PROJECT_DIR = BASE_DIR.parent
ENV_PATH = PROJECT_DIR / ".env"
DB_PATH = BASE_DIR / "aliya_chat.db"
SYSTEM_PROMPT_PATH = PROJECT_DIR / "aliya_system_prompt.txt"
SEEDS_PATH = BASE_DIR / "seeds.json"
PORTRAITS_DIR = BASE_DIR / "assets" / "portraits"

# API
API_KEY = os.getenv("API_KEY", "")
BASE_URL = os.getenv("BASE_URL", "")
CHAT_MODEL = os.getenv("CHAT_MODEL", "claude-sonnet-4-20250514")
SUMMARY_MODEL = os.getenv("SUMMARY_MODEL", "claude-haiku-4-5-20251001")
MAX_TOKENS = 2048

# Memory
SUMMARY_THRESHOLD_CHARS = 1500  # 降到很低，确保对话几轮后就生成摘要
RECENT_TURNS_IN_CONTEXT = 40  # 增加历史上下文，让Aliya有更多记忆

# Time
SHIP_TIME_OFFSET_HOURS = 5  # Aliya is always 5 hours behind the user

# Timing (words per minute)
WPM_READING = 230
WPM_TYPING = 90  # fast casual chat typing (not formal 45 WPM)
JITTER_RANGE = (0.7, 1.3)

# UI
WINDOW_WIDTH = 500
WINDOW_HEIGHT = 700
COLORS = {
    "bg": "#0a1628",
    "frame": "#0d1e36",
    "aliya_bubble": "#162544",
    "user_bubble": "#1a3a5c",
    "text_primary": "#e8f0ff",
    "text_secondary": "#6b7fa0",
    "accent": "#2563eb",
    "accent_hover": "#1d4ed8",
    "border": "#2a4a6c",
    "input_bg": "#0a1628",
    "input_disabled": "#060e1a",
    "placeholder": "#4a6a8c",
}
