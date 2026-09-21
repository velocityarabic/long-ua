"""
YouTube Long-Form Video Automation - Bilingual English/Ukrainian Content Generator
GENERATES 10-MINUTE VIDEOS with improved backgrounds for YouTube
"""

import os
import sys
import json
import random
import asyncio
import subprocess
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY")

# Directories
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
IMAGES_DIR = OUTPUT_DIR / "images"
AUDIO_DIR = OUTPUT_DIR / "audio"
VIDEO_DIR = OUTPUT_DIR / "video"
HISTORY_DIR = OUTPUT_DIR / "history"
LONGFORM_DIR = OUTPUT_DIR / "longform_videos"

for d in [OUTPUT_DIR, IMAGES_DIR, AUDIO_DIR, VIDEO_DIR, HISTORY_DIR, LONGFORM_DIR]:
    d.mkdir(exist_ok=True)

# Video settings (16:9 horizontal for YouTube long-form)
VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
FPS = 30
TARGET_DURATION_MINUTES = 5
TARGET_PHRASES = 120

# English category names
CATEGORIES_ENGLISH = [
    "Motivation", "Love", "Success", "Wisdom", "Happiness",
    "Self Improvement", "Gratitude", "Friendship", "Hope", "Creativity",
    "Inner Peace", "Confidence", "Perseverance", "Inspiration", "Positive Life",
    "Courage", "Kindness", "Patience", "Forgiveness", "Strength",
    "Joy", "Balance", "Growth", "Purpose", "Mindfulness",
]

# Ukrainian translations
CATEGORIES_UKRAINIAN = {
    "Motivation": "Мотивація",
    "Love": "Кохання",
    "Success": "Успіх",
    "Wisdom": "Мудрість",
    "Happiness": "Щастя",
    "Self Improvement": "Саморозвиток",
    "Gratitude": "Вдячність",
    "Friendship": "Дружба",
    "Hope": "Надія",
    "Creativity": "Творчість",
    "Inner Peace": "Внутрішній Спокій",
    "Confidence": "Впевненість",
    "Perseverance": "Наполегливість",
    "Inspiration": "Натхнення",
    "Positive Life": "Позитивне Життя",
    "Courage": "Сміливість",
    "Kindness": "Доброта",
    "Patience": "Терпіння",
    "Forgiveness": "Прощення",
    "Strength": "Сила",
    "Joy": "Радість",
    "Balance": "Баланс",
    "Growth": "Зростання",
    "Purpose": "Мета",
    "Mindfulness": "Усвідомленість",
}

# Edge TTS voices
ENGLISH_VOICE = "en-US-GuyNeural"
LANG_VOICE = "uk-UA-PolinaNeural"

# Phrase history file
PHRASE_HISTORY_FILE = HISTORY_DIR / "all_generated_phrases.json"

# Viral hook styles for engagement
VIRAL_STYLES = [
    "surprising fact",
    "common mistake correction",
    "quick tip",
    "must-know phrase",
    "local secret",
    "travel hack",
    "flirty phrase",
    "funny expression",
    "cultural insight",
    "word origin story"
]

# AI Model
AI_MODEL = os.getenv("AI_MODEL")

if not AI_MODEL:
    raise ValueError(
        "AI_MODEL not set! Please add 'AI_MODEL=gemini-fast' to your .env file."
    )


# ============== PHRASE HISTORY MANAGEMENT ==============

