# 🚀 PLESK'TE FLASK UYGULAMASI DEPLOY ETME

## 📌 PLESK NEDİR?
Plesk = VPS kontrol paneli (cPanel gibi) + SSH erişimi var = Python desteklenir!

---

## ✅ ADIM 1: SSH BÜTÜNLEŞTİRMEYİ KONTROLet

### Plesk'te SSH aktif mi?
1. **Plesk Paneline gir** → `enisakada.com.tr:8443`
2. **Tools & Settings** (Sol menü)
3. **SSH Access** → Aktivasyon kontrol et

### Komut satırında test et:
```bash
ssh -p 22 kullanici@enisakada.com.tr
# ya da
ssh -p 22 kullanici@IP_ADRES
```

---

## 📁 ADIM 2: PLESK'TE DOMAIN KLASÖRÜ

### Dosyalar nereye gider?
```
/var/www/vhosts/enisakada.com.tr/  ← Bu klasörde çalışacak
    ├── httpdocs/           (Web root - public_html gibi)
    ├── private/            (Gizli dosyalar)
    └── log/                (Loglar)
```

---

## 🐍 ADIM 3: PYTHON KURULUMU

### SSH'ye bağlan:
```bash
ssh kullanici@enisakada.com.tr
```

### Python 3 var mı kontrol et:
```bash
python3 --version
```

Yoksa (nadir), Plesk panelinden yükle:
- **Tools & Settings** → **Server Components** → Python 3 ekle

---

## 📦 ADIM 4: UYGULAMA DOSYALARINI UPLOAD ET

### Seçenek 1: SFTP ile Dosya Transfer

```bash
# Yerel bilgisayarında (macOS/Linux):
sftp kullanici@enisakada.com.tr

sftp> cd /var/www/vhosts/enisakada.com.tr/httpdocs

# Klasörü yükle
sftp> put -r dukkan/* .

sftp> exit
```

### Seçenek 2: Git Clone (SSH üzerinden)

```bash
ssh kullanici@enisakada.com.tr

cd /var/www/vhosts/enisakada.com.tr/httpdocs

# Git'i yükle (eğer yoksa)
sudo apt-get install git

# Repository'i clone et
git clone https://github.com/kullanici/dukkan.git .
```

---

## 🔐 ADIM 5: VIRTUAL ENVIRONMENT KURU

SSH'ye bağlıyken:

```bash
cd /var/www/vhosts/enisakada.com.tr/httpdocs

# Virtual environment oluştur
python3 -m venv venv

# Aktifleştir
source venv/bin/activate

# Paketleri yükle
pip install --upgrade pip
pip install flask flask-sqlalchemy gunicorn

# Gerekli paketleri requirements.txt'ten yükle
pip install -r requirements.txt
```

---

## 🌐 ADIM 6: PLESK'TE PROXY AYARLA

### Plesk Paneline gir: https://enisakada.com.tr:8443

1. **Sol menü** → **enisakada.com.tr** seç
2. **Hosting Settings** klik
3. Aşağıya scroll et → **nginx & Apache Settings**

#### Opsyon 1: Node.js Application (Alternatif)
```
1. Web Applications → Add
2. App path: /var/www/vhosts/enisakada.com.tr/httpdocs
3. Startup file: gunicorn_app.py
```

#### Opsyon 2: Ters Proxy (Önerilen)
1. **Addons** → **Nginx** açık mı kontrol et (genelde açık)
2. **Hosting Settings** → **Nginx Settings**
3. Aşağıdaki kodu ekle:

```nginx
location / {
    proxy_pass http://127.0.0.1:5055;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}

location /static/ {
    alias /var/www/vhosts/enisakada.com.tr/httpdocs/static/;
}
```

**Kaydet** → **OK**

---

## 🚀 ADIM 7: GUNICORN'U BAŞLAT

SSH'ye bağlıyken:

```bash
cd /var/www/vhosts/enisakada.com.tr/httpdocs

source venv/bin/activate

# Test çalıştırması
gunicorn -w 4 -b 127.0.0.1:5055 app:app
```

Çıktı görülüyor mu? (Listening on 127.0.0.1:5055)

**Evet** → Ctrl+C ile dur ve devam et

---

## ⚙️ ADIM 8: SYSTEMD SERVİSİ (Otomatik Başlatma)

### Servis dosyası oluştur:

```bash
sudo nano /etc/systemd/system/dukkan.service
```

Şunu yapıştır:

```ini
[Unit]
Description=Dükkan Flask Application
After=network.target

[Service]
Type=notify
User=psacln
Group=psacln
WorkingDirectory=/var/www/vhosts/enisakada.com.tr/httpdocs
Environment="PATH=/var/www/vhosts/enisakada.com.tr/httpdocs/venv/bin"
ExecStart=/var/www/vhosts/enisakada.com.tr/httpdocs/venv/bin/gunicorn \
    --workers 4 \
    --bind 127.0.0.1:5055 \
    --timeout 120 \
    app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Not:** `psacln` yerine gerçek Plesk kullanıcısını gir:
```bash
whoami  # Komutla bak
```

### Servis'i etkinleştir:

```bash
sudo systemctl daemon-reload
sudo systemctl enable dukkan
sudo systemctl start dukkan
sudo systemctl status dukkan
```

Çıktı:
```
● dukkan.service - Dükkan Flask Application
   Loaded: loaded (/etc/systemd/system/dukkan.service)
   Active: active (running)
