"""
Tek seferlik: Son N günün yorumlarını Slack'e gönderir.
fetch_reviews.py'dan ödünç alınan yardımcı fonksiyonları kullanır.
"""
import os, time
from datetime import datetime, timedelta, timezone
from fetch_reviews import fetch_all_reviews, post_to_slack

DAYS = int(os.environ.get("BACKFILL_DAYS", "7"))

print(f"Son {DAYS} günün yorumları çekiliyor...")
reviews = fetch_all_reviews()
print(f"Toplam {len(reviews)} yorum API'den geldi.")

cutoff = datetime.now(timezone.utc) - timedelta(days=DAYS)
recent = []
for r in reviews:
    try:
        d = datetime.fromisoformat(r["date"]).replace(tzinfo=timezone.utc) \
            if "+" not in r["date"] else datetime.fromisoformat(r["date"])
        if d >= cutoff:
            recent.append(r)
    except Exception:
        pass

# Eskiden yeniye sırala (Slack'te kronolojik aksın)
recent.sort(key=lambda x: x["date"])
print(f"Son {DAYS} günde {len(recent)} yorum bulundu, Slack'e gönderiliyor...")

for r in recent:
    post_to_slack(r)
    time.sleep(0.6)

print(f"Tamamlandı: {len(recent)} yorum gönderildi.")
