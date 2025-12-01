# Proje Bağlamı - AI Asistanlar İçin

Bu dosyayı AI asistanına (ChatGPT, Claude, vb.) kopyala-yapıştır yaparak projeye devam edebilirsin.

---

## Proje Özeti

**Friendship AI Backend** - Kişilik analizi yapan arkadaşlık eşleştirme uygulaması.

### Temel Özellikler:
- **Ücretsiz AI**: Ollama (llama3.2:1b) ile yerel LLM - internet/ücret gerektirmez
- **Big Five (OCEAN) Kişilik Analizi**: Bilimsel kişilik modeli
- **Doğal Sohbet**: AI kullanıcıyla 30+ mesaj konuşarak kişilik tespit eder
- **Akıllı Eşleştirme**: Kişilik uyumluluğuna göre arkadaş önerisi

### Teknolojiler:
- Python 3.10+
- FastAPI (REST API)
- Ollama (Yerel LLM)
- Pydantic (Veri modelleri)
- SQLAlchemy (Veritabanı - opsiyonel)

---

## Dosya Yapısı

```
friendship-ai-backend/
├── main.py                          # FastAPI ana uygulama
├── chat.py                          # Terminal chat scripti
├── requirements.txt                 # Python bağımlılıkları
├── README.md                        # Kurulum ve kullanım
├── CONTEXT.md                       # Bu dosya (AI için bağlam)
│
└── src/
    ├── models/
    │   ├── personality.py           # Kişilik modelleri (Big Five)
    │   └── database.py              # SQLAlchemy veritabanı modelleri
    │
    ├── services/
    │   ├── conversation_ai.py       # Sohbet AI servisi
    │   ├── personality_analyzer.py  # Kişilik analizi (Ollama)
    │   └── matching_engine.py       # Eşleştirme algoritması
    │
    ├── api/
    │   └── routes.py                # API endpoint'leri
    │
    └── config/
        └── settings.py              # Uygulama ayarları
```

---

## Önemli Dosyalar ve İşlevleri

### 1. `src/services/conversation_ai.py`
- Kullanıcıyla sohbet yönetimi
- Oturum takibi
- Her mesajda kişilik analizi tetikleme

### 2. `src/services/personality_analyzer.py`
- Ollama API ile LLM çağrısı
- Anahtar kelime bazlı hızlı analiz
- Big Five skorları hesaplama
- İlgi alanı ve iletişim stili tespiti

### 3. `src/services/matching_engine.py`
- İki profil arası uyumluluk hesaplama
- Arkadaşlık türü tahmini (deep, casual, intellectual, activity_based)
- Eşleşme nedenleri ve potansiyel zorluklar

### 4. `src/models/personality.py`
- `PersonalityProfile`: Big Five skorları
- `ConversationMessage`: Mesaj modeli
- `ConversationSession`: Oturum modeli
- `MatchScore`: Eşleşme skoru

---

## Big Five (OCEAN) Kişilik Modeli

| Özellik | Değişken | Açıklama |
|---------|----------|----------|
| Openness | `openness` | Deneyime açıklık, yaratıcılık, merak |
| Conscientiousness | `conscientiousness` | Sorumluluk, düzen, disiplin |
| Extraversion | `extraversion` | Dışadönüklük, sosyallik, enerji |
| Agreeableness | `agreeableness` | Uyumluluk, empati, işbirliği |
| Neuroticism | `neuroticism` | Duygusal hassasiyet, kaygı |

Her özellik 0.0 - 1.0 arası skorlanır.

---

## API Endpoint'leri

| Method | Endpoint | Açıklama |
|--------|----------|----------|
| POST | `/api/v1/conversation/start` | Sohbet başlat |
| POST | `/api/v1/conversation/message` | Mesaj gönder, AI cevabı al |
| GET | `/api/v1/conversation/summary/{user_id}` | Oturum özeti |
| POST | `/api/v1/conversation/end/{user_id}` | Sohbeti bitir |
| GET | `/api/v1/profile/{user_id}` | Kişilik profili |
| GET | `/api/v1/matches/{user_id}` | Eşleşme önerileri |

---

## Çalıştırma

```bash
# 1. Ollama başlat (ayrı terminal)
ollama serve

# 2. Terminal chat
python3 chat.py

# 3. API sunucusu
python3 main.py
# Docs: http://localhost:8000/docs
```

---

## Yapılabilecek Geliştirmeler

- [ ] Gerçek veritabanı entegrasyonu (şu an memory'de)
- [ ] Kullanıcı authentication (JWT)
- [ ] WebSocket ile gerçek zamanlı chat
- [ ] Daha büyük model desteği (llama3.2:3b, mistral)
- [ ] Frontend (React/Flutter)
- [ ] Çoklu dil desteği

---

## Örnek İstek

Mesaj gönderme:
```bash
curl -X POST http://localhost:8000/api/v1/conversation/message \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user123", "message": "Merhaba, ben Eyüp!"}'
```

---

**GitHub:** https://github.com/eyupakky/friendship-ai-backend
