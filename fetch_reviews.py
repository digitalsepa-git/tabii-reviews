"""
Tabii App Store Yorum Çekici
- App Store Connect API'den tüm yorumları çeker
- reviews.json dosyasıyla karşılaştırır, yenileri Slack'e gönderir
- Güncel yorum listesini reviews.json'a yazar
"""
import os
import json
import time
import requests
import jwt
from datetime import datetime

# === KONFİG (GitHub Secrets'tan gelir) ===
ISSUER_ID = os.environ["ASC_ISSUER_ID"]
KEY_ID = os.environ["ASC_KEY_ID"]
PRIVATE_KEY = os.environ["ASC_PRIVATE_KEY"]
APP_ID = os.environ["ASC_APP_ID"]
SLACK_WEBHOOK = os.environ.get("SLACK_WEBHOOK_URL", "")

REVIEWS_FILE = "reviews.json"

# Ülke kodu çevirisi
COUNTRY = {
    "TUR": "🇹🇷 Türkiye", "DEU": "🇩🇪 Almanya", "USA": "🇺🇸 ABD",
    "GBR": "🇬🇧 İngiltere", "NLD": "🇳🇱 Hollanda", "FRA": "🇫🇷 Fransa",
    "AUT": "🇦🇹 Avusturya", "BEL": "🇧🇪 Belçika", "ARE": "🇦🇪 BAE",
    "SAU": "🇸🇦 Suudi Arabistan", "QAT": "🇶🇦 Katar", "DNK": "🇩🇰 Danimarka",
    "SWE": "🇸🇪 İsveç", "NOR": "🇳🇴 Norveç", "CHE": "🇨🇭 İsviçre",
    "AZE": "🇦🇿 Azerbaycan", "CAN": "🇨🇦 Kanada", "ITA": "🇮🇹 İtalya",
    "ESP": "🇪🇸 İspanya", "POL": "🇵🇱 Polonya", "ROU": "🇷🇴 Romanya",
    "BGR": "🇧🇬 Bulgaristan", "HUN": "🇭🇺 Macaristan", "CZE": "🇨🇿 Çekya",
    "GRC": "🇬🇷 Yunanistan", "EGY": "🇪🇬 Mısır", "RUS": "🇷🇺 Rusya",
    "UKR": "🇺🇦 Ukrayna", "KAZ": "🇰🇿 Kazakistan", "UZB": "🇺🇿 Özbekistan",
    "MKD": "🇲🇰 K.Makedonya", "ALB": "🇦🇱 Arnavutluk", "XKX": "🇽🇰 Kosova",
    "IRQ": "🇮🇶 Irak", "ISR": "🇮🇱 İsrail", "JOR": "🇯🇴 Ürdün",
    "KWT": "🇰🇼 Kuveyt", "LBN": "🇱🇧 Lübnan", "MAR": "🇲🇦 Fas",
    "DZA": "🇩🇿 Cezayir", "AUS": "🇦🇺 Avustralya",
}


def get_token():
    now = int(time.time())
    return jwt.encode(
        {"iss": ISSUER_ID, "iat": now, "exp": now + 1200, "aud": "appstoreconnect-v1"},
        PRIVATE_KEY, algorithm="ES256", headers={"kid": KEY_ID}
    )


def fetch_all_reviews():
    """API'den tüm yorumları çeker (en yeniden eskiye)."""
    headers = {"Authorization": f"Bearer {get_token()}"}
    reviews = []
    url = f"https://api.appstoreconnect.apple.com/v1/apps/{APP_ID}/customerReviews"
    params = {"limit": 200, "sort": "-createdDate"}

    while url:
        r = requests.get(url, headers=headers, params=params, timeout=30)
        if r.status_code != 200:
            print(f"API hatası: {r.status_code} {r.text[:300]}")
            break
        d = r.json()
        for item in d.get("data", []):
            a = item["attributes"]
            reviews.append({
                "id": item["id"],
                "date": a.get("createdDate", "")[:19],
                "rating": a.get("rating", 0),
                "title": a.get("title", "") or "",
                "body": a.get("body", "") or "",
                "nickname": a.get("reviewerNickname", "") or "",
                "territory": a.get("territory", "") or "",
            })
        url = d.get("links", {}).get("next")
        params = {}
        print(f"  {len(reviews)} yorum çekildi...")

    return reviews


def post_to_slack(review):
    """Bir yorumu Slack'e kart olarak gönderir."""
    if not SLACK_WEBHOOK:
        return

    rating = review["rating"]
    stars = "⭐" * rating + "☆" * (5 - rating)
    color = "#28a745" if rating >= 4 else ("#ffc107" if rating == 3 else "#dc3545")
    country = COUNTRY.get(review["territory"], review["territory"])
    title = review["title"] or "(başlıksız)"
    body = review["body"] or "(içerik yok)"
    if len(body) > 600:
        body = body[:600] + "…"

    try:
        date_obj = datetime.fromisoformat(review["date"])
        date_str = date_obj.strftime("%d %b %Y %H:%M")
    except Exception:
        date_str = review["date"][:10]

    payload = {
        "attachments": [{
            "color": color,
            "blocks": [
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": f"{stars}  {title}"[:150]}
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": body}
                },
                {
                    "type": "context",
                    "elements": [{
                        "type": "mrkdwn",
                        "text": f"*{review['nickname']}* • {country} • {date_str}"
                    }]
                }
            ]
        }]
    }
    try:
        r = requests.post(SLACK_WEBHOOK, json=payload, timeout=10)
        if r.status_code != 200:
            print(f"  Slack hatası: {r.status_code} {r.text[:200]}")
    except Exception as e:
        print(f"  Slack istisnası: {e}")


def load_existing():
    """Önceki çalışmadaki yorum ID'lerini yükler."""
    if not os.path.exists(REVIEWS_FILE):
        return set(), []
    with open(REVIEWS_FILE) as f:
        data = json.load(f)
    existing = data.get("reviews", [])
    return {r["id"] for r in existing}, existing


def main():
    print("Yorumlar çekiliyor...")
    all_reviews = fetch_all_reviews()
    print(f"Toplam {len(all_reviews)} yorum API'den geldi.")

    existing_ids, existing_list = load_existing()
    print(f"Önceki kayıtta {len(existing_ids)} yorum var.")

    # Yeni yorumları bul (eski → yeni sırayla Slack'e gönder)
    new_reviews = [r for r in all_reviews if r["id"] not in existing_ids]
    new_reviews.sort(key=lambda x: x["date"])

    print(f"{len(new_reviews)} yeni yorum bulundu.")

    if existing_ids and new_reviews:  # ilk çalışmada Slack spam etmesin
        for r in new_reviews:
            post_to_slack(r)
            time.sleep(0.5)
        print(f"{len(new_reviews)} yorum Slack'e gönderildi.")
    elif not existing_ids:
        print("İlk çalışma — Slack'e gönderim atlandı (spam önleme).")

    # JSON'u güncelle
    output = {
        "updated_at": datetime.utcnow().isoformat() + "Z",
        "total": len(all_reviews),
        "reviews": all_reviews,
    }
    with open(REVIEWS_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"{REVIEWS_FILE} güncellendi.")


if __name__ == "__main__":
    main()
