from flask import Flask, render_template, request, jsonify
from datetime import datetime
import math, random

app = Flask(__name__)

# ------------------ Yardımcı Fonksiyonlar ------------------ #
def hesapla_burc(gun, ay):
    burclar = [
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
        ("Yay", (11, 22), (12, 21)),
    ]
    for burc, (a1, g1), (a2, g2) in burclar:
        if (ay == a1 and gun >= g1) or (ay == a2 and gun <= g2):
            return burc
    return "Oğlak"

def element(burc):
    ates = ["Koç", "Aslan", "Yay"]
    toprak = ["Boğa", "Başak", "Oğlak"]
    hava = ["İkizler", "Terazi", "Kova"]
    su = ["Yengeç", "Akrep", "Balık"]
    if burc in ates: return "Ateş"
    if burc in toprak: return "Toprak"
    if burc in hava: return "Hava"
    if burc in su: return "Su"
    return "Bilinmiyor"

def biyoritim(birthdate):
    days = (datetime.now().date() - birthdate).days
    fiziksel = int((math.sin(2 * math.pi * days / 23) + 1) * 50)
    duygusal = int((math.sin(2 * math.pi * days / 28) + 1) * 50)
    zihinsel = int((math.sin(2 * math.pi * days / 33) + 1) * 50)
    return {"Fiziksel": fiziksel, "Duygusal": duygusal, "Zihinsel": zihinsel}

def numeroloji_ad(isim):
    toplam = sum(ord(c.lower()) - 96 for c in isim if c.isalpha())
    while toplam > 9:
        toplam = sum(int(x) for x in str(toplam))
    return toplam

def yas_donum(birthdate):
    yas = datetime.now().year - birthdate.year
    milestone = yas % 7
    return f"{yas} yaşındasın. Şu anda {milestone}. enerji döngüsündesin."

def cinsayisi(yil):
    hayvanlar = ["Fare","Öküz","Kaplan","Tavşan","Ejderha","Yılan","At","Keçi","Maymun","Horoz","Köpek","Domuz"]
    return hayvanlar[yil % 12]

def dobly_mesaji(burc, element_):
    mesajlar = {
        "Ateş": f"{burc} — cesur ol, yeni başlangıç seni bekliyor!",
        "Toprak": f"{burc} — sabırlı ol, istikrarlı ilerle!",
        "Hava": f"{burc} — yaratıcı fikirlerini paylaş!",
        "Su": f"{burc} — sezgilerine güven!"
    }
    oneriler = {
        "Ateş": "Net bir hedef seç ve küçük adımlarla ilerle.",
        "Toprak": "Bugün plan yap ve disiplinden ödün verme.",
        "Hava": "Yeni insanlarla iletişime geç.",
        "Su": "Meditasyon veya doğa yürüyüşü sana iyi gelir."
    }
    return mesajlar.get(element_, ""), oneriler.get(element_, "")

# ------------------ Rotalar ------------------ #
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/analyze", methods=["POST"])
def analyze():
    data = request.json
    try:
        name = data.get("name", "Anonim")
        dob_str = data.get("dob")
        birthdate = datetime.strptime(dob_str, "%Y-%m-%d").date()
        gun, ay, yil = birthdate.day, birthdate.month, birthdate.year
        burc = hesapla_burc(gun, ay)
        element_ = element(burc)
        bio = biyoritim(birthdate)
        num = numeroloji_ad(name)
        yas_dnm = yas_donum(birthdate)
        cin = cinsayisi(yil)
        mesaj, oner = dobly_mesaji(burc, element_)

        result = {
            "ok": True,
            "data": {
                "lang": data.get("lang", "tr"),
                "Günlük": {"text": f"{element_} elementi: {burc} — {name}, bugün enerji akışın yüksek!"},
                "Biyoritim": bio,
                "Astroloji": {"text": f"{burc} burcu ({element_} elementi). Duygularına kulak ver."},
                "Numeroloji": {"Yaşam Yolu": num, "Kader": num + 2, "Ruh": num + 3, "Kişilik": num + 4, "text": "İçsel dengen bu hafta güçleniyor."},
                "Yaş & Dönüm Noktaları": {"text": yas_dnm},
                "Çin Burcu": {"text": cin},
                "Yorum": mesaj,
                "Öneri": oner
            }
        }
        return jsonify(result)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

if __name__ == "__main__":
    app.run(debug=True)