def load_phrase_history():
    if PHRASE_HISTORY_FILE.exists():
        with open(PHRASE_HISTORY_FILE, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    return {"phrases": [], "last_updated": None}


def save_phrase_history(data):
    data["last_updated"] = datetime.now().isoformat()
    with open(PHRASE_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def is_phrase_used(english_phrase):
    history = load_phrase_history()
    english_lower = english_phrase.lower().strip()
    for p in history.get("phrases", []):
        if p.get("english", "").lower().strip() == english_lower:
            return True
    return False


def is_phrase_similar(new_phrase, used_phrases, similarity_threshold=0.6):
    new_words = set(new_phrase.lower().split())
    if len(new_words) < 3:
        for used in used_phrases:
            if new_phrase.lower() in used.lower() or used.lower() in new_phrase.lower():
                return True
        return False
    for used in used_phrases:
        used_words = set(used.lower().split())
        if len(new_words) == 0 or len(used_words) == 0:
            continue
        intersection = len(new_words.intersection(used_words))
        union = len(new_words.union(used_words))
        similarity = intersection / union if union > 0 else 0
        if similarity >= similarity_threshold:
            return True
    return False


def filter_similar_phrases(phrases, history, similarity_threshold=0.6):
    used_phrases = [p.get("english", "") for p in history.get("phrases", [])]
    unique_phrases = []
    for phrase in phrases:
        english_text = phrase.get("english", "")
        if not is_phrase_similar(english_text, used_phrases, similarity_threshold):
            unique_phrases.append(phrase)
        else:
            print(f"[filter] Skipping similar: {english_text[:50]}...")
    return unique_phrases


def add_phrases_to_history(phrases, category):
    history = load_phrase_history()
    for phrase in phrases:
        history["phrases"].append({
            "english": phrase["english"],
            "ukrainian": phrase["ukrainian"],
            "category": category,
            "generated_at": datetime.now().isoformat()
        })
    save_phrase_history(history)
    print(f"[history] Added {len(phrases)} phrases to history (total: {len(history['phrases'])})")


# ============== CONTENT GENERATION ==============

def calculate_phrases_needed(target_minutes: int) -> int:
    avg_phrase_duration = 5.0
    total_seconds = target_minutes * 60
    return int(total_seconds / avg_phrase_duration)


def repair_and_parse_json(content: str):
    """Robustly parse JSON from LLM output with truncation repair and regex recovery."""
    import re
    cleaned = content.strip()
    if "```json" in cleaned:
        cleaned = cleaned.split("```json", 1)[1].split("```", 1)[0].strip()
    elif "```" in cleaned:
        cleaned = cleaned.split("```", 1)[1].split("```", 1)[0].strip()
    
    try:
        return json.loads(cleaned)
    except Exception:
        pass

    start = cleaned.find("[")
    end = cleaned.rfind("]")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(cleaned[start:end+1])
        except Exception:
            pass

    if start != -1:
        sub = cleaned[start:]
        last_brace = sub.rfind("}")
        if last_brace != -1:
            try:
                return json.loads(sub[:last_brace+1] + "]")
            except Exception:
                pass

    matches = re.findall(r'\{[^{}]*\"english\"[^{}]*\}', cleaned)
    results = []
    for m in matches:
        try:
            obj = json.loads(m)
            if isinstance(obj, dict) and "english" in obj:
                results.append(obj)
        except Exception:
            continue
    if results:
        return results

    raise ValueError("Could not parse or repair JSON from content")


def generate_phrases_for_longform(category_english: str, num_phrases: int) -> list:
    category_ukrainian = CATEGORIES_UKRAINIAN[category_english]
    history = load_phrase_history()
    used_phrases = [p.get("english", "") for p in history.get("phrases", [])]
    viral_style = random.choice(VIRAL_STYLES)
    all_phrases = []
    batch_size = 20
    max_attempts = 5

    for batch_num in range((num_phrases + batch_size - 1) // batch_size):
        remaining = num_phrases - len(all_phrases)
        current_batch_size = min(batch_size, remaining)
        if current_batch_size <= 0:
            break
        for attempt in range(max_attempts):
            try:
                import requests
                url = "https://gen.pollinations.ai/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {POLLINATIONS_API_KEY}",
                    "Content-Type": "application/json"
                }
                exclusion_note = ""
                if used_phrases:
                    recent = used_phrases[-30:] if len(used_phrases) > 30 else used_phrases
                    exclusion_note = f"\n\nAVOID these phrases (already used): {recent}"

                prompt = f"""Create {current_batch_size * 2} unique {category_english} phrases for English speakers learning Ukrainian.

Style: Make each phrase feel like a {viral_style} - something people would want to share!

CRITICAL RULE - ABSOLUTELY ZERO Ukrainian IN ENGLISH FIELD:
The "english" field must contain ONLY English words. NO Ukrainian words at all.
The "ukrainian" field contains the Ukrainian translation.
The "pronunciation" field is phonetic English spelling approximating Ukrainian sounds.

These are INSPIRATIONAL PHRASES about the topic, NOT language-learning tips.

WRONG (teaching tip with Ukrainian words): {{"english": "Don't say 'щось там,' it means more than 'something.'", ...}}
WRONG (Ukrainian word in english): {{"english": "Use 'добрий день' for hello", ...}}
WRONG (lesson tip): {{"english": "Say 'будь ласка' for please", ...}}
CORRECT (pure english phrase): {{"english": "Knowledge is the key to wisdom.", "ukrainian": "Знання - це ключ до мудрості", "pronunciation": "znan-ya tse klyuch do mud-ros-ti"}}
CORRECT: {{"english": "A wise person listens more than they speak.", "ukrainian": "Мудра людина більше слухає, ніж говорить", "pronunciation": "mud-ra lyu-di-na bil-she slu-kha-ye, nizh go-vo-ryt"}}

The english field MUST be 100% English words only. Absolutely NO Ukrainian words in the english field.

IMPORTANT RULES FOR NATURAL SPEECH:
1. Keep phrases SHORT (5-12 words max per language)
2. Add NATURAL PAUSES using commas (e.g., "Dream big, start small")
3. Use punctuation for breathing room in TTS
4. Avoid long run-on sentences
5. Each phrase should be speakable in 3-5 seconds
6. Use everyday vocabulary - avoid exotic or rare words
7. Avoid complex grammar - keep it simple and practical
8. Vary sentence structure for natural flow

For each phrase:
1. English phrase (pure English, zero Ukrainian words) with commas for natural pauses
2. Ukrainian translation
3. Pronunciation guide (phonetic English spelling)
CRITICAL: Every translation MUST be in Ukrainian. NEVER use German, Spanish, or any other language. Only Ukrainian.

Return as JSON array:
[{{"english": "...", "ukrainian": "...", "pronunciation": "..."}}]

IMPORTANT: Create FRESH, UNIQUE phrases that haven't been used before.{exclusion_note}"""

                payload = {
                    "model": AI_MODEL,
                    "messages": [
                        {"role": "system", "content": "You create INSPIRATIONAL PHRASES for YouTube language learning videos. CRITICAL: The 'english' field must be PURE ENGLISH with ZERO Ukrainian words - no Ukrainian words at all. These are universal inspirational phrases, NOT language learning tips. Ukrainian goes ONLY in the 'ukrainian' field."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 1.0
                }

                response = requests.post(url, headers=headers, json=payload, timeout=90)
                response.raise_for_status()

                data = response.json()
                content = data["choices"][0]["message"]["content"].strip()

                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()

                phrases = repair_and_parse_json(content)
                filtered_phrases = filter_similar_phrases(phrases, history)
                unique_phrases = []
                for phrase in filtered_phrases:
                    if len(phrase["english"].split()) > 15:
                        continue
                    if not is_phrase_used(phrase["english"]):
                        unique_phrases.append(phrase)
                for phrase in unique_phrases:
                    if len(all_phrases) < num_phrases:
                        all_phrases.append(phrase)
                if len(all_phrases) >= num_phrases:
                    break
            except Exception as e:
                print(f"[content] Batch {batch_num + 1}, Attempt {attempt + 1} failed: {e}")
        if len(all_phrases) < num_phrases:
            import time
            time.sleep(1)

    if not all_phrases:
        print(f"[content] AI generation produced 0 phrases. Loading fresh fallback phrases for '{category_english}'...")
        all_phrases = get_fresh_fallback_phrases(category_english, num_phrases)
    elif len(all_phrases) < num_phrases:
        print(f"[content] Only {len(all_phrases)} phrases generated. Padding with fresh fallback phrases...")
        extras = get_fresh_fallback_phrases(category_english, num_phrases - len(all_phrases))
        for ex in extras:
            if ex not in all_phrases:
                all_phrases.append(ex)

    final_phrases = all_phrases[:num_phrases]
    if final_phrases:
        add_phrases_to_history(final_phrases, category_english)
    print(f"[content] Generated {len(final_phrases)} phrases for long-form video")
    return final_phrases


def get_fresh_fallback_phrases(category: str, num_phrases: int) -> list:
    all_fallbacks = {
        "Motivation": [
            {"english": "Believe in yourself.", "ukrainian": "Вір у себе.", "pronunciation": "veer u se-be"},
            {"english": "You are capable of amazing things.", "ukrainian": "Ти здатний на неймовірні речі.", "pronunciation": "ty zdat-nyi na nei-mo-vir-ni re-chi"},
            {"english": "Dream big, start small.", "ukrainian": "Мрій велико, починай з малого.", "pronunciation": "mriy ve-ly-ko, po-chy-nay z ma-lo-ho"},
            {"english": "Your future is created by your actions.", "ukrainian": "Твоє майбутнє створюється твоїми діями.", "pronunciation": "tvo-ye mai-but-nye stvo-ryu-yet-sya tvo-yi-my di-ya-my"},
            {"english": "Never give up on your dreams.", "ukrainian": "Ніколи не відмовляйся від своїх мрій.", "pronunciation": "ni-ko-ly ne vid-mov-lyai-sya vid svo-yikh mriy"},
            {"english": "Small steps lead to big changes.", "ukrainian": "Малі кроки ведуть до великих змін.", "pronunciation": "ma-li kro-ky ve-dut do ve-ly-khykh zmin"},
            {"english": "You are stronger than you think.", "ukrainian": "Ти сильніший, ніж думаєш.", "pronunciation": "ty syl-ni-shyi, nizh du-ma-yesh"},
        ],
        "Love": [
            {"english": "Love yourself first.", "ukrainian": "Люби себе насамперед.", "pronunciation": "lyu-by se-be na-sam-pe-red"},
            {"english": "Love makes everything possible.", "ukrainian": "Любов робить усе можливим.", "pronunciation": "lyu-bov ro-byt u-se mozh-ly-vym"},
            {"english": "My heart beats for you.", "ukrainian": "Моє серце б'ється для тебе.", "pronunciation": "mo-ye ser-tse byet-sya dlya te-be"},
            {"english": "You are my everything.", "ukrainian": "Ти моє все.", "pronunciation": "ty mo-ye vse"},
            {"english": "Together forever, hand in hand.", "ukrainian": "Разом назавжди, рука в руку.", "pronunciation": "ra-zom na-zavzh-dy, ru-ka v ru-ku"},
        ],
        "Success": [
            {"english": "Success comes from hard work.", "ukrainian": "Успіх приходить через наполегливу працю.", "pronunciation": "us-pikh pry-kho-dyt che-rez na-po-le-hly-vu pra-tsyu"},
            {"english": "Keep going, you're getting there.", "ukrainian": "Продовжуй, ти вже майже там.", "pronunciation": "pro-dov-zhui, ty vzhe mai-zhe tam"},
            {"english": "Winners never quit.", "ukrainian": "Переможці ніколи не здаються.", "pronunciation": "pe-re-mozh-tsi ni-ko-ly ne zda-yut-sya"},
            {"english": "Your effort will pay off.", "ukrainian": "Твої зусилля окупляться.", "pronunciation": "tvo-yi zu-syl-lya o-kup-lyat-sya"},
        ],
        "Wisdom": [
            {"english": "Knowledge is power.", "ukrainian": "Знання – це сила.", "pronunciation": "znan-nya tse sy-la"},
            {"english": "Learn from yesterday, live for today.", "ukrainian": "Вчися з минулого, живи сьогодні.", "pronunciation": "vchy-sya z my-nu-lo-ho, zhy-vy so-hod-ni"},
            {"english": "Think before you act.", "ukrainian": "Думай, перш ніж діяти.", "pronunciation": "du-mai, persh nizh di-ya-ty"},
            {"english": "Experience is the best teacher.", "ukrainian": "Досвід – найкращий вчитель.", "pronunciation": "dos-vid nai-kra-shchyi vchy-tel"},
        ],
        "Happiness": [
            {"english": "Happiness is a choice.", "ukrainian": "Щастя – це вибір.", "pronunciation": "shchas-tya tse vy-bir"},
            {"english": "Find joy in the little things.", "ukrainian": "Знаходь радість у дрібницях.", "pronunciation": "zna-khod ra-dist u dri-bny-tsyakh"},
            {"english": "Smile, it makes others happy.", "ukrainian": "Посміхайся, це робить інших щасливими.", "pronunciation": "pos-mi-khai-sya, tse ro-byt in-shykh shchas-ly-vy-my"},
            {"english": "Today is a gift.", "ukrainian": "Сьогодні – це дар.", "pronunciation": "so-hod-ni tse dar"},
        ],
        "Self Improvement": [
            {"english": "Be better than yesterday.", "ukrainian": "Будь кращим, ніж учора.", "pronunciation": "bud krah-shchym, nizh ucho-ra"},
            {"english": "Grow through what you go through.", "ukrainian": "Зростай через те, що переживаєш.", "pronunciation": "zro-stai che-rez te, shcho pe-re-zhy-va-yesh"},
            {"english": "Invest in yourself daily.", "ukrainian": "Інвестуй у себе щодня.", "pronunciation": "in-ves-tui u se-be shchod-nya"},
        ],
        "Gratitude": [
            {"english": "Thank you for everything.", "ukrainian": "Дякую тобі за все.", "pronunciation": "dya-ku-yu to-bi za vse"},
            {"english": "I appreciate your help.", "ukrainian": "Я ціную твою допомогу.", "pronunciation": "ya tsi-nu-yu tvo-yu do-po-mo-hu"},
            {"english": "Grateful for this moment.", "ukrainian": "Вдячний за цю мить.", "pronunciation": "vdya-chnyi za tsyu myt"},
        ],
        "Friendship": [
            {"english": "Friends forever, no matter what.", "ukrainian": "Друзі назавжди, незважаючи ні на що.", "pronunciation": "dru-zi na-zavzh-dy, ne-zva-zha-yu-chy ni na shcho"},
            {"english": "You are my best friend.", "ukrainian": "Ти мій найкращий друг.", "pronunciation": "ty miy nai-kra-shchyi druh"},
            {"english": "True friends stick together.", "ukrainian": "Справжні друзі тримаються разом.", "pronunciation": "spravzh-ni dru-zi try-ma-yut-sya ra-zom"},
        ],
        "Hope": [
            {"english": "There is always hope.", "ukrainian": "Надія є завжди.", "pronunciation": "na-di-ya ye zavzh-dy"},
            {"english": "Better days are coming.", "ukrainian": "Кращі дні попереду.", "pronunciation": "krah-shchi dni po-pe-re-du"},
            {"english": "Keep faith, keep going.", "ukrainian": "Зберігай віру, продовжуй рухатись.", "pronunciation": "zbe-ri-hay vi-ru, pro-dov-zhui ru-kha-tys"},
        ],
        "Creativity": [
            {"english": "Create something beautiful today.", "ukrainian": "Створи щось прекрасне сьогодні.", "pronunciation": "stvo-ry shchos pre-kras-ne so-hod-ni"},
            {"english": "Your imagination is unlimited.", "ukrainian": "Твоя уява безмежна.", "pronunciation": "tvo-ya u-ya-va bez-mezh-na"},
            {"english": "Art comes from the heart.", "ukrainian": "Мистецтво походить від серця.", "pronunciation": "my-stets-tvo po-kho-dyt vid ser-tsya"},
            {"english": "Express yourself freely.", "ukrainian": "Виражай себе вільно.", "pronunciation": "vy-ra-zhai se-be vil-no"},
            {"english": "Innovation starts with curiosity.", "ukrainian": "Інновації починаються з цікавості.", "pronunciation": "in-no-va-tsi-i po-chy-na-yut-sya z tsi-ka-vos-ti"},
        ],
        "Inner Peace": [
            {"english": "Find peace within yourself.", "ukrainian": "Знайди спокій у собі.", "pronunciation": "znai-dy spo-kii u so-bi"},
            {"english": "Breathe, relax, let go.", "ukrainian": "Дихай, розслабся, відпусти.", "pronunciation": "dy-khai, roz-slab-sya, vid-pus-ty"},
            {"english": "Calm mind, happy heart.", "ukrainian": "Спокійний розум, щасливе серце.", "pronunciation": "spo-kii-nyi ro-zum, shchas-ly-ve ser-tse"},
        ],
        "Confidence": [
            {"english": "You are enough, just as you are.", "ukrainian": "Ти достатній, такий, як ти є.", "pronunciation": "ty dos-tat-nii, ta-kyi, yak ty ye"},
            {"english": "Stand tall, speak up.", "ukrainian": "Стій гордо, говори впевнено.", "pronunciation": "stii hor-do, ho-vo-ry vpev-ne-no"},
            {"english": "Believe in your abilities.", "ukrainian": "Вір у свої здібності.", "pronunciation": "vir u svo-yi zdi-bnos-ti"},
        ],
        "Perseverance": [
            {"english": "Never give up, keep pushing.", "ukrainian": "Ніколи не здавайся, продовжуй боротись.", "pronunciation": "ni-ko-ly ne zda-vai-sya, pro-dov-zhui bo-ro-tys"},
            {"english": "Storms make trees take deeper roots.", "ukrainian": "Бурі змушують дерева пускати глибше коріння.", "pronunciation": "bu-ri zmu-shu-yut de-re-va pus-ka-ty hlyb-she ko-rin-nya"},
            {"english": "Patience and persistence win.", "ukrainian": "Терпіння та наполегливість перемагають.", "pronunciation": "ter-pin-nya ta na-po-le-hly-vist pe-re-ma-ha-yut"},
        ],
        "Inspiration": [
            {"english": "Let your light shine bright.", "ukrainian": "Нехай твоє світло сяє яскраво.", "pronunciation": "ne-khai tvo-ye svit-lo sya-ye yas-kra-vo"},
            {"english": "Inspire others by your actions.", "ukrainian": "Надихай інших своїми діями.", "pronunciation": "na-dy-khai in-shykh svo-yi-my di-ya-my"},
            {"english": "Be the change you want to see.", "ukrainian": "Будь зміною, яку хочеш бачити.", "pronunciation": "bud zmi-no-yu, ya-ku kho-chesh ba-chy-ty"},
        ],
        "Positive Life": [
            {"english": "Choose positivity every day.", "ukrainian": "Обирай позитив щодня.", "pronunciation": "o-by-ray po-zy-tyv shchod-nya"},
            {"english": "Good vibes only.", "ukrainian": "Тільки позитивна енергія.", "pronunciation": "til-ky po-zy-tyv-na e-ner-hi-ya"},
            {"english": "Life is what you make it.", "ukrainian": "Життя таким є, яким ти його створиш.", "pronunciation": "zhyt-tya ta-kym ye, ya-kym ty yo-ho stvo-rysh"},
        ],
        "Courage": [
            {"english": "Be brave, take the first step.", "ukrainian": "Будь сміливим, зроби перший крок.", "pronunciation": "bud smi-ly-vym, zro-by per-shyi krok"},
            {"english": "Courage is not the absence of fear.", "ukrainian": "Сміливість – це не відсутність страху.", "pronunciation": "smi-ly-vist tse ne vid-sut-nist stra-khu"},
            {"english": "Face your fears head on.", "ukrainian": "Дивись своїм страхам в очі.", "pronunciation": "dy-vys svo-yim stra-kham v o-chi"},
        ],
        "Kindness": [
            {"english": "Be kind to everyone you meet.", "ukrainian": "Будь добрим до кожного, кого зустрінеш.", "pronunciation": "bud dob-rym do kozh-no-ho, ko-ho zus-tri-nesh"},
            {"english": "Kindness costs nothing, means everything.", "ukrainian": "Доброта нічого не коштує, але означає все.", "pronunciation": "dob-ro-ta ni-cho-ho ne kosh-tu-ye, a-le oz-na-cha-ye vse"},
            {"english": "Spread kindness wherever you go.", "ukrainian": "Поширюй доброту, куди б ти не пішов.", "pronunciation": "po-schy-ryui dob-ro-tu, ku-dy b ty ne pi-shov"},
        ],
        "Patience": [
            {"english": "Good things take time.", "ukrainian": "Хороші речі потребують часу.", "pronunciation": "kho-ro-shi re-chi po-tre-bu-yut cha-su"},
            {"english": "Wait patiently, trust the process.", "ukrainian": "Чекай терпляче, довіряй процесу.", "pronunciation": "che-kai ter-plya-che, do-vi-ryai pro-tse-su"},
            {"english": "Rome wasn't built in a day.", "ukrainian": "Рим не за один день будували.", "pronunciation": "rym ne za o-dyn den bu-du-va-ly"},
        ],
        "Forgiveness": [
            {"english": "Forgive and set yourself free.", "ukrainian": "Прости і звільни себе.", "pronunciation": "pros-ty i zvil-ny se-be"},
            {"english": "Let go of grudges, find peace.", "ukrainian": "Відпусти образи, знайди спокій.", "pronunciation": "vid-pus-ty ob-ra-zy, znai-dy spo-kii"},
            {"english": "Forgiveness is a gift to yourself.", "ukrainian": "Прощення – це подарунок собі.", "pronunciation": "pro-shchen-nya tse po-da-ru-nok so-bi"},
        ],
        "Strength": [
            {"english": "You are stronger than you know.", "ukrainian": "Ти сильніший, ніж ти думаєш.", "pronunciation": "ty syl-ni-shyi, nizh ty du-ma-yesh"},
            {"english": "Inner strength comes from within.", "ukrainian": "Внутрішня сила походить зсередини.", "pronunciation": "vnu-trish-nya sy-la po-kho-dyt zse-re-dy-ny"},
            {"english": "Challenges make you stronger.", "ukrainian": "Виклики роблять тебе сильнішим.", "pronunciation": "vy-kly-ky rob-lyat te-be syl-ni-shym"},
        ],
        "Joy": [
            {"english": "Find joy in every moment.", "ukrainian": "Знаходь радість у кожній миті.", "pronunciation": "zna-khod ra-dist u kozh-nii my-ti"},
            {"english": "Joy is contagious, spread it.", "ukrainian": "Радість заразна, поширюй її.", "pronunciation": "ra-dist za-raz-na, po-schy-ryui yi-yi"},
            {"english": "Dance like nobody's watching.", "ukrainian": "Танцюй, ніби ніхто не бачить.", "pronunciation": "tan-tsiui, ni-by nikhto ne ba-chyt"},
        ],
        "Balance": [
            {"english": "Find balance in your life.", "ukrainian": "Знайди баланс у своєму житті.", "pronunciation": "znai-dy ba-lans u svo-ye-mu zhyt-ti"},
            {"english": "Work hard, rest well.", "ukrainian": "Працюй наполегливо, відпочивай добре.", "pronunciation": "pra-tsiui na-po-le-hly-vo, vid-po-chy-vai dob-re"},
            {"english": "Too much of anything is not good.", "ukrainian": "Забагато чогось не є добре.", "pronunciation": "za-ba-ha-to cho-hos ne ye dob-re"},
        ],
        "Growth": [
            {"english": "Growth happens outside your comfort zone.", "ukrainian": "Зростання відбувається поза зоною комфорту.", "pronunciation": "zro-stan-nya vid-bu-va-yet-sya po-za zo-no-yu kom-for-tu"},
            {"english": "Embrace change, grow stronger.", "ukrainian": "Приймай зміни, ставай сильнішим.", "pronunciation": "pryi-mai zmi-ny, sta-vai syl-ni-shym"},
            {"english": "Every challenge is a chance to grow.", "ukrainian": "Кожен виклик – це шанс зростати.", "pronunciation": "ko-zhen vy-klyk tse shans zro-sta-ty"},
        ],
        "Purpose": [
            {"english": "Find your purpose, follow it.", "ukrainian": "Знайди свою мету, слідуй за нею.", "pronunciation": "znai-dy svo-yu me-tu, sli-dui za ne-yu"},
            {"english": "Your life has meaning.", "ukrainian": "Твоє життя має сенс.", "pronunciation": "tvo-ye zhyt-tya ma-ye sens"},
            {"english": "Live with intention, not accident.", "ukrainian": "Живи з наміром, а не випадково.", "pronunciation": "zhy-vy z na-mi-rom, a ne vy-pad-ko-vo"},
        ],
        "Mindfulness": [
            {"english": "Be present in this moment.", "ukrainian": "Будь присутнім у цій миті.", "pronunciation": "bud pry-sut-nim u tsii my-ti"},
            {"english": "Breathe deeply, stay grounded.", "ukrainian": "Дихай глибоко, залишайся врівноваженим.", "pronunciation": "dy-khai hly-bo-ko, za-ly-shai-sya vriv-no-va-zhe-nym"},
            {"english": "Notice the little things around you.", "ukrainian": "Помічай дрібниці навколо себе.", "pronunciation": "po-mi-chai dri-bny-tsi nav-ko-lo se-be"},
        ],
    }

    fallbacks = all_fallbacks.get(category, all_fallbacks["Motivation"])
    history = load_phrase_history()
    fresh_phrases = []
    for p in fallbacks:
        if not is_phrase_used(p["english"]) and not is_phrase_similar(p["english"], [h.get("english", "") for h in history.get("phrases", [])]):
            fresh_phrases.append(p)

    if len(fresh_phrases) < num_phrases:
        for cat, cat_fallbacks in all_fallbacks.items():
            if cat != category:
                for p in cat_fallbacks:
                    if not is_phrase_used(p["english"]) and not is_phrase_similar(p["english"], [h.get("english", "") for h in history.get("phrases", [])]):
                        fresh_phrases.append(p)
                    if len(fresh_phrases) >= num_phrases:
                        break
            if len(fresh_phrases) >= num_phrases:
                break

    return fresh_phrases[:num_phrases]


# ============== AUDIO GENERATION ==============

async def generate_single_audio(text: str, voice: str, output_path: str, retries: int = 3):
    import edge_tts
    for attempt in range(retries):
        try:
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(output_path)
            if Path(output_path).exists() and Path(output_path).stat().st_size > 300:
                return True
        except Exception as e:
            if attempt < retries - 1:
                await asyncio.sleep(0.8 * (attempt + 1))
            else:
                print(f"  TTS error after {retries} attempts: {e}")
    return False


def generate_all_audio(phrases: list, output_dir: str):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    audio_files = []

    for i, phrase in enumerate(phrases):
        english_file = output_dir / f"english_{i}.mp3"
        lang_file = output_dir / f"lang_{i}.mp3"
        combined_file = output_dir / f"combined_{i}.mp3"

        if (i + 1) % 20 == 0:
            print(f"  Generating audio {i+1}/{len(phrases)}...")

        en_success = asyncio.run(generate_single_audio(phrase["english"], ENGLISH_VOICE, str(english_file)))
        if not en_success:
            cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", "2", str(english_file)]
            subprocess.run(cmd, capture_output=True)

        lang_success = asyncio.run(generate_single_audio(phrase["ukrainian"], LANG_VOICE, str(lang_file)))
        if not lang_success:
            cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", "2", str(lang_file)]
            subprocess.run(cmd, capture_output=True)

        en_duration = get_audio_duration(str(english_file))
        lang_duration = get_audio_duration(str(lang_file))

        pause_between = 0.5
        total_duration = en_duration + pause_between + lang_duration

        cmd = [
            "ffmpeg", "-y",
            "-i", str(english_file),
            "-i", str(lang_file),
            "-filter_complex", f"[0:a]apad=pad_dur=0.5[a0];[a0][1:a]concat=n=2:v=0:a=1[out]",
            "-map", "[out]",
            str(combined_file)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            concat_file = output_dir / f"concat_{i}.txt"
            with open(concat_file, "w", encoding="utf-8") as f:
                f.write(f"file '{english_file.as_posix()}'\n")
                f.write(f"file '{lang_file.as_posix()}'\n")
            cmd = [
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0",
                "-i", str(concat_file),
                "-c:a", "aac",
                str(combined_file)
            ]
            subprocess.run(cmd, capture_output=True)
            if concat_file.exists():
                concat_file.unlink()

        actual_duration = get_audio_duration(str(combined_file))

        audio_files.append({
            "index": i,
            "english": str(english_file),
            "lang": str(lang_file),
            "combined": str(combined_file),
            "duration": actual_duration,
            "en_duration": en_duration,
            "lang_duration": lang_duration
        })

    print(f"\n[audio] Generated {len(audio_files)} phrase audios")
    return audio_files


def get_audio_duration(audio_file: str) -> float:
    if not Path(audio_file).exists():
        return 2.0
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", audio_file]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return float(result.stdout.strip())
    except:
        return 2.0


def create_final_narration(audio_files: list, output_file: str):
    n = len(audio_files)
    print(f"[audio] Combining {n} audio files...")
    concat_file = Path(output_file).parent / "narration_list.txt"
    with open(concat_file, "w", encoding="utf-8") as f:
        for audio_info in audio_files:
            combined_path = Path(audio_info["combined"])
            if combined_path.exists():
                path_str = str(combined_path.resolve()).replace("\\", "/").replace("'", "'\\''")
                f.write(f"file '{path_str}'\n")
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c:a", "copy", str(output_file)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if concat_file.exists():
        concat_file.unlink()
    if result.returncode == 0 and Path(output_file).exists() and Path(output_file).stat().st_size > 0:
        size = Path(output_file).stat().st_size
        print(f"\n[audio] Final narration: {Path(output_file).name} ({size/1024:.1f} KB)")
        return True
    return False


# ============== BACKGROUND GENERATION ==============

def create_premium_background(category_english: str):
    from PIL import Image, ImageDraw
    img = Image.new('RGB', (VIDEO_WIDTH, VIDEO_HEIGHT))
    draw = ImageDraw.Draw(img)
    for y in range(VIDEO_HEIGHT):
        ratio = y / VIDEO_HEIGHT
        if ratio < 0.5:
            r, g, b = 255, 252, 245
        else:
            r = int(255 + (245 - 255) * ((ratio - 0.5) * 2))
            g = int(252 + (240 - 252) * ((ratio - 0.5) * 2))
            b = int(245 + (230 - 245) * ((ratio - 0.5) * 2))
        draw.rectangle([(0, y), (VIDEO_WIDTH, y + 1)], fill=(r, g, b))
    return img


def generate_complete_image(phrase_data: dict, category_english: str, output_path: str):
    try:
        from PIL import Image, ImageDraw, ImageFont, ImageFilter
    except ImportError:
        print("PIL not available. Install: pip install Pillow")
        return None

    img = create_premium_background(category_english)
    img = img.convert('RGBA')
    draw = ImageDraw.Draw(img)

    # Font paths - check fonts/ directory first
    english_font_paths = [
        str(BASE_DIR / "fonts" / "DejaVuSans-Bold.ttf"),
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]

    lang_font_paths = [
        str(BASE_DIR / "fonts" / "DejaVuSans-Bold.ttf"),
        "C:/Windows/Fonts/arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]

    def load_font(font_paths, size):
        for font_path in font_paths:
            try:
                return ImageFont.truetype(font_path, size)
            except:
                continue
        return ImageFont.load_default()

    font_category = load_font(english_font_paths, 42)
    font_english = load_font(english_font_paths, 68)
    font_lang = load_font(lang_font_paths, 82)
    font_pronunciation = load_font(lang_font_paths, 48)
    font_branding = load_font(english_font_paths, 38)

    english = phrase_data.get("english", "")
    ukrainian = phrase_data.get("ukrainian", "")
    pronunciation = phrase_data.get("pronunciation", "")

    def wrap_text(text, font, max_width):
        words = text.split()
        lines = []
        current_line = []
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] - bbox[0] <= max_width:
                current_line.append(word)
            else:
                if current_line: lines.append(' '.join(current_line))
                current_line = [word]
        if current_line: lines.append(' '.join(current_line))
        return lines

    # Header Bar
    cat_text = category_english.upper()
    cat_bbox = draw.textbbox((0, 0), cat_text, font=font_category)
    cat_w = cat_bbox[2] - cat_bbox[0]
    badge_h = 75
    badge_pad_x = 40
    container_w = cat_w + (badge_pad_x * 2)
    container_x = 60
    container_y = 60
    draw.rounded_rectangle(
        [(container_x, container_y), (container_x + container_w, container_y + badge_h)],
        radius=15, fill=(45, 35, 65, 255)
    )
    draw.text(
        (container_x + container_w // 2, container_y + badge_h // 2 + 2),
        cat_text,
        fill=(255, 255, 255, 255),
        font=font_category,
        anchor="mm"
    )

    CONTENT_Y_CENTER = VIDEO_HEIGHT // 2
    GAP = 60

    en_lines = wrap_text(english, font_english, VIDEO_WIDTH - 300)
    en_line_h = 80
    en_total_h = len(en_lines) * en_line_h

    lang_lines = wrap_text(ukrainian, font_lang, VIDEO_WIDTH - 300)
    lang_line_h = 100
    lang_total_h = len(lang_lines) * lang_line_h

    pron_text = f"[{pronunciation}]"
    pron_lines = wrap_text(pron_text, font_pronunciation, VIDEO_WIDTH - 400)
    pron_line_h = 60
    pron_total_h = len(pron_lines) * pron_line_h

    total_content_h = en_total_h + lang_total_h + pron_total_h + (GAP * 2)
    y_start = CONTENT_Y_CENTER - (total_content_h // 2)

    box_w = VIDEO_WIDTH - 200
    box_x = (VIDEO_WIDTH - box_w) // 2

    # English Box
    en_box_h = en_total_h + 60
    draw.rounded_rectangle(
        [(box_x, y_start), (box_x + box_w, y_start + en_box_h)],
        radius=25, fill=(65, 50, 95, 255)
    )
    for i, line in enumerate(en_lines):
        draw.text((VIDEO_WIDTH // 2, y_start + 30 + (i * en_line_h) + en_line_h // 2),
                  line, fill=(255, 255, 255), font=font_english, anchor="mm")

    y_cursor = y_start + en_box_h + GAP

    # Ukrainian Section
    lang_box_h = lang_total_h + 60
    draw.rounded_rectangle(
        [(box_x, y_cursor), (box_x + box_w, y_cursor + lang_box_h)],
        radius=25, fill=(95, 80, 125, 255)
    )
    for i, line in enumerate(lang_lines):
        draw.text((VIDEO_WIDTH // 2, y_cursor + 30 + (i * lang_line_h) + lang_line_h // 2),
                  line, fill=(255, 255, 255), font=font_lang, anchor="mm")

    y_cursor += lang_box_h + (GAP // 2)

    # Pronunciation Section
    pron_box_h = pron_total_h + 40
    pron_box_w = box_w - 200
    pron_box_x = (VIDEO_WIDTH - pron_box_w) // 2
    draw.rounded_rectangle(
        [(pron_box_x, y_cursor), (pron_box_x + pron_box_w, y_cursor + pron_box_h)],
        radius=20, fill=(255, 210, 160, 255)
    )
    for i, line in enumerate(pron_lines):
        draw.text((VIDEO_WIDTH // 2, y_cursor + 20 + (i * pron_line_h) + pron_line_h // 2),
                  line, fill=(70, 45, 25), font=font_pronunciation, anchor="mm")

    # Branding
    brand_text = "VELOCITY UKRAINIAN"
    brand_bbox = draw.textbbox((0, 0), brand_text, font=font_branding)
    brand_w = brand_bbox[2] - brand_bbox[0]
    draw.text((VIDEO_WIDTH - brand_w - 60, VIDEO_HEIGHT - 80), brand_text,
              fill=(45, 35, 65, 255), font=font_branding)

    img = img.convert('RGB')
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, quality=95, optimize=True)
    return output_path


# ============== THUMBNAIL GENERATION ==============

def generate_thumbnail(category_english: str, category_ukrainian: str, output_path: str):
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("PIL not available for thumbnail. Install: pip install Pillow")
        return None

    img = create_premium_background(category_english)
    img = img.convert('RGBA')
    draw = ImageDraw.Draw(img)

    english_font_paths = [
        str(BASE_DIR / "fonts" / "DejaVuSans-Bold.ttf"),
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
    ]
    lang_font_paths = [
        str(BASE_DIR / "fonts" / "DejaVuSans-Bold.ttf"),
        "C:/Windows/Fonts/arialbd.ttf",
    ]

    def load_font(font_paths, size):
        for font_path in font_paths:
            try: return ImageFont.truetype(font_path, size)
            except: continue
        return ImageFont.load_default()

    font_huge = load_font(english_font_paths, 130)
    font_main = load_font(lang_font_paths, 110)
    font_sub = load_font(english_font_paths, 60)
    font_badge = load_font(english_font_paths, 45)

    draw.text((VIDEO_WIDTH // 2, 220), "MASTER UKRAINIAN", fill=(45, 35, 65), font=font_huge, anchor="mm")

    cat_text = category_english.upper()
    cat_bbox = draw.textbbox((0, 0), cat_text, font=font_sub)
    cat_w = cat_bbox[2] - cat_bbox[0]
    draw.rounded_rectangle(
        [(VIDEO_WIDTH // 2 - cat_w // 2 - 40, 320), (VIDEO_WIDTH // 2 + cat_w // 2 + 40, 410)],
        radius=20, fill=(65, 50, 95, 255)
    )
    draw.text((VIDEO_WIDTH // 2, 365), cat_text, fill=(255, 255, 255), font=font_sub, anchor="mm")

    draw.text((VIDEO_WIDTH // 2, 530), category_ukrainian, fill=(45, 35, 65), font=font_main, anchor="mm")

    cta_text = "60 ВАЖЛИВИХ ФРАЗ"
    draw.rounded_rectangle(
        [(VIDEO_WIDTH // 2 - 300, 650), (VIDEO_WIDTH // 2 + 300, 730)],
        radius=15, fill=(255, 210, 160, 255)
    )
    draw.text((VIDEO_WIDTH // 2, 690), cta_text, fill=(70, 45, 25), font=font_badge, anchor="mm")

    draw.rectangle([(0, VIDEO_HEIGHT - 100), (VIDEO_WIDTH, VIDEO_HEIGHT)], fill=(45, 35, 65, 255))
    draw.text((VIDEO_WIDTH // 2, VIDEO_HEIGHT - 50), "VELOCITY UKRAINIAN", fill=(255, 255, 255), font=font_badge, anchor="mm")

    img = img.convert('RGB')
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, quality=95, optimize=True)
    return output_path


def extract_video_thumbnail(video_path: str, output_path: str, timestamp_seconds: int = 5):
    try:
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(timestamp_seconds),
            "-i", str(video_path),
            "-vframes", "1",
            "-q:v", "2",
            str(output_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0 and Path(output_path).exists():
            print(f"  Video thumbnail extracted: {Path(output_path).name}")
            return str(output_path)
        else:
            print(f"  Could not extract video thumbnail")
            return None
    except Exception as e:
        print(f"  Thumbnail extraction error: {e}")
        return None


# ============== TITLE & DESCRIPTION GENERATION ==============

def generate_title_description(category_english: str, category_ukrainian: str, phrases: list, duration_minutes: float, output_dir: str):
    titles = [
        f"Learn Ukrainian in 10 Minutes | {category_english} Phrases Every Beginner NEEDS to Know! ({category_ukrainian})",
        f"60 Ukrainian Phrases for {category_english} | Speak Ukrainian Like a Native! ({category_ukrainian})",
        f"Master Ukrainian {category_english} | 60 Essential Ukrainian Phrases with Pronunciation | Velocity Ukrainian",
        f"Ukrainian Learning Made Easy | {category_english} Vocabulary | 10 Minute Lesson",
        f"Speak Ukrainian Fluently | {category_english} Phrases | English + Ukrainian + Pronunciation",
    ]

    description = f"""🇺🇦 Learn Ukrainian with Velocity Ukrainian! 🇺🇦

In this video, you'll learn 60 essential Ukrainian phrases about {category_english} ({category_ukrainian}).
Perfect for beginners and intermediate learners!

📚 WHAT YOU'LL LEARN:
• 60 practical {category_english} phrases in Ukrainian
• Correct pronunciation guide
• Natural pauses for speaking practice
• Common expressions used by native speakers

⏱️ VIDEO TIMESTAMPS:
"""

    avg_phrase_duration = duration_minutes * 60 / len(phrases)
    for i in range(0, len(phrases), 10):
        timestamp = int(i * avg_phrase_duration / 60)
        minute = timestamp
        second = int((i * avg_phrase_duration) % 60)
        end_phrase = min(i + 10, len(phrases))
        description += f"{minute:02d}:{second:02d} Phrases {i+1}-{end_phrase}\n"

    description += """
📝 ALL PHRASES IN THIS VIDEO:
"""

    for i, phrase in enumerate(phrases, 1):
        description += f"""
{i}. {phrase['english']}
   Ukrainian: {phrase['ukrainian']}
    Pronunciation: {phrase['pronunciation']}
"""

    description += """
🎯 PERFECT FOR:
• Ukrainian beginners wanting to expand vocabulary
• Intermediate learners practicing pronunciation
• Anyone interested in Ukrainian language and culture
• Language enthusiasts and polyglots
• Students preparing for exams

💡 TIPS FOR LEARNING:
1. Repeat each phrase out loud
2. Practice daily for best results
3. Use the pauses to speak along
4. Write down phrases you find difficult
5. Review this video multiple times

🔔 SUBSCRIBE for more Ukrainian learning content!
👍 LIKE this video if you found it helpful!
💬 COMMENT which phrases you want to learn next!

📱 FOLLOW VELOCITY UKRAINIAN:
[Add your social media links here]

🎵 MUSIC:
[Add music credits if applicable]

📖 RELATED VIDEOS:
• Ukrainian Motivation Phrases
• Ukrainian Love Expressions
• Basic Ukrainian Greetings

#LearnUkrainian #UkrainianPhrases #UkrainianLanguage #{category_english.replace(' ', '')} #VelocityUkrainian #UkrainianForBeginners #SpeakUkrainian #UkrainianVocabulary #Pronunciation #LanguageLearning #Ukrainian101 #UkrainianLesson

---
© Velocity Ukrainian - Making Ukrainian learning accessible to everyone!
"""

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(output_dir / "youtube_upload_info.txt", "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("YOUTUBE VIDEO UPLOAD INFORMATION\n")
        f.write("=" * 80 + "\n\n")
        f.write("RECOMMENDED TITLES (Choose one):\n")
        f.write("-" * 80 + "\n")
        for i, title in enumerate(titles, 1):
            f.write(f"\n{i}. {title}\n")
        f.write("\n" + "=" * 80 + "\n")
        f.write("SELECTED TITLE (Recommended):\n")
        f.write("-" * 80 + "\n")
        f.write(f"\n{titles[0]}\n")
        f.write("\n" + "=" * 80 + "\n")
        f.write("VIDEO DESCRIPTION:\n")
        f.write("-" * 80 + "\n\n")
        f.write(description)
        f.write("\n" + "=" * 80 + "\n")
        f.write("VIDEO TAGS (for YouTube):\n")
        f.write("-" * 80 + "\n")
        tags = [
            "Learn Ukrainian",
            "Ukrainian Phrases",
            "Ukrainian Language",
            category_english,
            "Velocity Ukrainian",
            "Ukrainian for Beginners",
            "Speak Ukrainian",
            "Ukrainian Vocabulary",
            "Pronunciation",
            "Language Learning",
            "Ukrainian 101",
            "Ukrainian Lesson"
        ]
        f.write(", ".join(tags) + "\n")

    metadata = {
        "recommended_titles": titles,
        "selected_title": titles[0],
        "description": description,
        "category_english": category_english,
        "category_ukrainian": category_ukrainian,
        "phrases_count": len(phrases),
        "duration_minutes": round(duration_minutes, 2),
        "tags": tags
    }

    with open(output_dir / "video_metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"\n[metadata] Generated YouTube upload files")
    print(f"  youtube_upload_info.txt (title + description + tags)")
    print(f"  video_metadata.json")

    return metadata


# ============== VIDEO CREATION ==============

def create_video_from_images_audio(image_files: list, audio_files: list, combined_audio: str, output_file: str):
    print(f"\n[video] Creating long-form video from {len(image_files)} images...")

    temp_clips = []

    for i, (img_path, audio_info) in enumerate(zip(image_files, audio_files)):
        duration = audio_info['duration']
        print(f"  Image {i+1}/{len(image_files)}: {duration:.2f}s")

        temp_clip = Path(output_file).parent / f"temp_clip_{i:02d}.mp4"
        temp_clips.append(temp_clip)

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(img_path),
            "-i", audio_info['combined'],
            "-vf", f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=decrease,pad={VIDEO_WIDTH}:{VIDEO_HEIGHT}:(ow-iw)/2:(oh-ih)/2,fps={FPS}",
            "-c:v", "libx264",
            "-c:a", "aac",
            "-b:a", "128k",
            "-pix_fmt", "yuv420p",
            "-preset", "medium",
            "-shortest",
            "-vsync", "cfr",
            str(temp_clip)
        ]

        subprocess.run(cmd, check=True, capture_output=True)

    print("[video] Concatenating clips...")
    concat_file = Path(output_file).parent / "concat_list.txt"

    with open(concat_file, "w", encoding="utf-8") as f:
        for clip in temp_clips:
            f.write(f"file '{clip.resolve().as_posix()}'\n")

    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c", "copy", str(output_file)]
    subprocess.run(cmd, check=True, capture_output=True)

    if concat_file.exists():
        concat_file.unlink()

    video_duration = get_audio_duration(str(output_file))
    print(f"[video] Video created: {Path(output_file).name} ({video_duration:.2f}s)")

    for clip in temp_clips:
        if clip.exists():
            clip.unlink()


# ============== MAIN WORKFLOW ==============

def generate_longform_video(category_english: str = None, target_phrases: int = None):
    if not category_english:
        category_english = random.choice(CATEGORIES_ENGLISH)

    phrases_count = target_phrases if target_phrases else TARGET_PHRASES

    print(f"\n{'='*80}")
    print(f"LONG-FORM VIDEO - Category: {category_english} ({CATEGORIES_UKRAINIAN[category_english]})")
    print(f"Target Phrases: {phrases_count}")
    print(f"{'='*80}\n")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    video_dir = LONGFORM_DIR / f"{category_english}_longform_{timestamp}"
    video_dir.mkdir(exist_ok=True)

    print(f"[1/6] Generating {phrases_count} unique phrases (checking history)...")
    phrases = generate_phrases_for_longform(category_english, phrases_count)

    for i, phrase in enumerate(phrases, 1):
        print(f"  {i}. {phrase['english']} -> {phrase['ukrainian']}")

    print(f"\n[info] Total phrases: {len(phrases)}")

    print(f"\n[2/6] Generating {len(phrases)} images with premium backgrounds...")
    for i, phrase in enumerate(phrases):
        output_path = video_dir / f"phrase_{i:04d}.jpg"
        generate_complete_image(phrase, category_english, str(output_path))
        if (i + 1) % 10 == 0:
            print(f"  Progress: {i+1}/{len(phrases)} images...")

    print(f"\n[3/6] Using first phrase image as thumbnail...")
    thumbnail_path = video_dir / "thumbnail.jpg"
    first_phrase = sorted(video_dir.glob("phrase_*.jpg"))
    if first_phrase:
        import shutil
        shutil.copy2(str(first_phrase[0]), str(thumbnail_path))
        print(f"  Thumbnail: {first_phrase[0].name} (content-based)")
    else:
        try:
            from generate_thumbnail import generate_scenic_image
            result = generate_scenic_image(category_english, category_english, str(thumbnail_path))
            if result and Path(result).exists():
                print(f"  gpt-image-2 thumbnail saved")
            else:
                print(f"  gpt-image-2 failed, using built-in")
                generate_thumbnail(category_english, CATEGORIES_UKRAINIAN[category_english], str(thumbnail_path))
        except Exception as e:
            print(f"  Thumbnail error: {e}, using built-in")
            generate_thumbnail(category_english, CATEGORIES_UKRAINIAN[category_english], str(thumbnail_path))
    video_thumbnail_path = video_dir / "video_thumbnail_frame.jpg"
    print(f"\n[4/6] Generating audio for {len(phrases)} phrases...")
    audio_files = generate_all_audio(phrases, str(video_dir))

    final_audio = video_dir / "narration.mp3"
    create_final_narration(audio_files, str(final_audio))

    total_duration = sum(a['duration'] for a in audio_files)
    print(f"\n[info] Total audio duration: {total_duration:.2f}s ({total_duration/60:.2f} minutes)")

    print(f"\n[5/6] Creating long-form video with transitions...")
    output_video = video_dir / "final_video.mp4"

    image_files = sorted([str(p) for p in video_dir.glob("phrase_*.jpg")])

    create_video_from_images_audio(
        image_files,
        audio_files,
        str(final_audio),
        str(output_video)
    )

    print(f"\n[5.5/6] Extracting video frame for thumbnail...")
    extract_video_thumbnail(str(output_video), str(video_thumbnail_path), timestamp_seconds=5)

    print(f"\n[6/6] Generating YouTube title, description, and metadata...")
    title_meta = generate_title_description(
        category_english,
        CATEGORIES_UKRAINIAN[category_english],
        phrases,
        total_duration / 60,
        str(video_dir)
    )

    import json as _json
    from pathlib import Path as _Path
    meta_out = {
        "title": title_meta.get("selected_title", f"Learn Ukrainian: {category_english}"),
        "description": title_meta.get("description", ""),
        "tags": ["Learn Ukrainian", "Ukrainian Phrases", "Ukrainian", category_english, "Velocity Ukrainian"],
        "category_english": category_english,
        "category_ukrainian": CATEGORIES_UKRAINIAN[category_english],
        "phrases_count": len(phrases),
        "duration_seconds": total_duration,
        "duration_minutes": total_duration / 60,
        "video_path": str(output_video),
        "thumbnail_path": str(thumbnail_path),
        "phrases": phrases,
        "generated_at": datetime.now().isoformat(),
    }
    _Path("output").mkdir(exist_ok=True)
    with open(_Path("output") / "latest_video.json", "w", encoding="utf-8") as f:
        _json.dump(meta_out, f, indent=2, ensure_ascii=False)
    with open(_Path("output") / "latest_upload_info.json", "w", encoding="utf-8") as f:
        _json.dump({"title": meta_out["title"], "description": meta_out["description"],
                     "category": category_english, "phrases_count": len(phrases)}, f, indent=2)

    print(f"\n{'='*80}")
    print(f"LONG-FORM VIDEO COMPLETE!")
    print(f"  {video_dir}")
    print(f"  {output_video.name}")
    print(f"  thumbnail.jpg (generated)")
    print(f"  {video_thumbnail_path.name} (from video)")
    print(f"  youtube_upload_info.txt (title + description + tags)")
    print(f"  Duration: {total_duration/60:.2f} minutes")
    print(f"  Phrases: {len(phrases)}")
    print(f"  Branding: Velocity Ukrainian")
    print(f"  Format: 16:9 (1920x1080)")
    print(f"{'='*80}\n")

    return meta_out


def generate_multiple_longform(count: int = 1, target_phrases: int = None):
    print(f"\nGenerating {count} long-form video(s)...")
    print("="*80)
    for i in range(count):
        print(f"\n{'='*80}")
        print(f"VIDEO {i+1}/{count}")
        print("="*80)
        generate_longform_video(target_phrases=target_phrases)
    print("\n" + "="*80)
    print(f"ALL {count} LONG-FORM VIDEOS COMPLETE!")
    print("="*80)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Velocity Ukrainian YouTube Long-form Video Generator")
    parser.add_argument("--phrases", type=int, default=TARGET_PHRASES, help="Number of phrases to generate")
    parser.add_argument("--category", type=str, default=None, help="Specific category to generate")
    args = parser.parse_args()

    print("\n" + "="*80)
    print("VELOCITY UKRAINIAN - YOUTUBE LONG-FORM AUTOMATION")
    print("="*80)
    print("\nFEATURES:")
    print("  16:9 format (1920x1080) for YouTube long-form")
    print(f"  Target {args.phrases} phrases (~{args.phrases * 5.5 / 60:.1f} minute video)")
    print("  Light Theme (Cream background, dark/light purple + peach containers)")
    print("  Natural pauses with commas (non-robotic TTS)")
    print("  Perfect audio-video synchronization")
    print("  NEVER repeats phrases (permanent history tracking)")
    print(f"\nAVAILABLE CATEGORIES ({len(CATEGORIES_ENGLISH)} total):")
    for i, cat in enumerate(CATEGORIES_ENGLISH, 1):
        print(f"   {i:2d}. {cat} ({CATEGORIES_UKRAINIAN[cat]})")
    print(f"\nVIDEO SPECIFICATIONS:")
    print(f"  Resolution: {VIDEO_WIDTH}x{VIDEO_HEIGHT} (16:9)")
    print(f"  Frame Rate: {FPS} FPS")
    print(f"  Target Phrases: {args.phrases}")
    print(f"  Estimated Duration: ~{args.phrases * 5.5 / 60:.1f} minutes")
    print(f"  Phrase History: PERMANENT (never deletes)")
    print("="*80)

    generate_longform_video(category_english=args.category, target_phrases=args.phrases)