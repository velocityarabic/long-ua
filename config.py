"""VELOCITY LONGFORM - 16:9 chapter lesson, brand and motion constants."""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

OUTPUT_DIR = BASE_DIR / "output"
LESSONS_DIR = OUTPUT_DIR / "lessons"
HISTORY_DIR = OUTPUT_DIR / "history"
SCENE_DIR = BASE_DIR / "scene"

VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
FPS = 30

TARGET_CHAPTERS = 8
PHRASES_PER_CHAPTER = 7
TARGET_PHRASES = TARGET_CHAPTERS * PHRASES_PER_CHAPTER

# ---------------------------------------------------------------- brand

BRAND = "VELOCITY UKRAINIAN"
BRAND_LOCKUP_TOP = "VELOCITY"
BRAND_LOCKUP_BOTTOM = "UKRAINIAN"
HANDLE = "@velocityukrainian"
MASCOT_NAME = "Velo"

# ==== LANGUAGE PACK START ====
LANGUAGE = {'code': 'uk',
 'name': 'Ukrainian',
 'native_name': 'Українська',
 'history_key': 'ukrainian',
 'english_voice': 'en-US-AvaNeural',
 'english_fallback_voice': 'en-US-GuyNeural',
 'native_voice': 'uk-UA-OstapNeural',
 'native_fallback_voice': 'uk-UA-PolinaNeural',
 'native_engine': 'edge',
 'native_lang_code': 'uk',
 'english_rate': '-4%',
 'native_rate': '-10%',
 'english_pitch': '+0Hz',
 'native_pitch': '+0Hz',
 'native_label': 'УКРАЇНСЬКА',
 'translit_label': 'SAY IT LIKE',
 'flag': 'ua',
 'greeting': 'Привіт!',
 'encouragement': 'Чудово!',
 'rtl': False,
 'char_tiles': False,
 'script_font': '',
 'glyphs': 'абвгґдеєжзиіїйклмнопрстуфхцчшщьюя'}
# ==== LANGUAGE PACK END ====

# ==== CATEGORIES START ====
CATEGORIES = {'Motivation': 'Мотивація',
 'Love': 'Кохання',
 'Success': 'Успіх',
 'Wisdom': 'Мудрість',
 'Happiness': 'Щастя',
 'Self Improvement': 'Саморозвиток',
 'Gratitude': 'Вдячність',
 'Friendship': 'Дружба',
 'Hope': 'Надія',
 'Creativity': 'Творчість',
 'Inner Peace': 'Внутрішній Спокій',
 'Confidence': 'Впевненість',
 'Perseverance': 'Наполегливість',
 'Inspiration': 'Натхнення',
 'Positive Life': 'Позитивне Життя',
 'Courage': 'Сміливість',
 'Kindness': 'Доброта',
 'Patience': 'Терпіння',
 'Forgiveness': 'Прощення',
 'Strength': 'Сила',
 'Joy': 'Радість',
 'Balance': 'Баланс',
 'Growth': 'Зростання',
 'Purpose': 'Мета',
 'Mindfulness': 'Усвідомленість',
 'Travel & Airport': 'Подорожі та аеропорт',
 'Ordering Food & Dining': 'Замовлення їжі та харчування',
 'Shopping & Prices': 'Покупки та ціни',
 'Asking for Directions': 'Як запитати дорогу',
 'Hotel & Accommodation': 'Готель та проживання',
 'Daily Routine': 'Щоденна рутина',
 'Meeting People & Greetings': 'Знайомство та привітання',
 'Emergency & Health': "Надзвичайні ситуації та здоров'я",
 'Public Transportation': 'Громадський транспорт',
 'Work & Office': 'Робота та офіс',
 'Weather & Small Talk': 'Погода та світські розмови',
 'Coffee Shop & Bakery': "Кав'ярня та пекарня",
 'Family & Home': "Сім'я та дім",
 'Hobbies & Free Time': 'Хобі та вільний час',
 'Dating & Romance': 'Знайомства та романтика',
 'Phone Calls & Messages': 'Телефонні дзвінки та повідомлення',
 'Banking & Money': 'Банки та гроші',
 'Doctor & Pharmacy': 'Лікар та аптека',
 'Sports & Fitness': 'Спорт та фітнес',
 'Celebrations & Parties': 'Святкування та вечірки',
 'Feelings & Emotions': 'Почуття та емоції',
 'Agreeing & Disagreeing': 'Згода та незгода',
 'Making Plans': 'Планування',
 'Common Native Slang': 'Поширений місцевий сленг',
 'Cultural Traditions': 'Культурні традиції'}
# ==== CATEGORIES END ====

CATEGORY_NAMES = list(CATEGORIES.keys())

AI_MODEL = os.getenv("AI_MODEL", "openai/gpt-5.4-nano")
AI_FALLBACK_MODEL = os.getenv("AI_FALLBACK_MODEL", "gemini-fast")
POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY", "")

# ---------------------------------------------------------------- timing (seconds)

INTRO_DURATION = 7.2
CHAPTER_INTRO_DURATION = 4.4
OUTRO_DURATION = 13.0

EN_CARD_IN = 0.70
GAP_EN_NATIVE = 0.60
NATIVE_CARD_LEAD = 0.40
GAP_BEFORE_REPEAT = 1.00
TAIL_HOLD = 1.30

# ---------------------------------------------------------------- palette

INK = "#30303A"
MUTED = "#8A8A8A"
CREAM = "#FFF8E7"
GREEN = "#58CC02"
GREEN_DARK = "#46A302"
GREEN_DEEP = "#3D8F00"
BLUE = "#1CB0F6"
PURPLE = "#7C5CFF"
ORANGE = "#FF7A00"
RED = "#FF4B4B"
YELLOW = "#F5A700"
TEAL = "#00A889"
PINK = "#E056A0"

# ==== HASHTAGS START ====
HASHTAGS = ['#learnukrainian',
 '#ukrainianlessons',
 '#ukrainianforbeginners',
 '#languagelearning',
 '#ukrainianvocabulary',
 '#velocityukrainian',
 '#dailyukrainian',
 '#ukrainian',
 '#learnlanguages',
 '#speakukrainian']
# ==== HASHTAGS END ====
