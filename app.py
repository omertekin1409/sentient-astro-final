from flask import Flask, render_template, request, jsonify
from datetime import date, datetime, timedelta
from dateutil import parser as dateparse
import math, re, hashlib
import swisseph as swe  # pip install pyswisseph

app = Flask(__name__, template_folder="templates", static_folder="static")

# --- Burç aralıkları (güncel NASA / tropikal sistem) ---
def sun_sign(d: date):
    m, day = d.month, d.day
    if   (m == 3  and day >= 21) or (m == 4  and day <= 19): return "Koç"
    elif (m == 4  and day >= 20) or (m == 5  and day <= 20): return "Boğa"
    elif (m == 5  and day >= 21) or (m == 6  and day <= 20): return "İkizler"
    elif (m == 6  and day >= 21) or (m == 7  and day <= 22): return "Yengeç"
    elif (m == 7  and day >= 23) or (m == 8  and day <= 22): return "Aslan"
    elif (m == 8  and day >= 23) or (m == 9  and day <= 22): return "Başak"
    elif (m == 9  and day >= 23) or (m == 10 and day <= 22): return "Terazi"
    elif (m == 10 and day >= 23) or (m == 11 and day <= 21): return "Akrep"
    elif (m == 11 and day >= 22) or (m == 12 and day <= 21): return "Yay"
    elif (m == 12 and day >= 22) or (m == 1  and day <= 19): return "Oğlak"
    elif (m == 1  and day >= 20) or (m == 2  and day <= 18): return "Kova"
    elif (m == 2  and day >= 19) or (m == 3  and day <= 20): return "Balık"

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

# --- Numeroloji ---
def life_path(d: date):
    digits = list(str(d.year) + f"{d.month:02d}{d.day:02d}")
    n = sum(int(x) for x in digits)
    while n > 9 and n not in (11, 22, 33):
        n = sum(int(x) for x in str(n))
    return n

LETTER_MAP = {ch: i % 9 if i % 9 != 0 else 9 for i, ch in enumerate("abcdefghijklmnopqrstuvwxyz", 1)}

def number_from_name(name, pick="all"):
    clean = re.sub(r"[^a-zA-Z]", "", name).lower()
    if not clean: return 0
    if pick == "vowels":
        pool = [c for c in clean if c in "aeiou"]
    elif pick == "consonants":
        pool = [c for c in clean if c not in "aeiou"]
    else:
        pool = list(clean)
    total = sum(LETTER_MAP.get(c, 0) for c in pool)
    while total > 9 and total not in (11, 22, 33):
        total = sum(int(x) for x in str(total))
    return total

# --- Biyoritim ---
def biorhythm(born: date, target: date = None):
    if target is None:
        target = date.today()
    days = (target - born).days
    def cyc(p): return round((math.sin(2 * math.pi * days / p) + 1) / 2 * 100)
    return {"Fiziksel": cyc(23), "Duygusal": cyc(28), "Zihinsel": cyc(33)}

