from flask import Flask, render_template, request, jsonify
from datetime import date, timedelta
from dateutil import parser as dateparse
import math, re, hashlib
import swisseph as swe

app = Flask(__name__, template_folder="templates", static_folder="static")

# ---- Astro hesaplamaları ----
ZODIAC_SIGNS_TR = [
    "Koç","Boğa","İkizler","Yengeç","Aslan","Başak",
    "Terazi","Akrep","Yay","Oğlak","Kova","Balık"
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

def get_sun_sign(dob):
    # Swiss Ephemeris ile burç hesapla
    d = dateparse.parse(dob).date()
    jd = swe.julday(d.year, d.month, d.day)
    lon, lat, dist, lon_speed = swe.calc_ut(jd, swe.SUN)
    sign_index = int(lon // 30)
    return ZODIAC_SIGNS_TR[sign_index]

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
    pool = [c for c in clean if (pick=="vowels" and c in "aeiou") or (pick=="consonants" and c not in "aeiou") or (pick=="all")]
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

def daily_tip(element):
    tips = {
        "Ateş": "Cesur ol, liderlik bugün senden parlıyor.",
        "Toprak": "Sabırlı ol, istikrarın seni büyütecek.",
        "Hava": "Zihnini aç, yeni fikirler seni bulacak.",
        "Su": "Sezgine güven, kalbin seni doğru yere götürür."
    }
    return tips.get(element,"Bugün merkezde kal.")

def dobly_comment(sign, element, bio):
    top = max(bio, key=bio.get)
    return f"Dobly diyor ki 🐾 {sign} burcu olarak {element.lower()} enerjindesin. Bugün {top.lower()} kanalında güçlü hissediyorsun — bunu değerlendir!"

# ---- Ana analiz ----
def analyze_data(name, dob, time, place, lang="tr"):
    dob = dob.replace(".", "-")
    d = dateparse.parse(dob).date()
    sign = get_sun_sign(dob)
    element = ELEMENTS.get(sign, "")
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
    day_tip = daily_tip(element)
    comment = dobly_comment(sign, element, bio)

    return {
        "Burç": sign,
        "Element": element,
        "Numeroloji": nums,
        "Biyoritim": bio,
        "Çin": cz,
        "Dönüm": ms,
        "Yorum": day_tip,
        "Dobly": comment
    }

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/analyze", methods=["POST"])
def api_analyze():
    data = request.get_json()
    name = data.get("name","Misafir")
    dob = data.get("dob")
    time = data.get("time","00:00")
    place = data.get("place","Bilinmiyor")
    lang = data.get("lang","tr")
    result = analyze_data(name, dob, time, place, lang)
    return jsonify({"ok":True, "data":result})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
