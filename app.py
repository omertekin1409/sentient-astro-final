from flask import Flask, render_template, request, jsonify
from datetime import date, datetime, timedelta
from dateutil import parser as dateparse
import math, re, hashlib, os

app = Flask(__name__, template_folder="templates", static_folder="static")

# ---- Astro helpers (TR) ----
ZODIAC_BOUNDS = [
    ((1, 20), "Oğlak"), ((2, 19), "Kova"), ((3, 21), "Balık"),
    ((4, 20), "Koç"), ((5, 21), "Boğa"), ((6, 21), "İkizler"),
    ((7, 23), "Yengeç"), ((8, 23), "Aslan"), ((9, 23), "Başak"),
    ((10, 23), "Terazi"), ((11, 22), "Akrep"), ((12, 22), "Yay"),
    ((12, 31), "Oğlak")
]
ELEMENTS = {
    "Koç":"Ateş","Aslan":"Ateş","Yay":"Ateş",
    "Boğa":"Toprak","Başak":"Toprak","Oğlak":"Toprak",
    "İkizler":"Hava","Terazi":"Hava","Kova":"Hava",
    "Yengeç":"Su","Akrep":"Su","Balık":"Su"
}
MODALITY = {
    "Koç":"Öncü","Yengeç":"Öncü","Terazi":"Öncü","Oğlak":"Öncü",
    "Boğa":"Sabit","Aslan":"Sabit","Akrep":"Sabit","Kova":"Sabit",
    "İkizler":"Değişken","Başak":"Değişken","Yay":"Değişken","Balık":"Değişken"
}

def sun_sign(d: date):
    m, day = d.month, d.day
    sign = "Oğlak"
    for (mm, dd), s in ZODIAC_BOUNDS:
        if (m, day) >= (mm, dd):
            sign = s
    return sign

def life_path(d: date):
    digits = list(str(d.year) + f"{d.month:02d}{d.day:02d}")
    n = sum(int(x) for x in digits)
    while n > 9 and n not in (11,22,33):
        n = sum(int(x) for x in str(n))
    return n

LETTER_MAP = {ch:i%9 if i%9!=0 else 9 for i,ch in enumerate("abcdefghijklmnopqrstuvwxyz",1)}
def number_from_name(name, pick="all"):
    clean = re.sub(r"[^a-zA-Z]", "", name).lower()
    if not clean: return 0
    if pick == "vowels":
        pool = [c for c in clean if c in "aeiou"]
    elif pick == "consonants":
        pool = [c for c in clean if c not in "aeiou"]
    else:
        pool = list(clean)
    total = sum(LETTER_MAP.get(c,0) for c in pool)
    while total > 9 and total not in (11,22,33):
        total = sum(int(x) for x in str(total))
    return total

def biorhythm(born: date, target: date=None):
    if target is None: target = date.today()
    days = (target - born).days
    def cyc(p): return round((math.sin(2*math.pi*days/p)+1)/2*100)
    return {"Fiziksel":cyc(23),"Duygusal":cyc(28),"Zihinsel":cyc(33)}

def chinese_zodiac(y:int):
    animals = ["Maymun","Horoz","Köpek","Domuz","Fare","Öküz","Kaplan","Tavşan","Ejderha","Yılan","At","Keçi"]
    elements = ["Metal","Su","Ahşap","Ateş","Toprak"]
    return {"Hayvan": animals[y % 12], "Element": elements[((y - 4) % 10)//2]}

def milestones(born: date):
    today = date.today()
    days = (today - born).days
    years = days // 365
    next_10k = ((days // 10000) + 1) * 10000
    next_10k_date = born + timedelta(days=next_10k)
    return {"Yaş":years,"Gün":days,"Sonraki10K":next_10k_date.isoformat()}

DAILY_LINES_TR = {
    "Ateş": [
        "Cesur bir başlangıç yap; küçük bir adım bile alevi büyütür.",
        "Tempoyu belirle; hızlı karar, net sonuç getirir.",
        "Tutkunu yönlendir; dikkatini tek hedefe kilitle."
    ],
    "Toprak": [
        "Planını somutlaştır; düzen istikrarı büyütür.",
        "Küçük ama sürekli adımlar bugün altın değerinde.",
        "Kaynaklarını sadeleştir; netlik verimi artırır."
    ],
    "Hava": [
        "Fikrini paylaş; bağlantılar kapılar açar.",
        "Soru sor; merakın doğru çözümü getirecek.",
        "Zihnini boşalt; en iyi fikirler sakinlikte gelir."
    ],
    "Su": [
        "Sezgine güven; kalbin yol gösteriyor.",
        "Duygularına alan aç; yumuşaklık güçtür.",
        "Derin bir nefes; akışta kal ve kabullen."
    ]
}

def daily_horoscope(element_tr: str):
    today = date.today().isoformat()
    seed = int(hashlib.md5(today.encode()).hexdigest(), 16)
    idx = seed % 3
    return DAILY_LINES_TR.get(element_tr, ["Bugün merkezde kal."])[idx]

def analyze_data(name, dob, time, place):
    d = dateparse.parse(dob).date()
    sign = sun_sign(d)
    element, modality = ELEMENTS.get(sign,""), MODALITY.get(sign,"")
    lp = life_path(d)
    nums = {
        "Yaşam Yolu": lp,
        "Kader": number_from_name(name,"all"),
        "Ruh": number_from_name(name,"vowels"),
        "Kişilik": number_from_name(name,"consonants")
    }
    bio = biorhythm(d)
    cz = chinese_zodiac(d.year)
    ms = milestones(d)
    day_tip = daily_horoscope(element)

    return {
        "Astroloji": {"burc": sign, "element": element, "modalite": modality},
        "Numeroloji": nums,
        "Biyoritim": bio,
        "Yaş & Dönüm Noktaları": ms,
        "Çin Burcu": cz,
        "Günlük": day_tip
    }

# ---- ROUTES ----
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/analyze", methods=["POST"])
def api_analyze():
    data = request.get_json()
    name  = data.get("name","Misafir")
    dob   = data.get("dob")
    time  = data.get("time","00:00")
    place = data.get("place","Bilinmiyor")
    result = analyze_data(name, dob, time, place)
    return jsonify({"ok":True, "data":result})

# ---- ERROR HANDLER ----
@app.errorhandler(404)
def page_not_found(e):
    return jsonify({"ok": False, "error": "404 - route not found"}), 404

# ---- RUN ----
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
