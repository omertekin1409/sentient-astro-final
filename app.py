from flask import Flask, render_template, request, jsonify
from datetime import date, datetime, timedelta
from dateutil import parser as dateparse
import math, re, hashlib

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
    # basit rehber metni
    text = f"Yaş: {years} • Gün: {days} • Sonraki 10K gün: {next_10k_date.isoformat()}."
    return {"Yaş":years,"Gün":days,"Sonraki10K":next_10k_date.isoformat(),"text":text}

# ---- Günlük burç yorumu (seed'li liste; her gün değişen kısa rehber) ----
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
DAILY_LINES_EN = {
    "Fire": [
        "Initiate boldly; even a tiny spark becomes a flame.",
        "Set the pace; swift clarity leads to clean results.",
        "Aim your passion; focus turns heat into power."
    ],
    "Earth": [
        "Make it tangible; structure multiplies progress.",
        "Small, steady steps compound today.",
        "Simplify your resources; clarity boosts output."
    ],
    "Air": [
        "Share your idea; connections unlock doors.",
        "Ask questions; curiosity finds the path.",
        "Quiet the mind; the best ideas arrive in stillness."
    ],
    "Water": [
        "Trust intuition; your heart is a compass.",
        "Give your feelings space; softness is strength.",
        "Breathe deeply; stay in flow, accept and move."
    ]
}

def daily_horoscope(element_tr: str, lang="tr"):
    today = date.today().isoformat()
    seed = int(hashlib.md5(today.encode()).hexdigest(), 16)
    idx = seed % 3
    if lang == "tr":
        return DAILY_LINES_TR.get(element_tr, ["Bugün merkezde kal."])[idx]
    # map TR element to EN
    map_en = {"Ateş":"Fire","Toprak":"Earth","Hava":"Air","Su":"Water"}
    element_en = map_en.get(element_tr, "Air")
    return DAILY_LINES_EN.get(element_en, ["Stay centered today."])[idx]

# ---- Ana analiz ----
def analyze_data(name, dob, time, place, lang="tr"):
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
    day_tip = daily_horoscope(element, lang)

    # Daha uzun & vurucu yorum
    if lang == "tr":
        astro_text = f"Güneş {sign} • Element {element} • Modalite {modality}. Bu karışım, karar alma biçimini ve dış dünyaya açılma hızını belirginleştirir."
        num_text = f"Yaşam Yolu {nums['Yaşam Yolu']} uzun hikâyeni yönlendirir; Kader {nums['Kader']} dışarıdan nasıl algılandığını; Ruh {nums['Ruh']} içten gelen arzunu; Kişilik {nums['Kişilik']} ilk izlenimini renklendirir."
        bio_text = f"Fiziksel {bio['Fiziksel']}% • Duygusal {bio['Duygusal']}% • Zihinsel {bio['Zihinsel']}%. Yüksek olan kanalı günün kritik işlerine ayır."
        cz_text = f"{cz['Element']} {cz['Hayvan']}. Doğanın ritmiyle uyumlandığında fırsatlar daha görünür olur."
        day_text = f"Günlük Burç Yorumu: {day_tip}"
        sentient = (
            f"{name}, {place} doğumlu; {sign} doğası sende cesaret ve {element.lower()} unsuru ile "
            f"pratik sezgiyi birleştiriyor. Bugün ‘netlik→eylem’ zincirine odaklan: önce 1 net karar, "
            f"ardından 20 dakikalık kesintisiz uygulama. Yorulduğunda kısa bir nefes, sonra devam. "
            f"Ruhsal ritmin {max(bio, key=bio.get)} kanalında güçlü; bunu avantaja çevir."
        )
        recommendation = "Sentient diyor ki: Bugün tek cesur adım at — küçük ama tamamlanmış bir iş, büyük bir ivme yaratır."
        return {
            "lang":"tr",
            "Astroloji": {"burc": sign, "element": element, "modalite": modality, "text": astro_text},
            "Numeroloji": nums | {"text": num_text},
            "Biyoritim": bio | {"text": bio_text},
            "Yaş & Dönüm Noktaları": ms,
            "Çin Burcu": cz | {"text": cz_text},
            "Günlük": {"text": day_text},
            "Yorum": sentient,
            "Öneri": recommendation
        }
    else:
        # EN
        map_en = {"Ateş":"Fire","Toprak":"Earth","Hava":"Air","Su":"Water"}
        element_en = map_en.get(element, element)
        modality_en = {
            "Öncü":"Cardinal","Sabit":"Fixed","Değişken":"Mutable"
        }.get(modality, modality)
        astro_text = f"Sun in {sign} • Element {element_en} • Modality {modality_en}. This blend shapes how you choose, start, and sustain momentum."
        num_text = f"Life Path {nums['Yaşam Yolu']} guides your arc; Destiny {nums['Kader']} your outer role; Soul {nums['Ruh']} inner desire; Personality {nums['Kişilik']} first impression."
        bio_text = f"Physical {bio['Fiziksel']}% • Emotional {bio['Duygusal']}% • Intellectual {bio['Zihinsel']}%. Allocate key tasks to your strongest channel."
        cz_en = {"Hayvan":"Animal","Element":"Element"}
        cz_text = f"{cz['Element']} {cz['Hayvan']}."
        day_text = f"Daily Horoscope: {day_tip}"
        sentient = (
            f"{name} from {place}: your {sign} nature blends courage with {element_en.lower()} essence. "
            f"Focus on the chain ‘clarity→action’: one crisp decision then 20 minutes of undistracted doing. "
            f"Pause, breathe, resume. Your strongest channel today is {max(bio, key=bio.get)} — leverage it."
        )
        recommendation = "Sentient suggests: take one bold, finishable step — small done beats big pending."
        return {
            "lang":"en",
            "Astrology": {"sign": sign, "element": element_en, "modality": modality_en, "text": astro_text},
            "Numerology": {"Life Path": nums["Yaşam Yolu"], "Destiny": nums["Kader"], "Soul": nums["Ruh"], "Personality": nums["Kişilik"], "text": num_text},
            "Biorhythm": {"Physical": bio["Fiziksel"], "Emotional": bio["Duygusal"], "Intellectual": bio["Zihinsel"], "text": bio_text},
            "Age & Milestones": {"Age": ms["Yaş"], "Days": ms["Gün"], "Next10K": ms["Sonraki10K"], "text": f"Age: {ms['Yaş']} • Days: {ms['Gün']} • Next 10K day: {ms['Sonraki10K']}."},
            "Chinese Zodiac": {"Animal": cz["Hayvan"], "Element": cz["Element"], "text": cz_text},
            "Daily": {"text": day_text},
            "Insight": sentient,
            "Suggestion": recommendation
        }

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
    lang  = data.get("lang","tr")
    result = analyze_data(name, dob, time, place, lang)
    return jsonify({"ok":True, "data":result})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

