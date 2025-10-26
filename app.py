from flask import Flask, render_template, request, jsonify
from datetime import date, datetime, timedelta
import math, re, hashlib

app = Flask(__name__, template_folder="templates", static_folder="static")

# ---- Burç tarihleri (GÜNCEL) ----
ZODIAC_SIGNS = [
    ("Oğlak", (12, 22), (1, 19)),
    ("Kova", (1, 20), (2, 18)),
    ("Balık", (2, 19), (3, 20)),
    ("Koç", (3, 21), (4, 19)),
    ("Boğa", (4, 20), (5, 20)),
    ("İkizler", (5, 21), (6, 20)),
    ("Yengeç", (6, 21), (7, 22)),
    ("Aslan", (7, 23), (8, 22)),
    ("Başak", (8, 23), (9, 22)),
    ("Terazi", (9, 23), (10, 22)),
    ("Akrep", (10, 23), (11, 21)),
    ("Yay", (11, 22), (12, 21))
]

ELEMENTS = {
    "Koç": "Ateş", "Aslan": "Ateş", "Yay": "Ateş",
    "Boğa": "Toprak", "Başak": "Toprak", "Oğlak": "Toprak",
    "İkizler": "Hava", "Terazi": "Hava", "Kova": "Hava",
    "Yengeç": "Su", "Akrep": "Su", "Balık": "Su"
}

MODALITY = {
    "Koç": "Öncü", "Yengeç": "Öncü", "Terazi": "Öncü", "Oğlak": "Öncü",
    "Boğa": "Sabit", "Aslan": "Sabit", "Akrep": "Sabit", "Kova": "Sabit",
    "İkizler": "Değişken", "Başak": "Değişken", "Yay": "Değişken", "Balık": "Değişken"
}

# ---- Burç belirleme ----
def sun_sign(birthdate):
    m, d = birthdate.month, birthdate.day
    for sign, start, end in ZODIAC_SIGNS:
        sm, sd = start
        em, ed = end
        if (m == sm and d >= sd) or (m == em and d <= ed):
            return sign
    return "Oğlak"  # fallback

# ---- Numeroloji ----
LETTER_MAP = {ch: i % 9 if i % 9 != 0 else 9 for i, ch in enumerate("abcdefghijklmnopqrstuvwxyz", 1)}

def number_from_name(name):
    clean = re.sub(r"[^a-zA-Z]", "", name).lower()
    total = sum(LETTER_MAP.get(c, 0) for c in clean)
    while total > 9 and total not in (11, 22, 33):
        total = sum(int(x) for x in str(total))
    return total

def life_path(d):
    total = sum(int(x) for x in f"{d.year}{d.month:02d}{d.day:02d}")
    while total > 9 and total not in (11, 22, 33):
        total = sum(int(x) for x in str(total))
    return total

# ---- Biyoritim ----
def biorhythm(born, target=None):
    if target is None:
        target = date.today()
    days = (target - born).days
    def cycle(period):
        return round((math.sin(2 * math.pi * days / period) + 1) / 2 * 100)
    return {
        "Fiziksel": cycle(23),
        "Duygusal": cycle(28),
        "Zihinsel": cycle(33)
    }

# ---- Çin burcu ----
def chinese_zodiac(year):
    animals = ["Maymun", "Horoz", "Köpek", "Domuz", "Fare", "Öküz", "Kaplan", "Tavşan", "Ejderha", "Yılan", "At", "Keçi"]
    elements = ["Metal", "Su", "Ahşap", "Ateş", "Toprak"]
    return {
        "Hayvan": animals[year % 12],
        "Element": elements[((year - 4) % 10) // 2]
    }

# ---- Günlük burç mesajı ----
DAILY_LINES = {
    "Ateş": [
        "Cesur ol, yeni başlangıç seni bekliyor.",
        "Harekete geç, enerji senin yanında.",
        "Tutkunu yönlendir, kalbin ne söylüyorsa o yoldan git."
    ],
    "Toprak": [
        "Ayaklarını yere bas, planlarını somutlaştır.",
        "Sabırlı ol, başarı emin adımlarla gelecek.",
        "Bugün disiplin kazandırır, temelleri güçlendir."
    ],
    "Hava": [
        "Yeni fikirler doğuyor, paylaşmaktan çekinme.",
        "Zihnin açık, öğrenmeye hazır bir gün.",
        "Sözlerin etkili, doğru kişiye doğru kelimeyi söyle."
    ],
    "Su": [
        "Duygularını ifade et, seni özgürleştirecek.",
        "Sezgine güven, kalbin doğruyu biliyor.",
        "Bugün derin bir nefes al, duygusal denge seni bulacak."
    ]
}

def daily_message(element):
    seed = int(hashlib.md5(date.today().isoformat().encode()).hexdigest(), 16)
    idx = seed % 3
    return DAILY_LINES.get(element, ["Bugün merkezde kal."])[idx]

# ---- Ana analiz ----
def analyze_data(name, dob, time, place):
    d = datetime.strptime(dob, "%Y-%m-%d").date()
    sign = sun_sign(d)
    element = ELEMENTS.get(sign, "")
    modality = MODALITY.get(sign, "")
    lp = life_path(d)
    num = number_from_name(name)
    bio = biorhythm(d)
    cz = chinese_zodiac(d.year)
    day_tip = daily_message(element)

    dobly_comment = f"{name}, senin burcun **{sign}** ({element} elementi). Bugün {day_tip.lower()} Dobly diyor ki: 'Net bir hedef seç ve küçük ama kararlı adımlar at.'"

    return {
        "Burç": sign,
        "Element": element,
        "Modalite": modality,
        "YaşamYolu": lp,
        "Numeroloji": num,
        "Biyoritim": bio,
        "ÇinBurcu": cz,
        "Dobly": dobly_comment
    }

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/analyze", methods=["POST"])
def api_analyze():
    data = request.get_json()
    name = data.get("name", "Misafir")
    dob = data.get("dob")
    time = data.get("time", "00:00")
    place = data.get("place", "Bilinmiyor")
    result = analyze_data(name, dob, time, place)
    return jsonify({"ok": True, "data": result})

if __name__ == "__main__":
    app.run(debug=True)
