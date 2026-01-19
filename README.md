# Dükkan (MVP)

Günlük gelir/gider takibi + ciro raporu (günlük/aylık/yıllık).

## Hızlı Başlangıç

```bash
cd /Users/enisbugra/Desktop/Dukkan
source .venv/bin/activate
python app.py
```

Tarayıcıdan aç: **http://127.0.0.1:5055** veya **http://localhost:5055**

## İlk Kurulum (sadece bir kez)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Ekranlar
- Günlük Giriş: `daily_entry` tablosuna bugüne ait nakit/kart gelir girilir. Toplam otomatik.
- Giderler: Liste + yeni gider ekleme (kategori, ödeme tipi).
- Rapor: Toplam gelir/gider/net ve nakit/kart dağılımı.

## Notlar
- `daily_entry.date` tektir (UNIQUE). Aynı gün yeniden kaydetmek "güncelleme" etkisi yaratır.
- `income` tablosu mevcuttur ama MVP ekranlarında kullanılmamaktadır; istenirse ekstra gelir/düzeltme amacıyla eklenebilir.
- Veritabanı dosyası: `dukkan.db` (SQLite).
