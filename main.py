import feedparser
import time
import requests
from bs4 import BeautifulSoup
import re
import json
import os
import random

# ============================
#   CONFIG (Render variables)
# ============================

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

def send_telegram_message(text: str):
    """Envoie un message dans Telegram."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, data=payload, timeout=10)
    except:
        pass


# ============================
#   MOTS CLES POSITIFS
# ============================

positive_keywords = {
    "ancien": 40, "très ancien": 50, "art nouveau": 50, "art deco": 50,
    "daum": 60, "gallé": 60, "lalique": 60, "baccarat": 55, "loetz": 55,
    "bronze": 50, "bronze d’art": 60, "statue": 40, "statuette": 40,
    "huile sur toile": 50, "peinture": 30, "peinture signée": 50,
    "gravure": 25, "lithographie": 30, "eau-forte": 35,
    "pâte de verre": 40, "verre soufflé": 30, "cristal": 35,
    "faience": 30, "porcelaine": 30, "terre cuite": 30,
    "céladon": 40, "imari": 40, "satsuma": 40, "kutani": 40,
    "monnaie": 30, "pièce argent": 40, "pièce or": 50, "napoleon": 45,
    "denier": 50, "sesterce": 50, "drachme": 50,
    "timbre": 30, "album timbre": 30, "timbre rare": 40,
    "bd ancien": 40, "tintin": 45, "hergé": 45, "asterix": 40,
    "jouet ancien": 35, "dinky": 35, "meccano": 35,
    "figurine": 30, "figurine plomb": 30,
    "militaria": 40, "ww1": 40, "ww2": 40,
    "casque": 40, "épée": 40, "baionnette": 40,
    "medaille": 40, "decoration": 40, "legion": 50,
    "art tribal": 50, "masque africain": 50, "statuette africain": 50,
    "objets de vitrine": 25, "curiosité": 40,
    "succession": 40, "grenier": 40, "vide maison": 35, "brocante": 20
}

# ============================
#   MOTS NEGATIFS (à éviter)
# ============================

negative_keywords = [
    "reproduction", "repro", "copie", "imitation", "fake",
    "style", "façon", "poster", "print", "giclee",
    "déco", "decoratif", "made in china",
    "résine", "zamak", "plastique",
    "look ancien", "vieilli artificiellement"
]


# ============================
#   FLUX LEBONCOIN (FRANCE)
# ============================

rss_feeds = [
    "https://www.leboncoin.fr/recherche?text=ancien&owner_type=private&sort=publication&limit=100&rss=1",
    "https://www.leboncoin.fr/recherche?text=bronze&owner_type=private&sort=publication&limit=100&rss=1",
    "https://www.leboncoin.fr/recherche?text=peinture&owner_type=private&sort=publication&limit=100&rss=1",
    "https://www.leboncoin.fr/recherche?text=bd%20ancienne&owner_type=private&sort=publication&limit=100&rss=1",
    "https://www.leboncoin.fr/recherche?text=faience&owner_type=private&sort=publication&limit=100&rss=1",
    "https://www.leboncoin.fr/recherche?text=porcelaine&owner_type=private&sort=publication&limit=100&rss=1",
    "https://www.leboncoin.fr/recherche?text=art%20tribal&owner_type=private&sort=publication&limit=100&rss=1",
    "https://www.leboncoin.fr/recherche?text=militaria&owner_type=private&sort=publication&limit=100&rss=1"
]


# ============================
#   ANTI-DOUBLON
# ============================

SEEN_FILE = "seen.json"

try:
    with open(SEEN_FILE, "r", encoding="utf-8") as f:
        seen_links = set(json.load(f))
except:
    seen_links = set()

def save_seen():
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(list(seen_links), f)


# ============================
#   ESTIMATION EBAY
# ============================

def estimate_value(search_term: str) -> int:
    url = f"https://www.ebay.fr/sch/i.html?_nkw={search_term}&LH_Sold=1&LH_Complete=1"
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
    except:
        return 0

    soup = BeautifulSoup(r.text, "lxml")

    prices = []
    for span in soup.select(".s-item__price"):
        txt = span.get_text(strip=True)
        price_digits = re.sub(r"[^\d]", "", txt)
        if price_digits.isdigit():
            prices.append(int(price_digits))

    if not prices:
        return 0

    return sum(prices) // len(prices)


# ============================
#   SCAN PRINCIPAL
# ============================

def scan_once():
    for feed in rss_feeds:
        time.sleep(random.uniform(1.0, 2.0))  # anti-ban

        d = feedparser.parse(feed)

        for entry in d.entries:
            title = entry.title.lower()
            desc = entry.description.lower() if hasattr(entry, "description") else ""
            link = entry.link

            if link in seen_links:
                continue

            # négatif
            if any(bad in title or bad in desc for bad in negative_keywords):
                continue

            # score positif
            score = 0
            for word, pts in positive_keywords.items():
                if word in title or word in desc:
                    score += pts

            if score < 40:
                continue

            price_match = re.search(r"(\d+)\s*€", entry.description)
            if not price_match:
                continue

            price = int(price_match.group(1))
            if price <= 0:
                continue

            est_value = estimate_value(entry.title)
            if est_value <= 0:
                continue

            ratio = est_value / price

            if ratio >= 10:
                txt = (
                    "🔥 *PÉPITE DÉTECTÉE !*\n"
                    f"*Titre* : {entry.title}\n"
                    f"*Prix* : {price} €\n"
                    f"*Valeur estimée* : {est_value} €\n"
                    f"*Multiplicateur* : x{round(ratio, 1)}\n"
                    f"{link}"
                )
                send_telegram_message(txt)

                seen_links.add(link)
                save_seen()


# ============================
#   LOOP 20 SECONDES
# ============================

send_telegram_message("🤖 Bot Chasseur de Trésors lancé ! Scan toutes les 20 sec.")

while True:
    scan_once()
    time.sleep(random.uniform(18, 25))  # interval 20 sec avg