# --- Çin burcu ---
def chinese_zodiac(y: int):
    animals = ["Maymun", "Horoz", "Köpek", "Domuz", "Fare", "Öküz", "Kaplan", "Tavşan", "Ejderha", "Yılan", "At", "Keçi"]
    elements = ["Metal", "Su", "Ahşap", "Ateş", "Toprak"]
    return {"Hayvan": animals[y % 12], "Element": elements[((y - 4) % 10) // 2]}

# --- Yükselen ve Ay burcu ---
def rising_and_moon(d: datetime, place="Denizli"):
    # Türkiye varsayımı (çünkü render'da coğrafi API yok)
    lat, lon = 37.77, 29.09  # Denizli koordinatları
    jd = swe.julday(d.year, d.month, d.day, d.hour + d.minute/60)
    # Güneş, Ay ve Asc (yükselen) pozisyonları
    sun = swe.calc_ut(jd, swe.SUN)[0]
    moon = swe.calc_ut(jd, swe.MOON)[0]
    asc = swe.houses(jd, lat, lon)[0][0]

    # 12 burç 30 derece aralıkla
    signs = ["Koç", "Boğa", "İkizler", "Yengeç", "Aslan", "Başak", "Terazi", "Akrep", "Yay", "Oğlak", "Kova", "Balık"]
    def get_sign(deg): return signs[int(deg // 30) % 12]

    return {"Yükselen": get_sign(asc), "Ay": get_sign(moon)}

# --- Dönüm noktaları ---
def milestones(born: date):
    today = date.today()
    days = (today - born).days
    years = days // 365
    next_10k = ((days // 10000) + 1) * 10000
    next_10k_date = born + timedelta(days=next_10k)
    return {"Yaş": years, "Gün": days, "Sonraki10K": next_10k_date.isoformat(),
            "text": f"Yaş: {years} • Gün: {days} • Sonraki 10K gün: {next_10k_date.isoformat()}."}

# --- Günlük burç rehberi ---
DAILY_LINES_TR = {
    "Ateş": ["Cesur bir başlangıç yap; küçük bir adım bile alevi büyütür.",
             "Tempoyu belirle; hızlı karar, net sonuç getirir.",
             "Tutkunu yönlendir; dikkatini tek hedefe kilitle."],
    "Toprak": ["Planını somutlaştır; düzen istikrarı büyütür.",
               "Küçük ama sürekli adımlar bugün altın değerinde.",
               "Kaynaklarını sadeleştir; netlik verimi artırır."],
    "Hava": ["Fikrini paylaş; bağlantılar kapılar açar.",
             "Soru sor; merakın doğru çözümü getirecek.",
             "Zihnini boşalt; en iyi fikirler sakinlikte gelir."],
    "Su": ["Sezgine güven; kalbin yol gösteriyor.",
           "Duygularına alan aç; yumuşaklık güçtür.",
           "Derin bir nefes; akışta kal ve kabullen."]
}

def daily_horoscope(element: str):
    today = date.today().isoformat()
    seed = int(hashlib.md5(today.encode()).hexdigest(), 16)
    idx = seed % 3
    return DAILY_LINES_TR.get(element, ["Bugün merkezde kal."])[idx]

# --- Ana analiz ---
def analyze_data(name, dob, time, place, lang="tr"):
    d = dateparse.parse(dob).date()
    dt = datetime.strptime(f"{dob} {time}", "%Y-%m-%d %H:%M")
    sign = sun_sign(d)
    element, modality = ELEMENTS.get(sign, ""), MODALITY.get(sign, "")
    asc_moon = rising_and_moon(dt, place)
    lp = life_path(d)
    nums = {
        "Yaşam Yolu": lp,
        "Kader": number_from_name(name, "all"),
        "Ruh": number_from_name(name, "vowels"),
        "Kişilik": number_from_name(name, "consonants")
    }
    bio = biorhythm(d)
    cz = chinese_zodiac(d.year)
    ms = milestones(d)
    day_tip = daily_horoscope(element)

    astro_text = (f"Güneş {sign} • Yükselen {asc_moon['Yükselen']} • Ay {asc_moon['Ay']} • "
                  f"Element {element} • Modalite {modality}.")
    num_text = (f"Yaşam Yolu {nums['Yaşam Yolu']}, Kader {nums['Kader']}, Ruh {nums['Ruh']}, "
                f"Kişilik {nums['Kişilik']}.")
    sentient_text = (
        f"{name}, {place} doğumlu. Güneşin {sign}, yükselenin {asc_moon['Yükselen']}, "
        f"ayın {asc_moon['Ay']}. Bu karışım seni özgün ve sezgisel kılıyor. "
        f"Bugün ‘netlik→eylem’ zincirine odaklan: önce 1 net karar, ardından 20 dakikalık odaklanma."
    )

    return {
        "lang": "tr",
        "Astroloji": {"burc": sign, "element": element, "modalite": modality, "text": astro_text},
        "Numeroloji": nums | {"text": num_text},
        "Biyoritim": bio | {"text": f"Fiziksel {bio['Fiziksel']}% • Duygusal {bio['Duygusal']}% • Zihinsel {bio['Zihinsel']}%"},
        "Yaş & Dönüm Noktaları": ms,
        "Çin Burcu": cz | {"text": f"{cz['Element']} {cz['Hayvan']}"},
        "Günlük": {"text": day_tip},
        "Yorum": sentient_text,
        "Öneri": "Dobly diyor ki: Bugün iç sesini dinle ve küçük ama tamamlayıcı bir adım at."
    }

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/analyze", methods=["POST"])
def api_analyze():
    data = request.get_json()
    name  = data.get("name", "Misafir")
    dob   = data.get("dob")
    time  = data.get("time", "00:00")
    place = data.get("place", "Bilinmiyor")
    lang  = data.get("lang", "tr")
    result = analyze_data(name, dob, time, place, lang)
    return jsonify({"ok": True, "data": result})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