```

✅ Çalışıyor!

---

## 🔒 ADIM 9: SSL/HTTPS (Let's Encrypt)

### Plesk'te otomatik:

1. **Plesk Paneline gir**
2. **enisakada.com.tr** seç
3. **Security** → **SSL/TLS Certificate**
4. **Install** → Let's Encrypt seç
5. **Install Certificate**

Veya komut satırında:
```bash
sudo plesk sbin certificate_deployer \
  --install-certificate enisakada.com.tr letsencrypt
```

---

## ✅ ADIM 10: TEST ET

### Tarayıcıda aç:
```
https://enisakada.com.tr
```

### Tablet/Telefon'dan:
```
https://enisakada.com.tr
```

---

## 📋 PRODUCTION AYARLARI

### app.py kontrol et:

```python
# ❌ Yoksa (debug True):
if __name__ == "__main__":
    app.run(debug=True)

# ✅ Düzelt (debug False):
if __name__ == "__main__":
    app.run(debug=False)
```

### .env dosyası:

```bash
cd /var/www/vhosts/enisakada.com.tr/httpdocs

nano .env
```

İçeriği:
```
FLASK_ENV=production
SECRET_KEY=super-gizli-anahtar-isimleri-burada-olustur
DATABASE_URL=sqlite:////var/www/vhosts/enisakada.com.tr/httpdocs/dukkan.db
```

### app.py'de oku:

```python
import os
from dotenv import load_dotenv

load_dotenv()

app.secret_key = os.getenv("SECRET_KEY", "fallback-key")
os.environ["FLASK_ENV"] = "production"
```

---

## 📊 MONİTÖRİNG

### Servis durumu:
```bash
sudo systemctl status dukkan
```

### Live log:
```bash
sudo journalctl -u dukkan -f
```

### Nginx hatası:
```bash
tail -f /var/log/nginx/enisakada.com.tr.error.log
tail -f /var/log/nginx/enisakada.com.tr.access.log
```

### CPU/RAM:
```bash
htop
```

---

## 🐛 SORUN GIDERME

### 502 Bad Gateway
```bash
# Gunicorn açılmış mı?
sudo systemctl status dukkan

# Port 5055 kullanılıyor mu?
lsof -i :5055

# Başlat
sudo systemctl restart dukkan
```

### 404 Statik dosyalar yüklenmedi
```bash
# Nginx yapılandırması doğru mu?
sudo nginx -t

# Dosya yetkisi:
sudo chown -R psacln:psacln /var/www/vhosts/enisakada.com.tr/httpdocs/static/
```

### Database hatası
```bash
# Dosya yetkisi:
sudo chown psacln:psacln /var/www/vhosts/enisakada.com.tr/httpdocs/dukkan.db
```

### Import hatası (modül bulunamadı)
```bash
source /var/www/vhosts/enisakada.com.tr/httpdocs/venv/bin/activate
pip list  # Tüm paketler yüklü mü?
```

---

## 🔄 GÜNCELLEME (Yeni versiyon deploy etme)

### Git'ten pull:
```bash
cd /var/www/vhosts/enisakada.com.tr/httpdocs
source venv/bin/activate
git pull origin main
pip install -r requirements.txt
```

### Servis'i yeniden başlat:
```bash
sudo systemctl restart dukkan
```

---

## 📈 PLESK'TE BACKUP

### Plesk Panelinde:
1. **Backup Manager**
2. **Backup Repositories**
3. **Automatic Backups** kur (günlük)

SSH'den manuel backup:
```bash
tar -czf ~/dukkan_backup_$(date +%Y%m%d).tar.gz \
  /var/www/vhosts/enisakada.com.tr/httpdocs/
```

---

## 🎯 ÖZETİ

| Adım | Komut |
|------|-------|
| 1. SSH bağlan | `ssh kullanici@enisakada.com.tr` |
| 2. Dosyaları upload | `sftp` veya `git clone` |
| 3. Virtual env | `python3 -m venv venv && source venv/bin/activate` |
| 4. Paketleri yükle | `pip install -r requirements.txt` |
| 5. Servis oluştur | `sudo nano /etc/systemd/system/dukkan.service` |
| 6. Proxy yapılandır | Plesk Panel → Nginx Settings |
| 7. SSL ekle | Plesk Panel → Let's Encrypt |
| 8. Test et | https://enisakada.com.tr |

---

## ❓ SORUN YAŞARSAN

**Hata mesajını gösterebilirsin:**
```bash
sudo journalctl -u dukkan -n 50
```

Çıktıyı göster, yardım edebilirim!

**Başarısı!** 🚀
