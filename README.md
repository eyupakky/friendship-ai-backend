# Friendship AI Backend

Kişilik analizi yapan AI destekli arkadaşlık eşleştirme uygulaması.

## Özellikler

- **Ücretsiz AI**: Ollama ile yerel LLM kullanır (internet gerektirmez)
- **Big Five Kişilik Analizi**: OCEAN modeliyle bilimsel kişilik profili
- **Akıllı Eşleştirme**: Kişilik uyumluluğuna göre arkadaş önerisi
- **Doğal Konuşma**: Samimi sohbet ile kişilik tespiti

## Kurulum

### 1. Ollama Kurulumu (Ücretsiz AI)

```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.com/install.sh | sh

# Model indir (1.3GB)
ollama pull llama3.2:1b
```

### 2. Projeyi Kur

```bash
git clone https://github.com/eyupakky/friendship-ai-backend.git
cd friendship-ai-backend

# Virtual environment (önerilen)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Bağımlılıkları yükle
pip install -r requirements.txt
```

### 3. Ollama'yı Başlat

```bash
ollama serve
```

## Kullanım

### Terminal Chat (Hızlı Test)

```bash
python chat.py
```

### API Sunucusu

```bash
python main.py
# veya
uvicorn main:app --reload
```

API Docs: http://localhost:8000/docs

## API Endpoint'leri

| Endpoint | Açıklama |
|----------|----------|
| `POST /api/v1/conversation/start` | Sohbet başlat |
| `POST /api/v1/conversation/message` | Mesaj gönder |
| `GET /api/v1/profile/{user_id}` | Profil getir |
| `GET /api/v1/matches/{user_id}` | Eşleşmeleri getir |

## Kişilik Modeli (Big Five / OCEAN)

| Özellik | Açıklama |
|---------|----------|
| **O**penness | Deneyime açıklık, yaratıcılık |
| **C**onscientiousness | Sorumluluk, düzen |
| **E**xtraversion | Dışadönüklük, sosyallik |
| **A**greeableness | Uyumluluk, empati |
| **N**euroticism | Duygusal hassasiyet |

## Nasıl Çalışır?

1. **Sohbet**: AI kullanıcıyla 30+ mesaj konuşur
2. **Analiz**: Her mesaj kişilik özellikleri için analiz edilir
3. **Profil**: Big Five skorları hesaplanır
4. **Eşleştirme**: Uyumlu profiller eşleştirilir

## Proje Yapısı

```
friendship-ai-backend/
├── main.py              # FastAPI uygulaması
├── chat.py              # Terminal chat scripti
├── requirements.txt     # Python bağımlılıkları
└── src/
    ├── models/
    │   ├── personality.py   # Kişilik modelleri
    │   └── database.py      # Veritabanı modelleri
    ├── services/
    │   ├── personality_analyzer.py  # Kişilik analizi
    │   ├── conversation_ai.py       # Sohbet AI
    │   └── matching_engine.py       # Eşleştirme
    ├── api/
    │   └── routes.py        # API endpoint'leri
    └── config/
        └── settings.py      # Ayarlar
```

## Gereksinimler

- Python 3.10+
- Ollama
- 4GB+ RAM (model için)

## Lisans

MIT
