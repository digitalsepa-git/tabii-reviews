# Tabii — App Store Yorum Takibi

App Store Connect API'den Tabii uygulamasının yorumlarını çeker, yenileri Slack'e gönderir ve web arayüzünde görselleştirir.

## Mimari

```
┌────────────────────┐    ┌─────────────────┐    ┌─────────────┐
│ App Store Connect  │──▶ │ GitHub Actions  │──▶ │ Slack Kanal │
│       API          │    │  (her gün 09:00)│    └─────────────┘
└────────────────────┘    └────────┬────────┘
                                   │
                                   ▼
                          ┌─────────────────┐    ┌─────────────┐
                          │  reviews.json   │──▶ │ GitHub Pages│
                          │   (repo'da)     │    │  (web UI)   │
                          └─────────────────┘    └─────────────┘
```

## Kurulum (10 dakika)

### 1. GitHub Repo'sunu hazırla

1. GitHub'da yeni bir **private** repository aç (örn: `tabii-reviews`)
2. Bu klasördeki tüm dosyaları repoya yükle:
   - `fetch_reviews.py`
   - `requirements.txt`
   - `index.html`
   - `reviews.json` (4,167 yorumla başlangıç verisi)
   - `.github/workflows/fetch.yml`
   - `README.md`

### 2. Slack Webhook URL'i al

1. Slack'te yorum kanalı aç: `#tabii-yorumlar`
2. https://api.slack.com/apps → **Create New App** → **From scratch**
3. App adı: "Tabii Reviews", workspace seç
4. **Incoming Webhooks** → açık konuma getir
5. **Add New Webhook to Workspace** → `#tabii-yorumlar` kanalını seç
6. Çıkan URL'yi kopyala (`https://hooks.slack.com/services/T.../B.../...`)

### 3. GitHub Secrets'ı ayarla

Repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

Beş secret ekle:

| Secret Adı | Değer |
|---|---|
| `ASC_ISSUER_ID` | `69a6de75-5b5c-47e3-e053-5b8c7c11a4d1` |
| `ASC_KEY_ID` | `RCJ6KG7R72` |
| `ASC_PRIVATE_KEY` | `AuthKey_RCJ6KG7R72.p8` dosyasının **tam içeriği** (BEGIN/END satırları dahil) |
| `ASC_APP_ID` | `1668441657` |
| `SLACK_WEBHOOK_URL` | Adım 2'de aldığın webhook URL |

### 4. İlk çalıştırma (manuel test)

Repo → **Actions** sekmesi → **Yorumları Çek** workflow → **Run workflow** butonu

Birkaç saniye sonra tamamlanır. İlk çalışmada Slack spam etmemek için bildirimler atlanır — sadece `reviews.json` güncellenir. İkinci çalıştırmadan itibaren yeni yorumlar Slack'e düşmeye başlar.

### 5. Web arayüzü için GitHub Pages

Repo → **Settings** → **Pages**
- **Source:** Deploy from a branch
- **Branch:** `main` / `(root)` → **Save**

Birkaç dakika sonra şuradan erişebilirsin:
`https://[kullanıcı-adın].github.io/tabii-reviews/`

## Otomatik Çalışma

Workflow her gün **sabah 09:00 (İstanbul)** otomatik çalışır. Yeni yorumları Slack'e atar ve `reviews.json`'ı günceller. Web arayüzü her ziyarette en son JSON'u okur.

## Manuel Tetikleme

İstediğin zaman: Actions → **Yorumları Çek** → **Run workflow**

## Sorun Giderme

- **Slack mesajı gelmedi:** Workflow log'larında `Slack hatası` arayın. Webhook URL'sinin doğru olduğundan emin olun.
- **Workflow hata verdi:** Actions sekmesinde kırmızı runın üstüne tıklayın, log'a bakın. En sık sebep: ASC_PRIVATE_KEY'in eksik kopyalanması (BEGIN/END satırlarını dahil etmediniz).
- **Web arayüzü boş:** Tarayıcı konsolunda hata var mı bakın. `reviews.json` dosyasının repo'da olduğunu doğrulayın.

## Geliştirme Fikirleri

- Sadece düşük puanlı yorumları Slack'e at (3★ ve altı)
- Slack mesajına "Cevap yaz" butonu (App Store Connect linkiyle)
- Negatif yorumlarda anahtar kelime trendi (haftalık özet)
- E-posta özeti (her Pazartesi, geçen haftanın özeti)
- Çoklu uygulama desteği (aynı script, birden fazla app)
